"""首页聚合：一次拉取首屏所需全部数据（user/pets/trend/今日看板/公告/贴士/AI 额度）。

对应前端 homeApi.summary() → GET /home?petId=。
避免在首屏并发多个接口，所有首屏数据在此一次性聚合返回。
"""

from __future__ import annotations

import datetime
import os

from fastapi import APIRouter, Query, Request

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok
from app.models.announcement import Announcement
from app.models.extra import AnnouncementDismiss
from app.models.consult_model import ConsultOrder
from app.models.extra import AiUsage
from app.models.pet import Pet
from app.models.schedule import ScheduleItem
from app.models.user import User

router = APIRouter(prefix="/home", tags=["home"])

_AI_DAILY_FREE = 3

_TYPE_ICON = {
    "vaccine": "calendar-check",
    "deworm": "pill",
    "check": "stethoscope",
    "weight": "scale",
    "groom": "sparkle",
    "feed": "bowl",
    "medication": "pill",
    "memo": "notes",
    "other": "calendar",
}
_TYPE_TONE = {
    "vaccine": "coral",
    "deworm": "sage",
    "check": "sand",
    "weight": "peach",
    "groom": "sage",
    "feed": "peach",
    "medication": "sage",
    "memo": "ink",
    "other": "ink",
}


def _uid(user: CurrentUser) -> int:
    return int(user.user_id)


def _greeting() -> str:
    h = datetime.datetime.now().hour
    if h < 6:
        return "凌晨好"
    if h < 12:
        return "早上好"
    if h < 14:
        return "中午好"
    if h < 18:
        return "下午好"
    return "晚上好"


def _rel_days(delta: int) -> str:
    if delta == 0:
        return "今天"
    if delta == 1:
        return "明天"
    if delta == -1:
        return "昨天"
    if delta > 0:
        return f"{delta} 天后"
    return f"{-delta} 天前"


def _trend(pet: Pet | None) -> list[dict]:
    base = int(pet.health_score or 80) if pet else 80
    points = []
    for i, day in enumerate(["一", "二", "三", "四", "五", "六", "日"]):
        v = max(40, min(100, base + (i % 3 - 1) * 5))
        label = "优" if v >= 90 else "良" if v >= 75 else "需关注"
        points.append({"day": day, "value": v, "label": label})
    return points


@router.get("")
def home(user: CurrentUser, db: DbSession, pet_id: int | None = Query(default=None)) -> dict:
    uid = _uid(user)
    me = db.get(User, uid)
    pets = (
        db.query(Pet)
        .filter(Pet.owner_id == uid, Pet.deleted_at.is_(None))
        .order_by(Pet.id.asc())
        .all()
    )
    current = next((p for p in pets if p.id == pet_id), pets[0] if pets else None)
    cur_id = current.id if current else None

    # 公告：过滤当前用户已关闭的
    dismissed = {
        d.announcement_id
        for d in db.query(AnnouncementDismiss).filter(AnnouncementDismiss.user_id == uid).all()
    }
    anns = [
        a for a in db.query(Announcement).order_by(Announcement.published_at.desc()).all()
        if a.id not in dismissed
    ]

    # 今日看板：跨全部宠物的日程聚合
    now = datetime.datetime.now()
    today_start = datetime.datetime(now.year, now.month, now.day)
    today_end = today_start + datetime.timedelta(days=1)
    all_items = db.query(ScheduleItem).filter(ScheduleItem.owner_id == uid).all()
    overdue = sum(1 for i in all_items if not i.done and i.due_at < now)
    today = sum(1 for i in all_items if today_start <= i.due_at < today_end)
    done = sum(1 for i in all_items if i.done)
    pending_total = sum(1 for i in all_items if not i.done)
    pet_pending = {
        p.id: sum(1 for i in all_items if i.pet_id == p.id and not i.done) for p in pets
    }
    upcoming = [i for i in all_items if not i.done and i.due_at <= now + datetime.timedelta(days=7)]
    upcoming.sort(key=lambda i: i.due_at)
    reminders = []
    for it in upcoming[:4]:
        p = next((x for x in pets if x.id == it.pet_id), None)
        delta = (it.due_at.date() - now.date()).days
        reminders.append(
            {
                "id": it.id,
                "petId": it.pet_id,
                "petName": p.name if p else None,
                "species": p.species if p else None,
                "icon": _TYPE_ICON.get(it.category, "calendar"),
                "tone": _TYPE_TONE.get(it.category, "ink"),
                "title": it.title,
                "date": it.due_at.strftime("%Y-%m-%d"),
                "diff": delta,
                "overdue": it.due_at < now,
                "dateText": _rel_days(delta),
                "cycle": it.cycle,
                "done": bool(it.done),
            }
        )
    remaining = max(0, len(upcoming) - 4)

    # AI 额度（每日 3 次）
    today_date = datetime.date.today()
    usage = (
        db.query(AiUsage)
        .filter(AiUsage.user_id == uid, AiUsage.stat_date == today_date)
        .first()
    )
    used = int(usage.used if usage else 0)
    left = max(0, _AI_DAILY_FREE - used)

    # 进行中的问诊单
    ongoing = (
        db.query(ConsultOrder)
        .filter(ConsultOrder.user_id == uid, ConsultOrder.state.in_(["pending", "replied"]))
        .count()
    )

    name = me.nickname if me else "宠主"
    data = {
        "user": {
            "name": name,
            "handle": me.handle if me else "",
            "initials": (name or "宠")[0],
        },
        "pets": [{"id": p.id, "name": p.name} for p in pets],
        "currentPetId": cur_id,
        "greeting": _greeting(),
        "trend": _trend(current),
        "todayBoard": {
            "stats": {"overdue": overdue, "today": today, "done": done, "pending": pending_total},
            "petFilter": "all",
            "pets": [{"id": p.id, "name": p.name, "pending": pet_pending.get(p.id, 0)} for p in pets],
            "reminders": reminders,
            "remaining": remaining,
        },
        "reminders": [
            {
                "icon": _TYPE_ICON.get(it.category, "calendar"),
                "label": it.title,
                "date": it.due_at.strftime("%m-%d"),
                "state": "good" if it.done else ("overdue" if it.due_at < now else "watch"),
            }
            for it in upcoming[:6]
        ],
        "announcements": [
            {
                "id": a.id,
                "title": a.title,
                "body": a.content,
                "date": a.published_at.strftime("%Y-%m-%d") if a.published_at else "",
                "level": a.level,
                "active": True,
            }
            for a in anns[:5]
        ],
        "tips": [
            {"id": 1, "tag": "今日贴士", "title": "换季掉毛期", "body": "每日梳毛 5 分钟，减少毛球症与误食风险。", "tone": "sage"},
            {"id": 2, "tag": "饮水提醒", "title": "骗水小技巧", "body": "用流动饮水机或湿粮拌水，预防泌尿问题。", "tone": "peach"},
        ],
        "quickActions": [
            {"id": "scan", "label": "拍照识别", "sub": "品种 · 体态 · 状态", "icon": "camera", "route": "/recognize", "accent": True},
            {"id": "consult", "label": "在线问诊", "sub": "真人兽医 24h", "icon": "stethoscope", "route": "/consult", "accent": False},
        ],
        "aiQuota": {
            "free": _AI_DAILY_FREE,
            "used": used,
            "left": left,
            "date": today_date.isoformat(),
        },
        "ongoingConsultCount": int(ongoing),
    }
    return ok(data)
