"""用户反馈表：App 端提交，管理端审核。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    # type: bug 故障 | suggestion 建议 | complaint 投诉
    type: Mapped[str] = mapped_column(String(30), default="suggestion")
    content: Mapped[str] = mapped_column(Text)
    contact: Mapped[str | None] = mapped_column(String(60), nullable=True)
    # status: pending 待处理 | processing 处理中 | resolved 已解决 | rejected 已驳回
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
