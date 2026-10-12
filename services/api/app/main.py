"""Petwise 业务后端入口。

职责边界（架构文档 4.2）：对外唯一网关 + 全部业务数据持有者。
vision / agent 不直接面对客户端，一律经由 app/clients/ 调用。
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exception_handlers import register_exception_handlers
from app.api.middleware.timing import SlowRequestMiddleware
from app.api.middleware.trace import TraceIdMiddleware
from app.api.routers import demo, health
from app.clients.agent import AgentClient
from app.clients.vision import VisionClient
from app.core.config import settings
from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """资源生命周期：下游客户端连接池在此创建与释放。"""
    setup_logging(settings.LOG_LEVEL, json_format=settings.LOG_JSON)

    app.state.vision_client = VisionClient()
    app.state.agent_client = AgentClient()
    logger.info(
        "%s 启动 env=%s vision=%s agent=%s",
        settings.APP_NAME,
        settings.ENV,
        settings.VISION_BASE_URL,
        settings.AGENT_BASE_URL,
    )

    yield

    await app.state.vision_client.aclose()
    await app.state.agent_client.aclose()
    logger.info("%s 已停止", settings.APP_NAME)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Petwise API",
        description="宠物智能服务平台 · 业务网关",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_prod else None,
        redoc_url=None,
        openapi_url="/openapi.json" if not settings.is_prod else None,
    )

    # 中间件顺序即执行顺序，trace 必须在最外层，否则后续拿不到 traceId
    app.add_middleware(SlowRequestMiddleware)
    app.add_middleware(TraceIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(demo.router, prefix=API_PREFIX)

    return app


app = create_app()
