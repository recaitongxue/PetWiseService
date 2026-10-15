"""通讯录路由：按分组返回当前用户的联系人（好友 / 兽医 / 群聊）。

对应前端 Contacts 页 → GET /contacts?q=。
分组：friend（好友） / vet（兽医） / group（群聊）。成员 shape 与前端契约一致。
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok
from app.models.social import Contact

router = APIRouter(prefix="/contacts", tags=["contacts"])

_GROUP_TITLE = {"friend": "好友", "vet": "兽医", "group": "群聊"}


def _uid(user: CurrentUser) -> int:
    return int(user.user_id)


def _member(c: Contact) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "kind": c.kind,
        "bio": c.bio or "",
        "online": bool(c.online),
        "chatId": c.chat_id,
        "doctorId": c.doctor_id,
        "pet": c.pet or {},
        "posts": int(c.posts or 0),
        "fans": c.fans or "0",
        "avatarUrl": c.avatar,
    }


def _group(kind: str, members: list[Contact]) -> dict:
    return {
        "id": kind,
        "title": _GROUP_TITLE.get(kind, kind),
        "count": len(members),
        "members": [_member(m) for m in members],
    }


@router.get("")
def list_contacts(user: CurrentUser, db: DbSession, q: str | None = Query(default=None)) -> dict:
    uid = _uid(user)
    rows = db.query(Contact).filter(Contact.owner_id == uid).all()
    if q:
        qk = q.lower()
        rows = [
            r for r in rows
            if qk in (r.name or "").lower() or qk in (r.bio or "").lower()
        ]
    groups = []
    for kind in ("friend", "vet", "group"):
        members = [r for r in rows if r.kind == kind]
        if members:
            groups.append(_group(kind, members))
    return ok({"groups": groups, "total": len(rows)})
