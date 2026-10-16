"""杂项模型：识别记录、备忘录、公告关闭、AI 额度。"""

from __future__ import annotations

import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Recognition(Base):
    __tablename__ = "recognitions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    pet_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    species: Mapped[str | None] = mapped_column(String(16), nullable=True)
    predicted: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sci: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    breed_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    alternatives: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    corrected: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="done")  # done|review|approved|rejected
    image_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Memo(Base):
    __tablename__ = "memos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    pet_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    text: Mapped[str] = mapped_column(String(200))
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AnnouncementDismiss(Base):
    __tablename__ = "announcement_dismiss"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    announcement_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)


class AiUsage(Base):
    __tablename__ = "ai_usage_daily"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    stat_date: Mapped[Date] = mapped_column(Date, primary_key=True)
    used: Mapped[int] = mapped_column(BigInteger, default=0)


class Setting(Base):
    """平台级配置（管理端「设置」页）：key-value，value 存 JSON。"""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class WalletTx(Base):
    """钱包流水：充值 / 提现 / 问诊消费，余额 = 各笔代数（以 User.balance 为权威值）。"""

    __tablename__ = "wallet_txs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    type: Mapped[str] = mapped_column(String(16), default="topup")  # topup | withdraw | consult
    amount: Mapped[float] = mapped_column(Float, default=0)  # 正数；withdraw/consult 为支出
    note: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
