"""宠物与健康记录 Schema。"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    name: str
    species: str = "dog"
    breed: str | None = None
    breed_id: int | None = None
    gender: str = "unknown"
    birthday: date | None = None
    weight: Decimal | None = None
    avatar: str | None = None
    neuter: bool = False
    created_at: datetime


class PetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    species: str = "dog"  # dog | cat
    breed: str | None = None
    breed_id: int | None = None
    gender: str = "unknown"
    birthday: date | None = None
    weight: Decimal | None = Field(default=None, ge=0, le=200)
    avatar: str | None = None
    neuter: bool = False


class PetUpdate(BaseModel):
    name: str | None = None
    species: str | None = None
    breed: str | None = None
    breed_id: int | None = None
    gender: str | None = None
    birthday: date | None = None
    weight: Decimal | None = Field(default=None, ge=0, le=200)
    avatar: str | None = None
    neuter: bool | None = None


class HealthRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pet_id: int
    kind: str = "weight"
    record_date: date
    weight: Decimal | None = None
    metrics: dict | None = None
    note: str | None = None
    created_at: datetime


class HealthRecordCreate(BaseModel):
    kind: str = "weight"  # weight|diet|symptom|care
    record_date: date
    weight: Decimal | None = Field(default=None, ge=0, le=200)
    metrics: dict | None = None
    note: str | None = None
