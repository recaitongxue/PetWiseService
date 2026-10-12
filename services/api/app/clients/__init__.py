"""客户端依赖：从 app.state 取 lifespan 阶段创建的单例。

不要在路由里 new 客户端 —— httpx 连接池必须复用。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.clients.agent import AgentClient
from app.clients.vision import VisionClient


def get_vision_client(request: Request) -> VisionClient:
    return request.app.state.vision_client  # type: ignore[no-any-return]


def get_agent_client(request: Request) -> AgentClient:
    return request.app.state.agent_client  # type: ignore[no-any-return]


VisionClientDep = Annotated[VisionClient, Depends(get_vision_client)]
AgentClientDep = Annotated[AgentClient, Depends(get_agent_client)]
