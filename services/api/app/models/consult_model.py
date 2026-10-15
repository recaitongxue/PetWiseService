"""问诊域模型：问诊单、问诊消息、问诊报告。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    JSON,
    String,
    Text,
    DECIMAL,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ConsultOrder(Base):
    __tablename__ = "consult_orders"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    doctor_id: Mapped[str] = mapped_column(String(32))
    pet_id: Mapped[int] = mapped_column(BigInteger)
    mode: Mapped[str] = mapped_column(String(16), default="text")  # text | voice | video
    price: Mapped[float] = mapped_column(DECIMAL(8, 2), default=0)
    state: Mapped[str] = mapped_column(String(16), default="pending")  # pending|replied|closed
    summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ConsultMessage(Base):
    __tablename__ = "consult_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(32), index=True)
    type: Mapped[str] = mapped_column(String(16), default="user")  # user|doctor|system|rx
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    images: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    drugs: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ConsultReport(Base):
    __tablename__ = "consult_reports"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    type: Mapped[str] = mapped_column(String(16), default="ai")  # ai | human
    pet_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    pet_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    order_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    preview: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chief: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    triage: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    doctor: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    doctor_advice: Mapped[str | None] = mapped_column(Text, nullable=True)
    rx: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    reminded: Mapped[bool] = mapped_column(Boolean, default=False)
    date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
