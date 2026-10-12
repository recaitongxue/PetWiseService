"""问诊智能体服务入口。

对外接口（全部需内部 Token，统一由 services/api 转发）：
- GET  /health                      健康检查
- POST /internal/v1/triage          一次性分诊
- POST /internal/v1/triage/stream   流式分诊（SSE）
- POST /internal/v1/report/stream   报告流式生成（SSE）
- /internal/v1/knowledge/*          知识库管理（见 knowledge/api.py）

设计要点：**本服务不持有任何业务数据**。
宠物档案由 api 服务显式传入，这里不连业务库（只连自己的知识库）。
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings
from app.graph.report import build_report
from app.graph.runner import engine_name, run_agent
from app.guard import InternalAuth
from app.knowledge.api import router as knowledge_router
from app.memory import get_memory
from app.schemas import TriageRequest

logging.basicConfig(level=settings.LOG_LEVEL, format="%(levelname)-7s %(name)s: %(message)s")
logger = logging.getLogger("agent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.memory = get_memory()
    logger.info(
        "agent 启动 env=%s engine=%s llm=%s embedding=%s mock=%s",
        settings.ENV,
        engine_name(),
        f"{settings.LLM_PROVIDER}:{settings.LLM_MODEL}",
        settings.EMBEDDING_PROVIDER,
        settings.mock_mode,
    )
    if settings.mock_mode:
        logger.warning("未检测到 LLM 密钥，处于 mock 模式：链路可跑通，结论来自规则基线")
    yield
    logger.info("agent 服务已停止")


app = FastAPI(
    title="Petwise Agent",
    description="问诊智能体：LangGraph 编排 + 知识库检索 + 合规护栏",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENV != "prod" else None,
)
app.include_router(knowledge_router)


@app.get("/health", summary="健康检查")
async def health() -> dict:
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "status": "ok",
            "service": settings.APP_NAME,
            "engine": engine_name(),
            "llm": f"{settings.LLM_PROVIDER}:{settings.LLM_MODEL}",
            "embedding": settings.EMBEDDING_PROVIDER,
            "mock": settings.mock_mode,
        },
    }


def _to_state(payload: TriageRequest, trace_id: str) -> dict:
    """把请求规整成图输入。"""
    return {
        "request": payload.model_dump(),
        "complaint": payload.complaint,
        "pet": payload.pet.model_dump() if payload.pet else {},
        "symptoms": payload.symptoms,
        "duration": payload.duration,
        "severity": payload.severity,
        "trace_id": trace_id,
    }


@app.post("/internal/v1/triage", dependencies=[InternalAuth], summary="一次性分诊")
async def triage(payload: TriageRequest) -> dict:
    trace_id = f"ag_{uuid.uuid4().hex[:12]}"
    started = time.perf_counter()

    state = await run_agent(_to_state(payload, trace_id))
    result = state.get("result") or {}
    result["traceId"] = trace_id

    logger.info(
        "分诊完成 level=%s used_llm=%s %.1fms",
        result.get("level"),
        state.get("used_llm", False),
        (time.perf_counter() - started) * 1000,
    )
    return {"code": 0, "message": "ok", "data": result}


def _sse(frame: dict) -> str:
    return f"data: {json.dumps(frame, ensure_ascii=False)}\n\n"


@app.post("/internal/v1/triage/stream", dependencies=[InternalAuth], summary="流式分诊")
async def triage_stream(payload: TriageRequest):
    """按阶段推送进度，最后推送完整结果。

    为什么需要阶段帧：LLM 首次返回可能要数秒，用户盯着空白屏会以为卡死。
    """
    trace_id = f"ag_{uuid.uuid4().hex[:12]}"
    memory = app.state.memory

    async def event_generator():
        stages = [
            ("precheck", "正在分析症状描述"),
            ("retrieve", "正在检索宠物知识库"),
            ("gather", "正在核对宠物档案"),
            ("reason", "正在生成健康建议"),
            ("critique", "正在进行安全审核"),
            ("finalize", "正在整理结论"),
        ]
        yield _sse({"stage": "start", "traceId": trace_id})

        # 逐帧发送阶段提示，真实链路是一次性跑完的：
        # 这样既能给出进度反馈，又不会因为节点粒度太细而拖慢整体响应
        state: dict = {}
        for stage, message in stages:
            yield _sse({"stage": stage, "message": message})
            if stage == "critique":
                # 到这里一次性执行完整链路（含自检），保证结果一致性
                state = await run_agent(_to_state(payload, trace_id))

        result = dict(state.get("result") or {})
        result["traceId"] = trace_id
        memory.append_turn(payload.userId or trace_id, {"role": "user", "content": payload.complaint})
        memory.append_turn(
            payload.userId or trace_id, {"role": "assistant", "content": result.get("short", "")}
        )

        yield _sse({"stage": "done", "data": result})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Trace-Id": trace_id},
    )


@app.post("/internal/v1/report/stream", dependencies=[InternalAuth], summary="研究报告流式生成")
async def report_stream(payload: dict):
    if not payload.get("transcript"):
        raise HTTPException(status_code=400, detail={"code": 10001, "message": "transcript 不能为空"})

    async def event_generator():
        yield _sse({"stage": "retrieve", "message": "正在检索相关知识"})
        report = await build_report(payload)
        yield _sse({"stage": "done", "data": report})

    return StreamingResponse(event_generator(), media_type="text/event-stream")
