"""服务间调用守卫（agent 侧）。

与 vision 服务保持一致的实现：compose 内部网络之外不应有人能调用推理接口，
否则绕过 api 服务的额度与鉴权，LLM 成本会失控。
"""

from __future__ import annotations

import hmac

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.config import settings

_INTERNAL_TOKEN_HEADER = "X-Internal-Token"

internal_key_scheme = APIKeyHeader(name=_INTERNAL_TOKEN_HEADER, auto_error=False)


def verify_internal_token(token: str | None = Depends(internal_key_scheme)) -> str:
    expected = settings.INTERNAL_TOKEN
    if not token or not hmac.compare_digest(token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 20003, "message": "无效的内部调用凭证"},
        )
    return token


InternalAuth = Depends(verify_internal_token)
