"""JWT 签发与校验。

Token 载荷与契约《2. 鉴权方案》一致；用户类型用 role 区分普通用户与管理员，
管理端接口通过 require_admin 依赖强制隔离。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings
from app.core.errors import AppError, ErrorCode


class TokenPayload(dict[str, Any]):
    """承载 sub / role / exp / jti 的轻量字典包装，便于取值带默认值。"""

    @property
    def user_id(self) -> str:
        return str(self.get("sub", ""))

    @property
    def role(self) -> str:
        return str(self.get("role", "user"))


def create_access_token(user_id: str, role: str = "user") -> tuple[str, int]:
    """签发 access token，返回 (token, expires_in)。"""
    expires_in = settings.ACCESS_TOKEN_TTL
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "exp": datetime.now(UTC) + timedelta(seconds=expires_in),
        "iat": datetime.now(UTC),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expires_in


def create_refresh_token(user_id: str) -> tuple[str, int]:
    """签发 refresh token，TTL 远长于 access。"""
    expires_in = settings.REFRESH_TOKEN_TTL
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.now(UTC) + timedelta(seconds=expires_in),
        "iat": datetime.now(UTC),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expires_in


def decode_token(token: str, *, expected_type: str | None = None) -> TokenPayload:
    """解析 Token。

    区分「过期」与「无效」两个错误码，前端才能正确触发静默刷新（契约 20002 / 20003）。
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        message = str(exc).lower()
        if "expired" in message or "exp " in message:
            raise AppError(ErrorCode.TOKEN_EXPIRED, "登录已过期") from exc
        raise AppError(ErrorCode.TOKEN_INVALID, "凭证无效") from exc

    if expected_type and payload.get("type") != expected_type:
        raise AppError(ErrorCode.TOKEN_INVALID, "凭证类型不匹配")

    return TokenPayload(payload)
