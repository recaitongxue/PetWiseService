"""健康记录表：体重趋势与每日状态评分（metrics 存 JSON）。"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Date, DECIMAL, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class HealthRecord(Base):
    __tablename__ = "health_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, index=True)
    pet_id: Mapped[int] = mapped_column(BigInteger, index=True)
    record_date: Mapped[date] = mapped_column(Date, index=True)
    kind: Mapped[str] = mapped_column(String(16), default="weight")  # weight|diet|symptom|care
    weight: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    # metrics 形如 {"appetite": 4, "mood": 5, "stool": 3, "activity": 4}
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
