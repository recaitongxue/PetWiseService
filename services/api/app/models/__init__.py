"""ORM 模型汇总：create_all 与 alembic 均从这里导入表结构。"""

from __future__ import annotations

from app.models.announcement import Announcement
from app.models.breed import Breed
from app.models.consult_model import ConsultMessage, ConsultOrder, ConsultReport
from app.models.doctor import Doctor, DoctorReview
from app.models.extra import (
    AiUsage,
    AnnouncementDismiss,
    Memo,
    Recognition,
    Setting,
    WalletTx,
)
from app.models.feedback import Feedback
from app.models.health import HealthRecord
from app.models.pet import Pet
from app.models.schedule import ScheduleItem
from app.models.sms_code import SmsCode
from app.models.social import (
    Comment,
    Contact,
    Conversation,
    Favorite,
    Message,
    Post,
    PostLike,
    PostReport,
)
from app.models.user import User

__all__ = [
    "Announcement",
    "Breed",
    "Doctor",
    "DoctorReview",
    "AiUsage",
    "AnnouncementDismiss",
    "Memo",
    "Recognition",
    "Setting",
    "WalletTx",
    "Feedback",
    "HealthRecord",
    "Pet",
    "ScheduleItem",
    "SmsCode",
    "Contact",
    "Conversation",
    "Message",
    "Post",
    "PostLike",
    "Comment",
    "Favorite",
    "PostReport",
    "ConsultOrder",
    "ConsultMessage",
    "ConsultReport",
    "User",
]
