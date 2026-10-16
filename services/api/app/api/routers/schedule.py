"""日程提醒路由：列表、增删改、完成、类型字典、AI 计划、批量写入、备忘录，以及首页聚合。"""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok
from app.core.errors import AppError, ErrorCode
from app.core.serialize import public_schedule
from app.models.extra import Memo
from app.models.pet import Pet
from app.models.schedule import ScheduleItem

router = APIRouter(tags=["schedule"])

SCHEDULE_TYPES = {
    "vaccine": {"label": "疫苗", "icon": "calendar-check", "tone": "coral"},
    "deworm": {"label": "驱虫", "icon": "pill", "tone": "sage"},
    "check": {"label": "体检", "icon": "stethoscope", "tone": "sand"},
    "weight": {"label": "称重", "icon": "scale", "tone": "peach"},
    "groom": {"label": "洗护", "icon": "sparkle", "tone": "sage"},
    "feed": {"label": "喂食", "icon": "bowl", "tone": "peach"},
    "medication": {"label": "喂药", "icon": "pill", "tone": "sage"},
    "memo": {"label": "备忘", "icon": "notes", "tone": "ink"},
    "other": {"label": "自定义", "icon": "calendar", "tone": "ink"},
}


def _uid(user: CurrentUser) -> int:
    return int(user.user_id)


def _owned_item(db: DbSession, uid: int, item_id: int) -> ScheduleItem:
    item = db.get(ScheduleItem, item_id)
    if item is None:
        raise AppError(ErrorCode.NOT_FOUND, "提醒不存在")
    if item.owner_id != uid:
        raise AppError(ErrorCode.FORBIDDEN, "无权访问该提醒")
    return item


