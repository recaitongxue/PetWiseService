"""服务间调用的守卫。

vision / agent 都不对外暴露端口，仅存在于 compose 内部网络；
再加一层内部 Token 校验，防止网络配置失误时被直接调用。
"""

from __future__ import annotations

import hmac

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.config import settings

_INTERNAL_TOKEN_HEADER = "X-Internal-Token"

internal_key_scheme = APIKeyHeader(name=_INTERNAL_TOKEN_HEADER, auto_error=False)


def verify_internal_token(
    token: str | None = Depends(internal_key_scheme),
) -> str:
    """常量时间比较，避免时序侧信道。"""
    expected = settings.INTERNAL_TOKEN
    if not token or not hmac.compare_digest(token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 20003, "message": "无效的内部调用凭证"},
        )
    return token


InternalAuth = Depends(verify_internal_token)
