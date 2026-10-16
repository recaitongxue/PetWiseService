"""医生表：在线问诊可选的医生与科室；医生评价表。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, JSON, BigInteger, Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(50), default="主治医师")
    hospital: Mapped[str] = mapped_column(String(120))
    department: Mapped[str] = mapped_column(String(50), default="general")  # 科室 id（internal/surgery...）
    dept_label: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 科室中文名
    years: Mapped[int] = mapped_column(BigInteger, default=0)  # 从业年限
    specialties: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)  # 擅长标签
    good_at: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)  # 擅长病症
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rating: Mapped[Decimal | None] = mapped_column(DECIMAL(2, 1), nullable=True)
    consult_count: Mapped[int] = mapped_column(BigInteger, default=0)
    response_min: Mapped[int] = mapped_column(BigInteger, default=0)  # 平均响应分钟
    price: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 2), nullable=True)
    slot: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 排班展示
    intro: Mapped[str | None] = mapped_column(Text, nullable=True)
    certs: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    online: Mapped[bool] = mapped_column(Boolean, default=True)


class DoctorReview(Base):
    """问诊评价：用户在问诊单结束后提交，落库后展示在医生详情页。"""

    __tablename__ = "doctor_reviews"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    doctor_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    user_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    order_id: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True)
    score: Mapped[int] = mapped_column(BigInteger, default=5)  # 1-5 星
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
