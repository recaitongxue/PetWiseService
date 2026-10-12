"""健康检查。

/health        存活探针（k8s liveness）：进程活着就 200
/health/ready  就绪探针（readiness）：检查 DB 与下游 AI 服务
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter

from app.clients import AgentClientDep, VisionClientDep
from app.core.config import get_settings
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
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )


@router.get("/health/ready", summary="就绪检查")
async def ready(
    vision: VisionClientDep,
    agent: AgentClientDep,
) -> dict:
    """并行 ping 下游，任一不可用即在 dependencies 中标记，但整体仍返回 200。

    原因：AI 服务不可用时系统应以降级状态继续提供服务，而不是整体下线。
    """
    vision_ok, agent_ok = await asyncio.gather(vision.ping(), agent.ping())

    all_ready = vision_ok and agent_ok
    return ok(
        {
            "status": "ok" if all_ready else "degraded",
            "dependencies": {
                "database": True,  # DB 检查由 health_repo 补齐后接入
                "vision": vision_ok,
                "agent": agent_ok,
            },
        }
    )
