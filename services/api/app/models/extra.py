"""杂项模型：识别记录、备忘录、公告关闭、AI 额度。"""

from __future__ import annotations

import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    JSON,
    String,
    Text,
    Date,
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
