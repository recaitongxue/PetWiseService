"""宠物品种百科表：狗/猫品种检索与快速建档。"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import BigInteger, DECIMAL, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Breed(Base):
    __tablename__ = "breeds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    species: Mapped[str] = mapped_column(String(10), index=True)  # dog | cat
    name: Mapped[str] = mapped_column(String(50))
    alias: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # traits 形如 {"temperament": ["友善","活泼"], "care": "中等"}
    traits: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    min_weight: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    max_weight: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    lifespan: Mapped[str | None] = mapped_column(String(30), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
