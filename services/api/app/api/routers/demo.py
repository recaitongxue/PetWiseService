"""演示路由：少量可持续演进的样板。

这里示范三件事，是后续所有 router 的统一写法：
1. 成功出口只有 ok() / paged()
2. 鉴权依赖来自 core/deps，路由内不再解析 Header
3. 需要调用 AI 能力时，只依赖 clients 层
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import AdminUser, CurrentUser
from app.core.envelope import ok
from app.core.security import create_access_token, create_refresh_token

router = APIRouter()


@router.get("/me", summary="获取当前用户", tags=["auth"])
async def me(user: CurrentUser) -> dict:
    """示范鉴权依赖的用法：路由拿到的直接是已校验的 TokenPayload。"""
    return ok({"id": user.user_id, "role": user.role})


@router.get("/admin/ping", summary="管理端连通性", tags=["admin"])
async def admin_ping(_: AdminUser) -> dict:
    """示范 require_admin：非 admin 角色会被拦成 403/20004。"""
    return ok({"admin": True})


@router.post("/demo/token", summary="签发示例 Token", tags=["system"])
async def demo_token() -> dict:
    """本地联调用的临时凭证签发（生产环境必须关闭）。

    仅用于前端替换 mock 时快速验证 401/403 分支，上线前务必删除或加环境判断。
    """
    user_token, expires_in = create_access_token("demo-user", role="user")
    refresh, _ = create_refresh_token("demo-user")
    return ok(
        {
            "accessToken": user_token,
            "refreshToken": refresh,
            "expiresIn": expires_in,
        }
    )
