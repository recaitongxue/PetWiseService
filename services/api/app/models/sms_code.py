"""短信验证码表：发送即落库，校验时比对并置 consumed，过期由 expires_at 判断。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SmsCode(Base):
    __tablename__ = "sms_codes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), index=True)
    code: Mapped[str] = mapped_column(String(10))
    scene: Mapped[str] = mapped_column(String(20), default="login")  # login | change_phone
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