def _parse_date(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d") if s else datetime.datetime.now()


@router.get("/schedule", summary="提醒列表（跨全部宠物）")
def list_schedule(
    user: CurrentUser,
    db: DbSession,
    pet_id: int | None = Query(default=None),
    type: str | None = Query(default=None),
    done: bool | None = Query(default=None),
    limit: int = Query(default=50, le=200),
) -> dict:
    uid = _uid(user)
    q = db.query(ScheduleItem).filter(ScheduleItem.owner_id == uid)
    if pet_id is not None:
        q = q.filter(ScheduleItem.pet_id == pet_id)
    if type:
        q = q.filter(ScheduleItem.category == type)
    if done is not None:
        q = q.filter(ScheduleItem.done.is_(done))
    rows = q.order_by(ScheduleItem.due_at.asc()).limit(limit).all()
    pets = {p.id: p for p in db.query(Pet).filter(Pet.owner_id == uid).all()}
    return ok([public_schedule(it, pets.get(it.pet_id)) for it in rows])


@router.post("/schedule", summary="新建提醒")
def create_schedule(body: dict, user: CurrentUser, db: DbSession) -> dict:
    uid = _uid(user)
    pet = db.get(Pet, body.get("petId", body.get("pet_id")))
    if pet is None or pet.owner_id != uid:
        raise AppError(ErrorCode.BAD_REQUEST, "宠物不存在或不属于你")
    item = ScheduleItem(
        owner_id=uid,
        pet_id=pet.id,
        title=body.get("title", "提醒"),
        category=body.get("type", body.get("category", "other")),
        due_at=_parse_date(body.get("date") or body.get("due_at")),
        cycle=body.get("cycle"),
        note=body.get("note"),
        custom=bool(body.get("custom", True)),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return ok(public_schedule(item, pet))


@router.patch("/schedule/{item_id}", summary="更新提醒")
def update_schedule(item_id: int, body: dict, user: CurrentUser, db: DbSession) -> dict:
    item = _owned_item(db, _uid(user), item_id)
    if "title" in body:
        item.title = body["title"]
    if "type" in body or "category" in body:
        item.category = body.get("type", body.get("category"))
    if "date" in body or "due_at" in body:
        item.due_at = _parse_date(body.get("date") or body.get("due_at"))
    if "cycle" in body:
        item.cycle = body["cycle"]
    if "note" in body:
        item.note = body["note"]
    db.commit()
    pet = db.get(Pet, item.pet_id)
    return ok(public_schedule(item, pet))


@router.post("/schedule/{item_id}/done", summary="标记完成/取消完成")
def toggle_done(item_id: int, user: CurrentUser, db: DbSession, done: bool = True) -> dict:
    item = _owned_item(db, _uid(user), item_id)
    item.done = done
    item.done_at = datetime.datetime.now() if done else None
    db.commit()
    pet = db.get(Pet, item.pet_id)
    return ok(public_schedule(item, pet))


@router.delete("/schedule/{item_id}", summary="删除提醒")
def delete_schedule(item_id: int, user: CurrentUser, db: DbSession) -> dict:
    item = _owned_item(db, _uid(user), item_id)
    if not item.custom:
        raise AppError(ErrorCode.CONFLICT, "系统周期提醒不可删除")
    db.delete(item)
    db.commit()
    return ok({"deleted": True})


@router.get("/schedule/types", summary="日程类型字典")
def schedule_types() -> dict:
    return ok(SCHEDULE_TYPES)


@router.post("/schedule/ai-plan", summary="AI 一键生成日程计划（演示规则）")
def ai_plan(body: dict, user: CurrentUser, db: DbSession) -> dict:
    uid = _uid(user)
    pet = db.get(Pet, body.get("petId", body.get("pet_id")))
    if pet is None or pet.owner_id != uid:
        raise AppError(ErrorCode.BAD_REQUEST, "宠物不存在")
    today = datetime.date.today()
    is_dog = pet.species == "dog"
    kitten = (pet.age or 0) <= 1 if hasattr(pet, "age") else False

    def plus(days):
        return (today + datetime.timedelta(days=days)).isoformat()

    vaccine_title = (
        f"年度疫苗（{pet.next_vaccine}）" if pet.next_vaccine
        else ("年度疫苗（犬六联+狂犬）" if is_dog else "年度疫苗（猫三联）")
    )
    items = [
        {"type": "deworm", "title": "体外驱虫", "date": plus(7), "cycle": "每月一次",
         "note": "滴颈后皮肤，用药后 48 小时不洗澡"},
        {"type": "deworm", "title": "体内驱虫", "date": plus(14), "cycle": "每季度一次",
         "note": "空腹喂服，幼宠剂量按体重换算"},
        {"type": "vaccine", "title": vaccine_title, "date": pet.next_vaccine or plus(30),
         "cycle": "每年一次", "note": "接种前一周完成驱虫，接种后观察 30 分钟"},
        {"type": "check", "title": "幼宠基础体检" if kitten else "年度健康体检",
         "date": plus(21 if kitten else 60), "cycle": "每年一次",
         "note": "血常规+生化+便检，老年宠建议加心脏评估"},
        {"type": "groom", "title": "洗澡与吹干护理" if is_dog else "梳毛与指甲护理",
         "date": plus(10), "cycle": "每两周一次" if is_dog else "每周一次",
         "note": "垂耳犬需检查耳道是否进水" if is_dog else "换季期每日梳毛减少毛球症"},
        {"type": "weight", "title": "体重复测", "date": plus(3), "cycle": "每月一次",
         "note": "同一时间空腹称重，记录到健康档案"},
    ]
    return ok(
        {
            "planId": f"sp_{pet.id}_{today.isoformat()}",
            "summary": f"为「{pet.name}」生成 {len(items)} 条养护计划",
            "items": items,
        }
    )


@router.post("/schedule/batch", summary="批量写入计划（按 title+petId 去重）")
def batch_create(body: dict, user: CurrentUser, db: DbSession) -> dict:
    uid = _uid(user)
    items = body.get("items", []) or []
    pet = db.get(Pet, body.get("petId", body.get("pet_id")))
    if pet is None or pet.owner_id != uid:
        raise AppError(ErrorCode.BAD_REQUEST, "宠物不存在")
    existing = {i.title for i in db.query(ScheduleItem).filter(ScheduleItem.pet_id == pet.id).all()}
    created, skipped = [], []
    for it in items:
        title = it.get("title")
        if title in existing:
            skipped.append(title)
            continue
        item = ScheduleItem(
            owner_id=uid,
            pet_id=pet.id,
            title=title,
            category=it.get("type", "other"),
            due_at=_parse_date(it.get("date")),
            cycle=it.get("cycle"),
            note=it.get("note"),
            custom=True,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        created.append(public_schedule(item, pet))
        existing.add(title)
    return ok({"created": created, "skipped": skipped})


@router.get("/memo", summary="备忘录列表")
def list_memo(user: CurrentUser, db: DbSession, pet_id: int | None = Query(default=None)) -> dict:
    uid = _uid(user)
    q = db.query(Memo).filter(Memo.user_id == uid)
    if pet_id is not None:
        q = q.filter(Memo.pet_id == pet_id)
    rows = q.order_by(Memo.pinned.desc(), Memo.created_at.desc()).all()
    return ok(
        [
            {"id": m.id, "petId": m.pet_id, "text": m.text, "pinned": bool(m.pinned),
             "time": m.created_at.strftime("%Y-%m-%d %H:%M")}
            for m in rows
        ]
    )


@router.post("/memo", summary="新增备忘录")
def add_memo(body: dict, user: CurrentUser, db: DbSession) -> dict:
    m = Memo(
        user_id=_uid(user),
        pet_id=body.get("petId", body.get("pet_id")),
        text=str(body.get("text", ""))[:200],
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return ok({"id": m.id, "petId": m.pet_id, "text": m.text, "pinned": False,
               "time": m.created_at.strftime("%Y-%m-%d %H:%M")})


@router.patch("/memo/{memo_id}", summary="置顶/取消置顶")
def pin_memo(memo_id: int, body: dict, user: CurrentUser, db: DbSession) -> dict:
    m = db.get(Memo, memo_id)
    if m is None or m.user_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "备忘录不存在")
    m.pinned = bool(body.get("pinned", not m.pinned))
    db.commit()
    return ok({"id": m.id, "pinned": bool(m.pinned)})


@router.delete("/memo/{memo_id}", summary="删除备忘录")
def delete_memo(memo_id: int, user: CurrentUser, db: DbSession) -> dict:
    m = db.get(Memo, memo_id)
    if m is None or m.user_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "备忘录不存在")
    db.delete(m)
    db.commit()
    return ok({"deleted": True})
