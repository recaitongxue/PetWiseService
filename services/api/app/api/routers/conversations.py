"""即时消息（IM）路由：会话列表、新建会话、消息收发、已读。

对应 imApi.* → /conversations。
消息以「我」(role=me) 发送存储；为让会话有回应感，发送后按规则追加一条对方
(role=them) 的演示回执消息；不依赖 WebSocket（前端轮询即可）。
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok
from app.core.errors import AppError, ErrorCode
from app.models.social import Contact, Conversation, Message

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _uid(user: CurrentUser) -> int:
    return int(user.user_id)


def _now_text() -> str:
    return time.strftime("%H:%M")


def _conv_shape(c: Conversation) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "kind": c.kind,
        "last": c.last,
        "time": c.time,
        "unread": int(c.unread or 0),
        "online": bool(c.online),
        "avatarUrl": c.avatar,
    }


def _msg_shape(m: Message) -> dict:
    return {
        "id": m.id,
        "role": m.role,
        "text": m.text,
        "time": m.time,
        "images": m.images or [],
    }


@router.get("")
def list_conversations(user: CurrentUser, db: DbSession) -> dict:
    rows = (
        db.query(Conversation)
        .filter(Conversation.owner_id == _uid(user))
        .order_by(Conversation.created_at.desc())
        .all()
    )
    return ok([_conv_shape(c) for c in rows])


@router.post("", summary="新建/复用会话（按联系人）")
def create_conversation(body: dict, user: CurrentUser, db: DbSession) -> dict:
    uid = _uid(user)
    contact_id = body.get("contactId")
    contact = db.get(Contact, contact_id) if contact_id else None
    if contact is None or contact.owner_id != uid:
        raise AppError(ErrorCode.NOT_FOUND, "联系人不存在")
    conv = (
        db.query(Conversation)
        .filter(Conversation.owner_id == uid, Conversation.name == contact.name)
        .first()
    )
    if conv is None:
        conv = Conversation(
            id=f"c{int(time.time() * 1000)}",
            owner_id=uid,
            name=contact.name,
            kind=contact.kind,
            online=bool(contact.online),
            avatar=contact.avatar,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
    return ok(_conv_shape(conv))


@router.get("/{conv_id}/messages", summary="会话消息列表")
def list_messages(
    conv_id: str,
    user: CurrentUser,
    db: DbSession,
    before_id: int | None = Query(default=None),
    limit: int = Query(default=50, le=200),
) -> dict:
    conv = db.get(Conversation, conv_id)
    if conv is None or conv.owner_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "会话不存在")
    q = db.query(Message).filter(Message.conversation_id == conv_id)
    if before_id is not None:
        q = q.filter(Message.id < before_id)
    rows = q.order_by(Message.id.desc()).limit(limit).all()
    has_more = len(rows) == limit
    return ok(
        {
            "list": [_msg_shape(m) for m in reversed(rows)],
            "hasMore": has_more,
        }
    )


@router.post("/{conv_id}/messages", summary="发送消息")
def send_message(conv_id: str, body: dict, user: CurrentUser, db: DbSession) -> dict:
    uid = _uid(user)
    conv = db.get(Conversation, conv_id)
    if conv is None or conv.owner_id != uid:
        raise AppError(ErrorCode.NOT_FOUND, "会话不存在")
    text = str(body.get("text", "")).strip()
    images = body.get("images") or []
    if not text and not images:
        raise AppError(ErrorCode.BAD_REQUEST, "消息不能为空")

    mine = Message(
        conversation_id=conv_id,
        owner_id=uid,
        role="me",
        text=text or None,
        images=images,
        time=_now_text(),
    )
    db.add(mine)
    db.commit()
    db.refresh(mine)

    conv.last = text or "[图片]"
    conv.time = mine.time
    conv.unread = 0

    # 演示回执：对方一条简短回复
    them = Message(
        conversation_id=conv_id,
        owner_id=uid,
        role="them",
        text="收到～我看看情况，稍后回复你。",
        time=_now_text(),
    )
    db.add(them)
    conv.last = them.text
    db.commit()

    return ok({"message": _msg_shape(mine), "reply": _msg_shape(them)})


@router.post("/{conv_id}/read", summary="标记已读")
def read_conversation(conv_id: str, user: CurrentUser, db: DbSession) -> dict:
    conv = db.get(Conversation, conv_id)
    if conv is None or conv.owner_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "会话不存在")
    conv.unread = 0
    db.commit()
    return ok({"unread": 0})
