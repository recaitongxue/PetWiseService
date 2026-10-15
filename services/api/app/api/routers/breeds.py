"""品种百科路由：狗/猫品种检索与详情。"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok
from app.core.errors import AppError, ErrorCode
from app.models.extra import AnnouncementDismiss
from app.models.breed import Breed
from app.schemas.misc import BreedOut

router = APIRouter(prefix="/breeds", tags=["breeds"])


def _breed_detail(b: Breed) -> dict:
    t = b.traits or {}
    w = []
    if b.min_weight is not None:
        w.append(f"{b.min_weight}")
    if b.max_weight is not None:
        w.append(f"{b.max_weight}")
    weight = " – ".join(w) + " kg" if w else (t.get("weight") or "")
    return {
        "id": b.id,
        "name": b.name,
        "sci": b.alias or t.get("sci") or "",
        "species": b.species,
        "origin": t.get("origin") or "",
        "temperament": t.get("temperament") or [],
        "weight": weight,
        "life": b.lifespan or t.get("life") or "",
        "issues": t.get("issues") or [],
        "care": b.description or t.get("care") or "",
        "feeding": t.get("feeding") or [],
        "aiPrompts": t.get("aiPrompts") or [],
        "coverUrl": b.avatar,
    }


@router.get("", summary="品种列表（按物种/关键词筛选）")
def list_breeds(
    db: DbSession,
    species: str | None = Query(default=None, description="dog | cat"),
    q: str | None = Query(default=None, description="名称或别名模糊匹配"),
) -> dict:
    qry = db.query(Breed)
    if species:
        qry = qry.filter(Breed.species == species)
    if q:
        like = f"%{q}%"
        qry = qry.filter((Breed.name.like(like)) | (Breed.alias.like(like)))
    rows = qry.order_by(Breed.species.asc(), Breed.name.asc()).all()
    return ok(
        [
            {
                "id": r.id,
                "name": r.name,
                "sci": r.alias or "",
                "species": r.species,
                "origin": (r.traits or {}).get("origin") or "",
                "coverUrl": r.avatar,
            }
            for r in rows
        ]
    )


@router.get("/{breed_id}", summary="品种详情")
def breed_detail(breed_id: int, db: DbSession) -> dict:
    b = db.get(Breed, breed_id)
    if b is None:
        raise AppError(ErrorCode.NOT_FOUND, "品种不存在")
    return ok(_breed_detail(b))
