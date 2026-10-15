"""日程提醒 Schema。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    pet_id: int
    title: str
    note: str | None = None
    category: str = "other"
    due_at: datetime
    done: bool = False
    done_at: datetime | None = None
    created_at: datetime


class ScheduleCreate(BaseModel):
    pet_id: int
    title: str = Field(min_length=1, max_length=120)
    category: str = "other"
    due_at: datetime
    note: str | None = None


class ScheduleUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    due_at: datetime | None = None
    note: str | None = None
