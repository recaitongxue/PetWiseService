"""视觉推理服务入口。

对外只有两个端点：
- GET  /health                   健康检查（无需鉴权）
- POST /internal/v1/recognize    内部识别（需 X-Internal-Token）

任何 OpenAI 兼容字段都不要再往这里加 —— 它不知道用户、不知道订单，只做一件事：给图片打标签。
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status

from app.config import settings
from app.engine import InferenceEngine, ModelNotReadyError
from app.guard import InternalAuth
from app.registry import ModelRegistry
from app.schemas import HealthPayload

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(levelname)-7s %(name)s: %(message)s",
)
logger = logging.getLogger("vision")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.registry = ModelRegistry()
    app.state.engine = InferenceEngine(app.state.registry)

    error = app.state.registry.load_error
    if error:
        # 缺权重是可接受的启动状态：识别会返回 503，由 api 服务降级处理
        logger.warning("模型清单未就绪: %s", error)
    else:
        warmed = app.state.engine.warmup()
        logger.info(
            "推理引擎就绪 provider=%s models=%s warmup=%s",
            app.state.engine.provider,
            ",".join(app.state.registry.kinds) or "无",
            warmed,
        )

    yield
    logger.info("vision 服务已停止")


app = FastAPI(
    title="Petwise Vision",
    description="宠物视觉推理服务：无状态计算单元，仅对内提供接口",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENV != "prod" else None,
)


def get_engine() -> InferenceEngine:
    return app.state.engine  # type: ignore[no-any-return]


@app.get("/health", response_model=dict, summary="健康检查")
async def health() -> dict:
    registry: ModelRegistry = app.state.registry
    engine: InferenceEngine = app.state.engine
    degraded = registry.load_error is not None

    return {
        "code": 0,
        "message": registry.load_error or "ok",
        "data": HealthPayload(
            status="degraded" if degraded else "ok",
            models=registry.kinds,
            provider=engine.provider,
            env=settings.ENV,
        ).model_dump(),
    }


@app.post("/internal/v1/recognize", dependencies=[InternalAuth], summary="内部识别接口")
async def recognize(
    image: UploadFile = File(..., description="宠物图片，≤10MB"),
    kind: str = Form(default="auto", description="dog | cat | skin | auto"),
    topK: int = Form(default=settings.TOP_K, ge=1, le=10, description="返回候选数量"),
) -> dict:
    engine: InferenceEngine = app.state.engine
    started = time.perf_counter()

    content = await image.read()
    try:
        result = engine.predict(content, kind=kind, top_k=topK)
    except ModelNotReadyError as exc:
        raise HTTPException(status_code=503, detail={"code": 60001, "message": str(exc)}) from exc
    except KeyError as exc:
        raise HTTPException(status_code=400, detail={"code": 10001, "message": str(exc)}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": 10002, "message": str(exc)}) from exc

    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "识别 %s kind=%s conf=%.3f %.1fms",
        result.title,
        kind,
        result.confidence,
        elapsed_ms,
    )
    return {"code": 0, "message": "ok", "data": result.model_dump()}
