"""用户表：手机号即登录账号，演示环境无密码，靠短信验证码鉴权。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, DECIMAL, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(50), default="")
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)  # 演示用 sha256
    role: Mapped[str] = mapped_column(String(20), default="user")  # user | admin
    handle: Mapped[str | None] = mapped_column(String(32), nullable=True)  # 个性标识，如 @manman
    bio: Mapped[str | None] = mapped_column(String(200), nullable=True)
    followers: Mapped[int] = mapped_column(BigInteger, default=0)
    following: Mapped[int] = mapped_column(BigInteger, default=0)
    # 钱包余额（注销前需清零，对应前端注销四步校验）
    balance: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0)
    # 账号偏好：{personalized, visibility, binds:{wechat,apple}}
    prefs: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    # 黑名单：[{id, name}] 联系人拉黑
    blocked: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
