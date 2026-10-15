"""用户、鉴权、账号偏好相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phone: str
    nickname: str = ""
    avatar: str | None = None
    role: str = "user"
    balance: float = 0
    created_at: datetime


class SmsSendIn(BaseModel):
    phone: str = Field(min_length=11, max_length=11, pattern=r"^1[3-9]\d{9}$")
    scene: str = "login"


class LoginSmsIn(BaseModel):
    phone: str = Field(min_length=11, max_length=11, pattern=r"^1[3-9]\d{9}$")
    code: str = Field(min_length=4, max_length=10)


class ChangePhoneIn(BaseModel):
    phone: str = Field(min_length=11, max_length=11, pattern=r"^1[3-9]\d{9}$")
    code: str = Field(min_length=4, max_length=10)


class ChangePasswordIn(BaseModel):
    old_password: str = Field(min_length=6, max_length=64)
    new_password: str = Field(min_length=6, max_length=64)


class BindingsIn(BaseModel):
    provider: str  # wechat | apple
    bound: bool = True


class PreferencesOut(BaseModel):
    """账号偏好，默认值与前端 petwise_account_prefs 对齐。"""

    personalized: bool = True
    visibility: str = "public"  # public | followers | private
    binds: dict[str, bool] = Field(default_factory=lambda: {"wechat": True, "apple": False})


class PreferencesIn(BaseModel):
    personalized: bool | None = None
    visibility: str | None = None
    binds: dict[str, bool] | None = None


_DEFAULT_PREFS: dict[str, Any] = {
    "personalized": True,
    "visibility": "public",
    "binds": {"wechat": True, "apple": False},
}


def default_prefs() -> dict[str, Any]:
    return dict(_DEFAULT_PREFS)


def sms_debug_enabled() -> bool:
    return str(getattr(settings, "SMS_DEBUG", "")).lower() in ("1", "true", "yes")
