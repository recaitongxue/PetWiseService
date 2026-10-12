"""FastAPI 依赖注入集合。

提供的三类依赖：
- 鉴权：current_user / require_admin
- 数据：Session（后续由 repos 层消费）
- 对内：internal_call（服务间调用校验，见 clients/base.py）

业务层不要自己解析 Header，一律从这里取，保证鉴权口径唯一。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.errors import AppError, ErrorCode
from app.core.security import TokenPayload, decode_token

# auto_error=False：由我们自己抛契约错误码，而不是 FastAPI 默认的 403
bearer_scheme = HTTPBearer(auto_error=False)


def get_trace_id(request: Request) -> str:
    """从请求状态读取 traceId（由 TraceIdMiddleware 注入）。"""
    return str(getattr(request.state, "trace_id", "-"))


def _extract_credentials(
    credential: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    if credential is None or not credential.credentials:
        raise AppError(ErrorCode.UNAUTHORIZED, "缺少登录凭证")
    return credential.credentials


def get_current_payload(token: Annotated[str, Depends(_extract_credentials)]) -> TokenPayload:
    """解析并校验 access token，路由层不要直接使用。"""
    payload = decode_token(token, expected_type="access")
    if not payload.user_id:
        raise AppError(ErrorCode.UNAUTHORIZED, "凭证不完整")
    return payload


CurrentUser = Annotated[TokenPayload, Depends(get_current_payload)]


def require_admin(payload: CurrentUser) -> TokenPayload:
    """管理端接口专用：role 必须是 admin。"""
    if payload.role != "admin":
        raise AppError(ErrorCode.FORBIDDEN, "无管理端权限")
    return payload


AdminUser = Annotated[TokenPayload, Depends(require_admin)]


def get_settings_dep():
    """把配置作为依赖暴露，便于测试覆盖。"""
    return settings


SettingsDep = Annotated[object, Depends(get_settings_dep)]
