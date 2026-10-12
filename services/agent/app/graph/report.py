"""问诊报告生成（区别于分诊的一次性链路）。

报告的输入是完整对话，而不是单条主诉，因此不复用分诊图：
它需要一次独立的知识检索 + 一次 LLM 生成。
"""

from __future__ import annotations

import logging
from typing import Any

from app.config import settings
from app.guardrails import compliance_check, with_disclaimer
from app.knowledge import db as db_utils
from app.knowledge.retriever import KnowledgeRetriever, build_context
from app.llm.client import LLMClient, LLMError
from app.prompts import loader as prompt_loader

logger = logging.getLogger("agent.report")

_DEFAULT_REPORT = {
    "summary": "本次问诊记录已归档，建议按医嘱执行后续照护。",
    "chiefComplaint": "详见问诊对话记录",
    "measuresTaken": [],
    "impression": "待线下面诊确认",
    "recommendations": ["按医嘱完成后续观察", "症状加重及时复诊"],
    "followUpDate": "",
    "sources": [],
}


def _format_transcript(transcript: list[dict[str, str]]) -> str:
    lines = []
    for turn in transcript[-20:]:
        role = "医生" if turn.get("role") in {"doctor", "assistant"} else "主人"
        lines.append(f"{role}：{turn.get('content', '')}")
    return "\n".join(lines) or "（无对话记录）"


async def build_report(payload: dict[str, Any]) -> dict[str, Any]:
    """生成结构化问诊报告。"""
    pet = payload.get("pet") or {}
    transcript = payload.get("transcript") or []
    conclusion = str(payload.get("conclusion") or "")
    consult_id = str(payload.get("consultId") or "")

    # 1. 知识检索：报告要给出可核查的建议，同样依赖知识库
    query = " ".join(
        filter(None, [conclusion, str(pet.get("breed") or ""), _format_transcript(transcript)[:120]])
    )
    knowledge_context = "（无相关条目）"
    try:
        with db_utils.session_scope() as session:
            items = KnowledgeRetriever().retrieve(session, query, top_k=4)
            knowledge_context = build_context(items)
    except Exception as exc:  # noqa: BLE001
        logger.warning("报告检索知识失败: %s", exc)

    variables = {
        "consult_id": consult_id,
        "pet_summary": _pet_summary(pet),
        "dept": payload.get("dept") or "internal",
        "transcript": _format_transcript(transcript),
        "conclusion": conclusion or "（无）",
        "knowledge_context": knowledge_context,
    }

    client = LLMClient()
    if client.mock_mode:
        report = dict(_DEFAULT_REPORT)
        report["summary"] = f"{pet.get('name') or '该宠物'}的问诊记录已归档。"
    else:
        try:
            report = await client.chat_json(
                "你是 Petwise 的报告撰写助手，只输出 JSON 对象。",
                prompt_loader.render("report", variables),
            )
        except LLMError as exc:
            logger.warning("报告生成降级: %s", exc)
            report = dict(_DEFAULT_REPORT)

    # 2. 合规：报告同样不允许出现处方级内容
    report.setdefault("recommendations", [])
    joined = " ".join(str(x) for x in report.get("recommendations", []))
    check = compliance_check(joined + str(report.get("summary", "")))
    if not check["pass"]:
        report["recommendations"] = [
            "具体方案由执业兽医面诊后给出" if check.get("needHuman") else str(x)
            for x in report["recommendations"]
        ]

    if report.get("summary"):
        report["summary"] = with_disclaimer(str(report["summary"]))
    report["disclaimer"] = settings.DISCLAIMER
    return report


def _pet_summary(pet: dict[str, Any]) -> str:
    if not pet:
        return "未提供宠物档案"
    parts = [str(pet.get("name") or "未命名")]
    if pet.get("breed"):
        parts.append(str(pet["breed"]))
    if pet.get("ageMonths") is not None:
        parts.append(f"{pet['ageMonths']} 月龄")
    if pet.get("weightKg"):
        parts.append(f"{pet['weightKg']}kg")
    return "，".join(parts)
