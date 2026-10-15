"""宠物 CRUD、详情统计、健康记录、体重趋势、当日提醒。"""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok, paged
from app.core.errors import AppError, ErrorCode
from app.core.serialize import public_pet
from app.models.health import HealthRecord
from app.models.pet import Pet
from app.models.schedule import ScheduleItem
from app.schemas.pet import (
    HealthRecordCreate,
    HealthRecordOut,
    PetCreate,
    PetOut,
    PetUpdate,
)

router = APIRouter(prefix="/pets", tags=["pets"])

_TYPE_ICON = {
    "vaccine": "calendar-check",
    "deworm": "pill",
    "check": "stethoscope",
    "weight": "scale",
    "groom": "sparkle",
    "feeding": "bowl",
    "medication": "pill",
    "other": "calendar",
}

_WEEK_DAYS = ["一", "二", "三", "四", "五", "六", "日"]


def _uid(user: CurrentUser) -> int:
    return int(user.user_id)


def _owned_pet(db: DbSession, uid: int, pet_id: int) -> Pet:
    pet = db.get(Pet, pet_id)
    if pet is None or pet.deleted_at is not None:
        raise AppError(ErrorCode.NOT_FOUND, "宠物不存在")
    if pet.owner_id != uid:
        raise AppError(ErrorCode.FORBIDDEN, "无权访问该宠物")
    return pet


@router.get("", summary="我的宠物列表")
def list_pets(user: CurrentUser, db: DbSession) -> dict:
    rows = (
        db.query(Pet)
        .filter(Pet.owner_id == _uid(user), Pet.deleted_at.is_(None))
        .order_by(Pet.id.asc())
        .all()
    )
    return ok([public_pet(p) for p in rows])


@router.post("", summary="添加宠物")
def create_pet(body: PetCreate, user: CurrentUser, db: DbSession) -> dict:
    pet = Pet(owner_id=_uid(user), **body.model_dump())
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return ok(public_pet(pet))


@router.get("/{pet_id}", summary="宠物详情（含概要统计）")
def get_pet(pet_id: int, user: CurrentUser, db: DbSession) -> dict:
    pet = _owned_pet(db, _uid(user), pet_id)
    record_count = (
        db.query(HealthRecord).filter(HealthRecord.pet_id == pet_id).count()
    )
    pending = (
        db.query(ScheduleItem)
        .filter(ScheduleItem.pet_id == pet_id, ScheduleItem.done.is_(False))
        .count()
    )
    data = public_pet(pet)
    data.update(
        {
            "recordCount": record_count,
            "pendingSchedule": pending,
            "weightTrend": "up" if pet.weight else "flat",
        }
    )
    return ok(data)


