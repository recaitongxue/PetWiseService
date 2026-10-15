"""宠物表：一个用户可拥有多只宠物，软删除用 deleted_at。"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, DECIMAL, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(String(50))
    species: Mapped[str] = mapped_column(String(10), default="dog")  # dog | cat
    breed: Mapped[str | None] = mapped_column(String(50), nullable=True)
    breed_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    gender: Mapped[str] = mapped_column(String(10), default="unknown")  # male|female|unknown
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    weight: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    neuter: Mapped[bool] = mapped_column(Boolean, default=False)
    tagline: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 心情签名
    health_score: Mapped[int] = mapped_column(BigInteger, default=80)  # 0-100 健康评分
    next_vaccine: Mapped[date | None] = mapped_column(Date, nullable=True)  # 下次疫苗日期
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
