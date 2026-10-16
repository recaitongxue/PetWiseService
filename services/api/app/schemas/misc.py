"""公告、反馈、品种、医生等杂项 Schema。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AnnouncementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    level: str = "info"
    pinned: bool = False
    published_at: datetime


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    content: str
    contact: str | None = None
    status: str = "pending"
    created_at: datetime


class FeedbackCreate(BaseModel):
    type: str = "suggestion"  # bug | suggestion | complaint
    text: str = Field(min_length=1, max_length=2000)  # 契约字段名（对应模型 content 列）
    contact: str | None = Field(default=None, max_length=60)


class BreedOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    species: str
    name: str
    alias: str | None = None
    description: str | None = None
    traits: dict | None = None
    min_weight: Decimal | None = None
    max_weight: Decimal | None = None
    lifespan: str | None = None
    avatar: str | None = None


class DoctorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    title: str = "主治医师"
    hospital: str
    department: str = "全科"
    dept_label: str | None = None
    specialties: list | None = None
    good_at: list | None = None
    avatar: str | None = None
    rating: Decimal | None = None
    consult_count: int = 0
    response_min: int = 0
    years: int = 0
    price: Decimal | None = None
    slot: str | None = None
    intro: str | None = None
    certs: list | None = None
    online: bool = True
