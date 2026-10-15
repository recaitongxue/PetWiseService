"""收藏路由：品种 / 帖子 / 贴士收藏的增删查。

对应 contentApi.favorites / addFavorite / removeFavorite → /favorites。
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok
from app.core.errors import AppError, ErrorCode
from app.models.social import Favorite

router = APIRouter(prefix="/favorites", tags=["favorites"])


def _uid(user: CurrentUser) -> int:
    return int(user.user_id)


def _shape(f: Favorite) -> dict:
    return {
        "id": f.id,
        "kind": f.kind,
        "title": f.title,
        "desc": f.desc,
        "route": f.route,
    }


@router.get("")
def list_favorites(user: CurrentUser, db: DbSession, kind: str | None = Query(default=None)) -> dict:
    q = db.query(Favorite).filter(Favorite.user_id == _uid(user))
    if kind:
        q = q.filter(Favorite.kind == kind)
    rows = q.order_by(Favorite.created_at.desc()).all()
    return ok([_shape(f) for f in rows])


@router.post("")
def add_favorite(body: dict, user: CurrentUser, db: DbSession) -> dict:
    uid = _uid(user)
    kind = body.get("kind")
    if not kind:
        raise AppError(ErrorCode.BAD_REQUEST, "缺少 kind")
    target_id = str(body.get("targetId") or "") or None
    exist = (
        db.query(Favorite)
        .filter(Favorite.user_id == uid, Favorite.kind == kind, Favorite.target_id == target_id)
        .first()
    )
    if exist:
        return ok(_shape(exist))
    f = Favorite(
        user_id=uid,
        kind=kind,
        target_id=target_id,
        title=body.get("title", ""),
        desc=body.get("desc"),
        route=body.get("route"),
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return ok(_shape(f))


@router.delete("/{kind}/{target_id}")
def remove_favorite(kind: str, target_id: str, user: CurrentUser, db: DbSession) -> dict:
    uid = _uid(user)
    db.query(Favorite).filter(
        Favorite.user_id == uid,
        Favorite.kind == kind,
        Favorite.target_id == str(target_id),
    ).delete()
    db.commit()
    return ok({"deleted": True})
