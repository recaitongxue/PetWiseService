"""日程提醒表：跨全部宠物的「今日提醒」即来自此表的聚合查询。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ScheduleItem(Base):
    __tablename__ = "schedule_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, index=True)
    pet_id: Mapped[int] = mapped_column(BigInteger, index=True)
    title: Mapped[str] = mapped_column(String(120))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 类别：vaccine 疫苗 | checkup 体检 | medication 喂药 | feeding 喂食 | grooming 美容 | other
    category: Mapped[str] = mapped_column(String(30), default="other")
    cycle: Mapped[str | None] = mapped_column(String(32), nullable=True)  # 周期说明，如「每月一次」
    custom: Mapped[bool] = mapped_column(Boolean, default=False)  # 1 用户自建 / 0 系统周期生成
    due_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    done_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
