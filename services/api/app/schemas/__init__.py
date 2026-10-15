"""Pydantic 响应/请求模型汇总。"""

from __future__ import annotations

from app.schemas.misc import (
    AnnouncementOut,
    BreedOut,
    DoctorOut,
    FeedbackCreate,
    FeedbackOut,
)
from app.schemas.pet import HealthRecordCreate, HealthRecordOut, PetCreate, PetOut, PetUpdate
from app.schemas.schedule import ScheduleCreate, ScheduleOut, ScheduleUpdate
from app.schemas.user import (
    ChangePhoneIn,
    LoginSmsIn,
    PreferencesIn,
    PreferencesOut,
    SmsSendIn,
    UserOut,
)

__all__ = [
    "AnnouncementOut",
    "BreedOut",
    "DoctorOut",
    "FeedbackCreate",
    "FeedbackOut",
    "HealthRecordCreate",
    "HealthRecordOut",
    "PetCreate",
    "PetOut",
    "PetUpdate",
    "ScheduleCreate",
    "ScheduleOut",
    "ScheduleUpdate",
    "ChangePhoneIn",
    "LoginSmsIn",
    "PreferencesIn",
    "PreferencesOut",
    "SmsSendIn",
    "UserOut",
]
