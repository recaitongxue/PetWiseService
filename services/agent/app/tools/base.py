"""工具层：给智能体提供的**确定性**能力。

与 LLM 的区别：工具永远返回可复现的结果，不会因为模型状态不同而漂移。
因此凡是能从确定性数据推出的结论，都应该由工具给出。
"""

from __future__ import annotations

import re
from typing import Any, Callable, Protocol

from app.config import settings


class ToolResult(dict[str, Any]):
    """工具返回值：约定必须带 summary，便于 tracing 与降级展示。"""

    @property
    def ok(self) -> bool:
        return bool(self.get("ok", True))


class Tool(Protocol):
    name: str
    description: str

    def __call__(self, state: dict[str, Any]) -> ToolResult: ...


def tool(name: str, description: str) -> Callable[[Callable[..., ToolResult]], Callable[..., ToolResult]]:
    """轻量装饰器，给函数挂上元数据，便于自动拼系统提示。"""

    def decorator(func: Callable[..., ToolResult]) -> Callable[..., ToolResult]:
        func.name = name  # type: ignore[attr-defined]
        func.description = description  # type: ignore[attr-defined]
        return func

    return decorator


# ── 宠物档案工具 ─────────────────────────────────────────────
@tool("pet_profile", "读取宠物档案中的确定性信息：年龄、体重、免疫史、既往病史")
def pet_profile_tool(state: dict[str, Any]) -> ToolResult:
    """从 api 服务传来的上下文里取结构化字段。

    注意：这里**不查询数据库**。agent 服务不持有业务数据，
    跨服务数据获取必须走 services/api 显式传递或未来的只读接口。
    """
    pet = state.get("pet") or {}
    if not pet:
        return ToolResult(ok=False, summary="无宠物档案")

    age_months = pet.get("ageMonths")
    stage = "未知"
    if isinstance(age_months, int):
        if age_months < 12:
            stage = "幼年期"
        elif age_months < 96:
            stage = "成年期"
        else:
            stage = "老年期"

    summary_parts = [f"{pet.get('name') or '该宠物'}({stage})"]
    if pet.get("breed"):
        summary_parts.append(f"品种 {pet['breed']}")
    if pet.get("weightKg"):
        summary_parts.append(f"体重 {pet['weightKg']}kg")
    if pet.get("vaccinated") is False:
        summary_parts.append("未完成免疫")
    if pet.get("chronic"):
        summary_parts.append("既往：" + "、".join(pet["chronic"]))

    return ToolResult(
        ok=True,
        summary="，".join(summary_parts),
        stage=stage,
        pets=pet,
    )


# ── 日程建议工具 ─────────────────────────────────────────────
_REMINDER_RULES: list[tuple[str, str, str]] = [
    ("疫苗", "疫苗补打提醒", "联系医院确认免疫程序是否到期"),
    ("驱虫", "体内驱虫提醒", "按体重选择驱虫药，间隔 3 个月一次"),
    ("呕吐", "饮食观察提醒", "记录呕吐次数与进食量，24 小时内反馈变化"),
    ("腹泻", "补液观察提醒", "注意是否出现脱水（皮肤回弹变慢、精神沉郁）"),
    ("咳嗽", "环境调整提醒", "避免烟尘与冷空气刺激，观察夜间咳嗽频率"),
    ("皮肤", "驱虫与环境清洁", "检查是否有跳蚤，清洗寝具并保持干燥"),
]


@tool("schedule_suggestion", "根据主诉生成可加入日程的照护提醒")
def schedule_tool(state: dict[str, Any]) -> ToolResult:
    complaint = str(state.get("complaint", ""))
    level = str((state.get("draft") or {}).get("level", "home"))

    items: list[dict[str, str]] = []
    for keyword, title, note in _REMINDER_RULES:
        if keyword in complaint:
            items.append({"title": title, "note": note})

    if not items:
        return ToolResult(ok=True, summary="无需额外日程", items=[])

    if level == "emergency":
        # 急诊时不要给用户"记账"类提醒，徒增干扰
        return ToolResult(ok=True, summary="急诊场景跳过日程建议", items=[])

    return ToolResult(ok=True, summary=f"生成 {len(items)} 条提醒", items=items)


# ── 剂量/处方安全闸门 ────────────────────────────────────────
_PRESCRIPTION_PATTERN = re.compile(
    r"(?:[每]?[日天]\s*\d+\s*(?:次|粒|片|毫升|ml))|(?:\d+\s*mg)|(?:阿莫西林|头孢|多西环素|驱虫药|伊维菌素|泼尼松|地塞米松)",
    re.IGNORECASE,
)


@tool("prescription_guard", "检测并剔除回答中的处方级内容")
def prescription_guard_tool(state: dict[str, Any]) -> ToolResult:
    """默认关闭处方能力：命中的片段会被标记，交给 critique 节点改写。"""
    if settings.PRESCRIPTION_ENABLED:
        return ToolResult(ok=True, summary="处方能力已开启", hits=[])

    target = str((state.get("draft") or {}).get("advice", ""))
    hits = [m.group(0) for m in _PRESCRIPTION_PATTERN.finditer(target)]
    return ToolResult(
        ok=not hits,
        summary=f"检测到 {len(hits)} 处处方级表述" if hits else "无用药建议",
        hits=hits,
    )


ALL_TOOLS: list[Callable[[dict[str, Any]], ToolResult]] = [
    pet_profile_tool,
    schedule_tool,
    prescription_guard_tool,
]


def run_tools(state: dict[str, Any]) -> dict[str, Any]:
    """顺序执行全部工具，结果汇总到 state['tool_result']。"""
    collected: dict[str, Any] = {}
    for func in ALL_TOOLS:
        try:
            collected[getattr(func, "name")] = func(state)
        except Exception as exc:  # noqa: BLE001 - 单个工具失败不应中断链路
            collected[getattr(func, "name")] = ToolResult(ok=False, summary=f"工具异常: {exc}")
    return collected


def tool_descriptions() -> str:
    """生成给 LLM 看的工具清单（供后续扩展 function calling 使用）。"""
    return "\n".join(f"- {f.name}: {f.description}" for f in ALL_TOOLS)
