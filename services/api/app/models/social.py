"""社交域模型：通讯录、IM 会话与消息、社区帖子与评论、收藏。"""

from __future__ import annotations

import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # 联系人业务 id，如 ct-aju
    owner_id: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(String(50))
    kind: Mapped[str] = mapped_column(String(16), default="friend")  # vet | group | friend
    bio: Mapped[str | None] = mapped_column(String(200), nullable=True)
    online: Mapped[bool] = mapped_column(Boolean, default=False)
    chat_id: Mapped[str | None] = mapped_column(String(32), nullable=True)  # 直达已有会话
    doctor_id: Mapped[str | None] = mapped_column(String(32), nullable=True)  # 跳兽医资料页
    pet: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)  # {name,breed,age}
    posts: Mapped[int] = mapped_column(Integer, default=0)
    fans: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # 会话 id，如 c1
    owner_id: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(String(50))
    kind: Mapped[str] = mapped_column(String(16), default="friend")
    last: Mapped[str | None] = mapped_column(String(255), nullable=True)
    time: Mapped[str | None] = mapped_column(String(20), nullable=True)
    unread: Mapped[int] = mapped_column(Integer, default=0)
    online: Mapped[bool] = mapped_column(Boolean, default=False)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(32), index=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, index=True)
    role: Mapped[str] = mapped_column(String(16), default="them")  # them | me
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    images: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    time: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # 帖子 id，如 p1
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    author: Mapped[str] = mapped_column(String(50))
    role: Mapped[str | None] = mapped_column(String(16), nullable=True)  # vet 等
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    images: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    likes: Mapped[int] = mapped_column(Integer, default=0)  # 点赞总数（PostLike 行数冗余计数）
    comments: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PostLike(Base):
    """帖子点赞：每用户一行，liked 状态按当前用户实时计算。"""

    __tablename__ = "post_likes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    post_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    name: Mapped[str] = mapped_column(String(50))
    text: Mapped[str] = mapped_column(Text)
    time: Mapped[str | None] = mapped_column(String(20), nullable=True)
    liked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Favorite(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    kind: Mapped[str] = mapped_column(String(16))  # breed | post | tip
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(100))
    desc: Mapped[str | None] = mapped_column(String(200), nullable=True)
    route: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PostReport(Base):
    """社区帖子举报：App 端提交，管理端「内容审核」处理。"""

    __tablename__ = "post_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[str] = mapped_column(String(32), index=True)
    post_author: Mapped[str | None] = mapped_column(String(50), nullable=True)
    post_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    # reason: spam 广告垃圾 | abuse 辱骂 | inappropriate 不宜内容 | other 其他
    reason: Mapped[str] = mapped_column(String(30), default="other")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # status: pending 待处理 | resolved 已处理（保留）| rejected 已驳回
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
