"""Petwise 业务后端入口。

单一 FastAPI 服务：对外网关 + 全部业务数据持有者（MySQL）。
AI 分诊 / 品种识别当前为内置演示实现（规则引擎 + 品种库），
预留了替换为真实模型服务的位置（见 docs/ARCHITECTURE.md）。
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.exception_handlers import register_exception_handlers
from app.api.middleware.timing import SlowRequestMiddleware
from app.api.middleware.trace import TraceIdMiddleware
from app.api.routers import (
    admin,
    announcements,
    auth,
    breeds,
    community,
    consult,
    contacts,
    conversations,
    doctors,
    favorites,
    feedback,
    files,
    health,
    pets,
    recognitions,
    schedule,
    users,
    wallet,
)
from app.core.config import settings
from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL, json_format=settings.LOG_JSON)
    logger.info("%s 启动 env=%s", settings.APP_NAME, settings.ENV)
    yield
    logger.info("%s 已停止", settings.APP_NAME)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Petwise API",
        description="宠物智能服务平台 · 业务后端",
        version="1.0.0",
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
    for r in (
        auth, admin, users, pets, schedule, wallet, announcements, feedback,
        breeds, consult, doctors, community, contacts, conversations,
        favorites, files, recognitions,
    ):
        app.include_router(r.router, prefix=API_PREFIX)

    # 本地演示：上传文件静态服务（production 应替换为对象存储 + CDN）
    _upload_dir = os.path.normpath(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    )
    os.makedirs(_upload_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=_upload_dir), name="uploads")

    return app


app = create_app()
