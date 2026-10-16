"""健康检查。

/health        存活探针（k8s liveness）：进程活着就 200
/health/ready  就绪探针（readiness）：检查数据库连通性
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import get_settings
from app.core.deps import DbSession
from app.core.envelope import ok

router = APIRouter(tags=["system"])


@router.get("/health", summary="存活检查")
async def health() -> dict:
    """不做任何 IO，仅供容器编排判断进程是否存活。"""
    return ok(
        {
            "status": "ok",
            "service": get_settings().APP_NAME,
            "env": get_settings().ENV,
            "time": datetime.now(UTC).isoformat(timespec="seconds"),
        }
    )


@router.get("/health/ready", summary="就绪检查（数据库）")
async def ready(db: DbSession):
    """数据库不可用时返回 503，让编排层把流量切走。"""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content=ok({"status": "unavailable", "dependencies": {"database": False}}),
        )
    return ok({"status": "ok", "dependencies": {"database": True}})
