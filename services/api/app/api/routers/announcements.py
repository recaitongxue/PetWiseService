"""公告路由：App 首页公告与公告中心，支持按用户维度关闭（不再展示）。"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok
from app.core.errors import AppError, ErrorCode
from app.models.announcement import Announcement
from app.models.extra import AnnouncementDismiss

router = APIRouter(prefix="/announcements", tags=["announcements"])


def _uid(user: CurrentUser) -> int:
    return int(user.user_id)


def _serialize(a: Announcement) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "body": a.content,
        "date": a.published_at.strftime("%Y-%m-%d") if a.published_at else "",
        "level": a.level,
        "active": True,
    }


@router.get("", summary="生效公告（过滤已关闭）")
def list_announcements(user: CurrentUser, db: DbSession, active: bool = True, limit: int = 50) -> dict:
    dismissed = {
        d.announcement_id
        for d in db.query(AnnouncementDismiss).filter(AnnouncementDismiss.user_id == _uid(user)).all()
    }
    rows = (
        db.query(Announcement)
        .order_by(Announcement.pinned.desc(), Announcement.published_at.desc())
        .limit(limit)
        .all()
    )
    out = [_serialize(a) for a in rows if a.id not in dismissed]
    return ok(out)


@router.post("/{announcement_id}/dismiss", summary="关闭公告（记录用户维度已读）")
def dismiss(announcement_id: int, user: CurrentUser, db: DbSession) -> dict:
    a = db.get(Announcement, announcement_id)
    if a is None:
        raise AppError(ErrorCode.NOT_FOUND, "公告不存在")
    exist = (
        db.query(AnnouncementDismiss)
        .filter(
            AnnouncementDismiss.user_id == _uid(user),
            AnnouncementDismiss.announcement_id == announcement_id,
        )
        .first()
    )
    if exist is None:
        db.add(AnnouncementDismiss(user_id=_uid(user), announcement_id=announcement_id))
        db.commit()
    return ok({"dismissed": True})
