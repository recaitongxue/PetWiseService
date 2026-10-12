"""智能体状态定义。

用 dict 而不是自定义类：LangGraph 的 state 本质是 dict-like，
而我们的降级编排（SequentialRunner）也按 dict 传递，两者天然兼容。
"""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """一次问诊在图里流动的全部数据。

    约定：**每个节点只读自己需要的键、只写自己负责的键**，
    这样将来把某个节点换成 LLM 或换��本地规则，都不影响其它节点。
    """

    # ── 输入 ──────────────────────────────────────────────
    request: dict[str, Any]        # TriageRequest 的字典形态
    complaint: str
    pet: dict[str, Any]
    symptoms: list[str]
    duration: str
    severity: str

    # ── 中间产物 ──────────────────────────────────────────
    red_flags: list[str]           # 命中的危险信号
    rule_score: int                # 规则初筛得分
    factors: list[dict[str, Any]]  # 可解释评分依据
    knowledge: list[dict[str, Any]]  # 检索到的知识片段
    knowledge_context: str         # 拼好的上下文
    tool_result: dict[str, Any]    # 工具返回的确定性数据
    draft: dict[str, Any]          # LLM 原始输出
    critique: dict[str, Any]       # 自检结果

    # ── 输出 ──────────────────────────────────────────────
    result: dict[str, Any]         # 最终 TriageResult

    # ── 元信息 ────────────────────────────────────────────
    trace_id: str
    errors: list[str]
    used_llm: bool
