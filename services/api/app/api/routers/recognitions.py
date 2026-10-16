"""拍照识别路由：图片上传即识别、历史列表、异步任务查询、用户纠正回流。

**当前为演示识别**：服务端未接入视觉模型，按 species 从品种库取一个品种作为结果，
响应中 ``demo: true`` 明确标注，前端展示「演示识别」徽标。接入真实模型时
替换 ``_demo_recognize`` 即可，契约不变。用户纠正后标记 status=review，
供管理端审核回流训练集。
"""

from __future__ import annotations

import time

from fastapi import APIRouter, File, Form, Query, UploadFile

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok, paged
from app.core.errors import AppError, ErrorCode
from app.core.storage import save_upload
from app.models.breed import Breed
from app.models.extra import Recognition, Setting

router = APIRouter(prefix="/recognitions", tags=["recognitions"])

_SCI = {"dog": "Canis lupus familiaris", "cat": "Felis catus"}


def _uid(user: CurrentUser) -> int:
    return int(user.user_id)


def _feature_enabled(db: DbSession) -> bool:
    row = db.get(Setting, "platform")
    return bool((row.value if row and isinstance(row.value, dict) else {}).get("recognizeEnabled", True))


def _breed_profile(b: Breed) -> dict:
    traits = b.traits or {}
    weight = f"{float(b.min_weight)}~{float(b.max_weight)}kg" if b.min_weight and b.max_weight else ""
    return {
        "id": b.id,
        "name": b.name,
        "alias": b.alias,
        "origin": traits.get("origin", ""),
        "temperament": traits.get("temperament", []),
        "weight": weight or traits.get("weight", ""),
        "life": b.lifespan or traits.get("life", ""),
        "care": traits.get("care", ""),
        "feeding": traits.get("feeding", ""),
        "issues": traits.get("issues", []),
        "coverUrl": b.avatar,
    }


def _pick_breed(db: DbSession, species: str | None):
    q = db.query(Breed)
    if species in ("dog", "cat"):
        q = q.filter(Breed.species == species)
    return q.order_by(Breed.id.asc()).first()


def _demo_recognize(db: DbSession, species: str | None) -> dict:
    breed = _pick_breed(db, species)
    if breed is None:
        # 极端兜底：库里没有品种数据时返回通用结果
        sp = species or "cat"
        return {
            "title": "英国短毛猫" if sp == "cat" else "柯基犬",
            "sci": _SCI.get(sp, "Felis catus"),
            "confidence": 0.86,
            "species": sp,
            "breedId": None,
            "risk": "confirmed",
            "alternatives": [],
            "breedProfile": None,
        }
    others = (
        db.query(Breed)
        .filter(Breed.species == breed.species, Breed.id != breed.id)
        .limit(3)
        .all()
    )
    alternatives = [
        {"name": o.name, "confidence": round(max(0.1, 0.9 - 0.2 * i), 2)}
        for i, o in enumerate(others)
    ]
    return {
        "title": breed.name,
        "sci": (breed.traits or {}).get("sci") or _SCI.get(breed.species, ""),
        "confidence": 0.92,
        "species": breed.species,
        "breedId": breed.id,
        "risk": "confirmed",
        "alternatives": alternatives,
        "breedProfile": _breed_profile(breed),
    }


@router.post("", summary="上传图片并识别（演示识别，结果带 demo 标记）")
async def recognize(
    user: CurrentUser,
    db: DbSession,
    file: UploadFile | None = File(default=None),
    pet_id: int | None = Form(default=None),
    species: str | None = Form(default=None),
) -> dict:
    if not _feature_enabled(db):
        raise AppError(ErrorCode.FORBIDDEN, "识别功能维护中，暂不可用")
    image_ref = None
    if file is not None and file.filename:
        image_ref, _ = save_upload(file)
    result = _demo_recognize(db, species)
    rec = Recognition(
        id=f"rc{int(time.time() * 1000)}",
        user_id=_uid(user),
        pet_id=pet_id,
        species=result["species"],
        predicted=result["title"],
        sci=result["sci"],
        confidence=result["confidence"],
        breed_id=result["breedId"],
        alternatives=result["alternatives"],
        status="done",
        image_ref=image_ref,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    out = dict(result)
    out["id"] = rec.id
    out["imageRef"] = image_ref
    out["time"] = rec.created_at.strftime("%Y-%m-%d %H:%M")
    out["demo"] = True  # 未接入视觉模型，明确告知前端
    return ok(out)


@router.get("", summary="识别历史（分页）")
def list_recognitions(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
) -> dict:
    q = db.query(Recognition).filter(Recognition.user_id == _uid(user))
    total = q.count()
    rows = (
        q.order_by(Recognition.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [
        {
            "id": r.id,
            "species": r.species,
            "predicted": r.predicted,
            "sci": r.sci,
            "confidence": round(float(r.confidence or 0), 2),
            "breedId": r.breed_id,
            "corrected": r.corrected,
            "status": r.status,
            "imageRef": r.image_ref,
            "time": r.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for r in rows
    ]
    return paged(items, total=total, page=page, page_size=page_size)


@router.get("/tasks/{task_id}", summary="查询异步识别任务")
def task_status(task_id: str, user: CurrentUser, db: DbSession) -> dict:
    rec = db.get(Recognition, task_id)
    if rec is None or rec.user_id != _uid(user):
        # 任务可能尚未落库（演示为同步），返回 accepted 待轮询即可
        return ok({"state": "accepted", "taskId": task_id})
    return ok(
        {
            "state": "success",
            "taskId": rec.id,
            "result": {
                "id": rec.id,
                "title": rec.predicted,
                "sci": rec.sci,
                "confidence": round(float(rec.confidence or 0), 2),
                "species": rec.species,
                "breedId": rec.breed_id,
                "status": rec.status,
                "imageRef": rec.image_ref,
            },
        }
    )


@router.post("/{rec_id}/correction", summary="用户纠正识别结果")
def correct(rec_id: str, body: dict, user: CurrentUser, db: DbSession) -> dict:
    rec = db.get(Recognition, rec_id)
    if rec is None or rec.user_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "识别记录不存在")
    rec.corrected = str(body.get("breed") or body.get("corrected") or "")
    rec.status = "review"
    db.commit()
    return ok(
        {
            "id": rec.id,
            "corrected": rec.corrected,
            "status": rec.status,
        }
    )