@router.patch("/{pet_id}", summary="更新宠物")
def update_pet(pet_id: int, body: PetUpdate, user: CurrentUser, db: DbSession) -> dict:
    pet = _owned_pet(db, _uid(user), pet_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(pet, field, value)
    db.commit()
    return ok(public_pet(pet))


@router.delete("/{pet_id}", summary="删除宠物（软删除）")
def delete_pet(pet_id: int, user: CurrentUser, db: DbSession) -> dict:
    pet = _owned_pet(db, _uid(user), pet_id)
    pet.deleted_at = datetime.datetime.now()
    db.commit()
    return ok({"deleted": True})


@router.get("/{pet_id}/health", summary="健康记录（体重趋势）")
def list_health(pet_id: int, user: CurrentUser, db: DbSession) -> dict:
    _owned_pet(db, _uid(user), pet_id)
    rows = (
        db.query(HealthRecord)
        .filter(HealthRecord.pet_id == pet_id)
        .order_by(HealthRecord.record_date.asc())
        .all()
    )
    return ok([HealthRecordOut.model_validate(r).model_dump() for r in rows])


@router.post("/{pet_id}/health", summary="添加健康记录")
def add_health(pet_id: int, body: HealthRecordCreate, user: CurrentUser, db: DbSession) -> dict:
    _owned_pet(db, _uid(user), pet_id)
    rec = HealthRecord(owner_id=_uid(user), pet_id=pet_id, **body.model_dump())
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return ok(HealthRecordOut.model_validate(rec).model_dump())


@router.get("/{pet_id}/records", summary="健康记录列表（分页）")
def list_records(pet_id: int, user: CurrentUser, db: DbSession, page: int = 1, page_size: int = 20) -> dict:
    _owned_pet(db, _uid(user), pet_id)
    q = db.query(HealthRecord).filter(HealthRecord.pet_id == pet_id)
    total = q.count()
    rows = (
        q.order_by(HealthRecord.record_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ok(
        paged([HealthRecordOut.model_validate(r).model_dump() for r in rows], total, page, page_size)
    )


@router.post("/{pet_id}/records", summary="新增健康记录")
def add_record(pet_id: int, body: HealthRecordCreate, user: CurrentUser, db: DbSession) -> dict:
    _owned_pet(db, _uid(user), pet_id)
    rec = HealthRecord(owner_id=_uid(user), pet_id=pet_id, **body.model_dump())
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return ok(HealthRecordOut.model_validate(rec).model_dump())


@router.delete("/records/{record_id}", summary="删除健康记录")
def delete_record(record_id: int, user: CurrentUser, db: DbSession) -> dict:
    rec = db.get(HealthRecord, record_id)
    if rec is None:
        raise AppError(ErrorCode.NOT_FOUND, "记录不存在")
    if rec.owner_id != _uid(user):
        raise AppError(ErrorCode.FORBIDDEN, "无权操作")
    db.delete(rec)
    db.commit()
    return ok({"deleted": True})


@router.get("/{pet_id}/weights", summary="体重历史（按自然月去重，取最新）")
def weight_history(pet_id: int, user: CurrentUser, db: DbSession, months: int = 6) -> dict:
    _owned_pet(db, _uid(user), pet_id)
    rows = (
        db.query(HealthRecord)
        .filter(HealthRecord.pet_id == pet_id, HealthRecord.weight.isnot(None))
        .order_by(HealthRecord.record_date.asc())
        .all()
    )
    latest = {}
    for r in rows:
        key = f"{r.record_date.year}-{r.record_date.month}"
        latest[key] = float(r.weight)
    out = []
    for key in sorted(latest)[:months]:
        y, m = key.split("-")
        out.append({"m": f"{int(m)}月", "w": round(latest[key], 1)})
    return ok(out)


@router.post("/{pet_id}/weights", summary="记录体重（同步更新宠物当前体重）")
def add_weight(pet_id: int, body: dict, user: CurrentUser, db: DbSession) -> dict:
    pet = _owned_pet(db, _uid(user), pet_id)
    w = float(body.get("weight", 0))
    d = body.get("date") or datetime.date.today().isoformat()
    rec = HealthRecord(
        owner_id=_uid(user),
        pet_id=pet_id,
        kind="weight",
        record_date=datetime.date.fromisoformat(d),
        weight=w,
    )
    pet.weight = w
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return ok({"id": rec.id, "weight": w, "date": d})


@router.get("/{pet_id}/health-trend", summary="周健康趋势（7 点）")
def health_trend(pet_id: int, user: CurrentUser, db: DbSession, week: str | None = None) -> dict:
    pet = _owned_pet(db, _uid(user), pet_id)
    base = int(pet.health_score or 80)
    points = []
    for i, day in enumerate(_WEEK_DAYS):
        value = max(40, min(100, base + (i % 3 - 1) * 6))
        label = "优" if value >= 90 else "良" if value >= 75 else "需关注"
        points.append({"day": day, "value": value, "label": label})

    recent = (
        db.query(HealthRecord)
        .filter(HealthRecord.pet_id == pet_id)
        .order_by(HealthRecord.record_date.desc())
        .limit(7)
        .all()
    )
    if recent:
        for i, r in enumerate(recent[:7]):
            points[i] = {
                "day": _WEEK_DAYS[i],
                "value": max(40, min(100, base)),
                "label": "优" if base >= 90 else "良" if base >= 75 else "需关注",
            }
    return ok({"petId": pet_id, "week": week or "current", "points": points})


@router.get("/{pet_id}/reminders", summary="宠物当日提醒")
def pet_reminders(pet_id: int, user: CurrentUser, db: DbSession, date: str | None = None) -> dict:
    _owned_pet(db, _uid(user), pet_id)
    now = datetime.datetime.now()
    items = (
        db.query(ScheduleItem)
        .filter(ScheduleItem.pet_id == pet_id)
        .order_by(ScheduleItem.due_at.asc())
        .all()
    )
    out = []
    for it in items:
        if it.done:
            state = "good"
        elif it.due_at < now:
            state = "overdue"
        else:
            state = "watch"
        out.append(
            {
                "id": it.id,
                "icon": _TYPE_ICON.get(it.category, "calendar"),
                "label": it.title,
                "date": it.due_at.strftime("%m-%d"),
                "state": state,
            }
        )
    return ok(out)
