"""图节点实现。

每个节点一个文件、一个职责，签名统一为 ``(state) -> dict``：
返回值是**增量 patch**，不是完整 state —— 这是为了兼容 LangGraph，
也让每个节点可以被单独测试。

节点清单：
    precheck     输入清洗与危险信号初筛（规则，必执行）
    retrieve     知识库检索（本服务的核心能力）
    gather       工具调用（确定性数据）
    reason       LLM 推理（唯一用到模型的地方）
    critique     合规自检 + 必要时改写
    finalize     组装契约结构 TriageResult
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from app.config import settings
from app.graph.state import AgentState
from app.guardrails import (
    compliance_check,
    detect_red_flags,
    level_of,
    score_duration,
    score_severity,
    score_symptoms,
    with_disclaimer,
)
from app.knowledge import db as db_utils
from app.knowledge.retriever import KnowledgeRetriever, build_context
from app.llm.client import LLMClient, LLMError
from app.prompts import loader as prompt_loader
from app.tools.base import run_tools

logger = logging.getLogger("agent.graph")

_DEPT_OPTIONS = "internal | surgery | dermatology | dentistry | ophthalmology | emergency"

# 作为 system 消息固定下发：输出纪律必须每次强调，否则偶发的寒暄会打断 JSON 解析
_SYSTEM_DISCUSSION = (
    "你是 Petwise 的宠物健康助手，只输出用户要求的 JSON 对象。"
    "不要输出代码块标记、不要输出解释性文字。"
)


# ── 1. 预处理与危险信号初筛 ──────────────────────────────────
def precheck(state: AgentState) -> dict[str, Any]:
    """规则初筛：先算出一个不依赖 LLM 的基线结论。

    这个基线有两个用途：
    1. LLM 不可用时兜底；
    2. 作为 critique 的参照，防止模型把急诊判成居家观察。
    """
    complaint = str(state.get("complaint") or "")
    symptoms = state.get("symptoms") or []
    text = complaint + " " + " ".join(symptoms)

    factors: list[dict[str, Any]] = detect_red_flags(text)
    factors += score_symptoms(text)

    duration_factor = score_duration(text, state.get("duration", ""))
    if duration_factor:
        factors.append(duration_factor)
    severity_factor = score_severity(text, state.get("severity", ""))
    if severity_factor:
        factors.append(severity_factor)

    score = sum(int(f.get("w") or 0) for f in factors)
    has_danger = any(bool(f.get("danger")) for f in factors)

    return {
        "rule_score": score,
        "red_flags": [str(f["text"]) for f in factors if f.get("danger")],
        "factors": factors,
        "baseline_level": level_of(score, has_danger),
    }


# ── 2. 知识检索 ──────────────────────────────────────────────
def retrieve(state: AgentState) -> dict[str, Any]:
    """从知识库取最相关的若干片段。

    检索失败的语义是"没有额外知识"，而不是"整个链路失败"——
    后面的 reason 节点会退化为仅依据档案与规则作答。
    """
    retriever = KnowledgeRetriever()
    pet = state.get("pet") or {}
    query_parts = [str(state.get("complaint") or "")]
    query_parts += list(state.get("symptoms") or [])
    if pet.get("breed"):
        query_parts.append(str(pet["breed"]))
    query = " ".join(p for p in query_parts if p).strip()

    if not query:
        return {"knowledge": [], "knowledge_context": build_context([])}

    try:
        with db_utils.session_scope() as session:
            items = retriever.retrieve(
                session,
                query,
                top_k=settings.RETRIEVAL_TOP_K,
                species=pet.get("species") or None,
            )
    except Exception as exc:  # noqa: BLE001 - 知识库不可用必须降级而非中断
        logger.warning("知识检索失败，降级继续: %s", exc)
        return {"knowledge": [], "knowledge_context": build_context([])}

    knowledge = [
        {
            "chunkId": item.chunk_id,
            "title": item.title,
            "heading": item.heading,
            "content": item.content,
            "score": item.score,
            "sourceType": item.source_type,
            "citation": item.citation,
        }
        for item in items
    ]
    return {
        "knowledge": knowledge,
        "knowledge_context": build_context(items),
    }


# ── 3. 工具调用 ──────────────────────────────────────────────
def gather(state: AgentState) -> dict[str, Any]:
    """确定性数据的唯一入口。"""
    return {"tool_result": run_tools(state)}


# ── 4. LLM 推理 ──────────────────────────────────────────────
async def reason(state: AgentState) -> dict[str, Any]:
    """调用 LLM 生成结构化结论；不可用时回退到规则基线。"""
    client = LLMClient()
    pet = state.get("pet") or {}
    baseline = str(state.get("baseline_level") or "home")

    variables = {
        "pet": pet or None,
        "complaint": state.get("complaint", ""),
        "duration": state.get("duration", ""),
        "severity": state.get("severity", ""),
        "symptoms": state.get("symptoms") or [],
        "knowledge_context": state.get("knowledge_context") or "（无相关条目）",
        "dept_options": _DEPT_OPTIONS,
    }

    try:
        # 模板里已含角色设定与输入，这里只补一条输出纪律作为 system
        draft = await client.chat_json(
            _SYSTEM_DISCUSSION,
            prompt_loader.render("triage", variables),
        )
    except LLMError as exc:
        logger.warning("LLM 不可用，回退规则基线: %s", exc)
        return {"draft": _rule_based_draft(state), "used_llm": False}

    draft.setdefault("level", baseline)
    if not draft.get("sources"):
        draft["sources"] = sorted({str(k["title"]) for k in state.get("knowledge") or []})

    # 规则认为更严重时，以规则为准（安全方向偏斜）
    if baseline == "emergency" and draft.get("level") != "emergency":
        logger.warning("模型判断低于规则基线，已按规则修正")
        draft["level"] = "emergency"

    draft["modelVersion"] = f"{client.provider}:{client.model}"
    return {"draft": draft, "used_llm": True}


# ── 5. 合规自检 ──────────────────────────────────────────────
async def critique(state: AgentState) -> dict[str, Any]:
    """检查越界 / 幻觉 / 过度承诺，必要时改写。

    即使 LLM 不可用，规则检查仍然执行 —— 这一步不能省。
    """
    draft = dict(state.get("draft") or {})
    advice = str(draft.get("advice", ""))
    local = compliance_check(advice)

    if local["pass"]:
        return {"critique": {"pass": True, "issues": [], "needHuman": False}, "draft": draft}

    issues = list(local["issues"])  # type: ignore[arg-type]
    patched = _strip_prescription(advice)

    # 若本地无法改写干净且模型可用，让模型重写一次
    if local.get("needHuman") and not settings.mock_mode:
        try:
            client = LLMClient()
            result = await client.chat_json(
                _SYSTEM_DISCUSSION,
                prompt_loader.render(
                    "critique",
                    {
                        "complaint": state.get("complaint", ""),
                        "candidate": str(draft),
                        "knowledge_context": state.get("knowledge_context", ""),
                    },
                ),
            )
            patched = result.get("patched") or patched
            issues += [str(i) for i in result.get("issues", [])]
        except LLMError:
            pass

    draft["advice"] = patched
    return {
        "critique": {"pass": False, "issues": issues, "needHuman": bool(local.get("needHuman"))},
        "draft": draft,
    }


def _strip_prescription(text: str) -> str:
    """本地兜底改写：抹掉具体用药表述并补一句就医提示。"""
    from app.guardrails import PRESCRIPTION_PATTERN

    cleaned = PRESCRIPTION_PATTERN.sub("【请遵医嘱】", text or "")
    suffix = " 具体用药需要由执业兽医面诊后开具。"
    if suffix not in cleaned:
        cleaned += suffix
    return cleaned


# ── 6. 组装输出 ──────────────────────────────────────────────
def finalize(state: AgentState) -> dict[str, Any]:
    """把 draft 收敛成契约结构，补齐缺失字段。"""
    draft = dict(state.get("draft") or {})
    factors = [
        {
            "text": str(f.get("text", "")),
            "w": f.get("w"),
            "danger": bool(f.get("danger", False)),
        }
        for f in (draft.get("factors") or state.get("factors") or [])
    ]
    if not factors:
        factors = [{"text": "主诉信息有限", "w": None, "danger": False}]

    tool_result = state.get("tool_result") or {}
    suggestions = (tool_result.get("schedule_suggestion") or {}).get("items", [])

    level = str(draft.get("level") or state.get("baseline_level") or "home")
    if state.get("red_flags"):
        level = "emergency"

    result = {
        "level": level,
        "score": int(draft.get("score") or state.get("rule_score") or 0),
        "label": str(draft.get("label") or _DEFAULT_LABEL[level]),
        "short": str(draft.get("short") or _DEFAULT_SHORT[level]),
        "advice": with_disclaimer(str(draft.get("advice") or _DEFAULT_ADVICE[level])),
        "causes": [str(c) for c in (draft.get("causes") or [])][:4],
        "actions": [str(a) for a in (draft.get("actions") or [])][:4],
        "followUp": str(draft.get("followUp") or _DEFAULT_FOLLOWUP[level]),
        "dept": str(draft.get("dept") or ("emergency" if level == "emergency" else "internal")),
        "factors": factors[:8],
        "sources": [str(s) for s in (draft.get("sources") or [])][:5],
        "modelVersion": str(draft.get("modelVersion") or "rules-baseline"),
        "disclaimer": settings.DISCLAIMER,
        "reminders": suggestions,
        "traceId": state.get("trace_id") or f"ag_{uuid.uuid4().hex[:10]}",
    }
    return {"result": result}


_DEFAULT_LABEL = {
    "emergency": "建议立即就医",
    "urgent": "建议尽快就诊",
    "home": "可先居家观察",
}
_DEFAULT_SHORT = {
    "emergency": "请立即联系最近的动物医院",
    "urgent": "24 小时内预约医生",
    "home": "居家观察并保持记录",
}
_DEFAULT_ADVICE = {
    "emergency": "当前描述的症状存在快速恶化的可能，请立即前往动物医院急诊。"
    "途中注意保持宠物呼吸道通畅、减少搬动，若有呕吐物或排泄物可拍照记录供医生参考。",
    "urgent": "建议尽快预约线下面诊。请提前记录症状出现时间、频次与进食情况，"
    "就诊时一并提供给医生，有助于提高诊断效率。",
    "home": "可先在家观察。保持饮食与作息稳定，避免自行用药；"
    "如出现症状加重、拒食或精神变差，请及时就诊。",
}
_DEFAULT_FOLLOWUP = {
    "emergency": "立即前往急诊，途中保持安静与保暖",
    "urgent": "48 小时内若未见好转请线下就诊",
    "home": "连续观察 48 小时，出现新症状及时反馈",
}


def _rule_based_draft(state: AgentState) -> dict[str, Any]:
    """LLM 不可用时的兜底草稿：完全由规则生成。"""
    level = str(state.get("baseline_level") or "home")
    return {
        "level": level,
        "score": int(state.get("rule_score") or 0),
        "label": _DEFAULT_LABEL[level],
        "short": _DEFAULT_SHORT[level],
        "advice": _DEFAULT_ADVICE[level],
        "causes": [],
        "actions": ["记录症状出现时间与频次", "保证饮水供应", "避免剧烈运动", "不要自行给药"],
        "followUp": _DEFAULT_FOLLOWUP[level],
        "dept": "emergency" if level == "emergency" else "internal",
        "factors": list(state.get("factors") or []),
        "sources": [],
        "modelVersion": "rules-baseline",
    }
