"""编排执行器。

优先使用 LangGraph 构建状态机；未安装依赖时退化为按序执行的线性编排，
**节点顺序与语义完全一致**，因此两种模式产出可比对。

这样做的好处：答辩环境/离线环境缺少 langgraph 时，
链路依然能完整跑通，而不是"装了依赖才能演示"。
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.graph.state import AgentState

logger = logging.getLogger("agent.graph")

try:  # pragma: no cover - 依赖存在与否由环境决定
    from langgraph.graph import END, StateGraph
except ImportError:  # pragma: no cover
    StateGraph = None  # type: ignore[assignment]
    END = "__end__"  # type: ignore[assignment]

NodeFn = Callable[[AgentState], Any]

# 执行顺序即数据依赖顺序：先有迹线规则基线，再检索，再工具，最后模型推理与自检
NODE_SEQUENCE: list[tuple[str, NodeFn]] = []


def _register_sequence() -> None:
    from app.graph import nodes

    NODE_SEQUENCE.clear()
    NODE_SEQUENCE.extend(
        [
            ("precheck", nodes.precheck),
            ("retrieve", nodes.retrieve),
            ("gather", nodes.gather),
            ("reason", nodes.reason),
            ("critique", nodes.critique),
            ("finalize", nodes.finalize),
        ]
    )


_register_sequence()


async def _apply(node: NodeFn, state: AgentState) -> dict[str, Any]:
    """统一处理同步/异步节点：异步协程才 await。"""
    result = node(state)
    if inspect.isawaitable(result):
        result = await result
    return dict(result or {})


async def run_agent(initial: AgentState) -> AgentState:
    """执行完整链路，返回终态。"""
    state: AgentState = dict(initial)
    state.setdefault("errors", [])

    for name, node in NODE_SEQUENCE:
        try:
            patch = await _apply(node, state)
        except Exception as exc:  # noqa: BLE001 - 单节点失败记录后继续
            logger.exception("节点 %s 执行失败", name)
            state["errors"] = list(state.get("errors") or []) + [f"{name}: {exc}"]
            continue
        state.update(patch)  # type: ignore[arg-type]

    return state


def build_graph():
    """构建 LangGraph 状态机（仅当依赖可用）。

    保留这个入口是为了后续接入条件边（如"命中 red flag 直接 finalize"）。
    """
    if StateGraph is None:
        return None

    graph = StateGraph(AgentState)
    for name, node in NODE_SEQUENCE:
        graph.add_node(name, node)

    graph.set_entry_point(NODE_SEQUENCE[0][0])
    for (current, _), (nxt, _) in zip(NODE_SEQUENCE, NODE_SEQUENCE[1:], strict=False):
        graph.add_edge(current, nxt)
    graph.add_edge(NODE_SEQUENCE[-1][0], END)
    return graph.compile()


def engine_name() -> str:
    return "langgraph" if StateGraph is not None else "sequential"
