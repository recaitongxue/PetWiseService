"""统一序列化：把 ORM 对象转成前端契约需要的字段形状。

集中在此处，避免各路由重复拼装；前端按这些字段渲染即可。
"""

from __future__ import annotations

import datetime


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def public_user(u) -> dict:
    nickname = u.nickname or f"宠主{str(u.phone)[-4:]}"
    return {
        "id": u.id,
        "phone": u.phone,
        "nickname": nickname,
        "name": nickname,
        "handle": u.handle or f"@user{str(u.phone)[-4:]}",
        "avatar": u.avatar,
        "avatarUrl": u.avatar,
        "role": u.role,
        "bio": u.bio or "",
        "followers": int(u.followers or 0),
        "following": int(u.following or 0),
        "initials": (nickname or "宠")[0],
        "balance": _to_float(u.balance) or 0,
    }


def _compute_age(birthday) -> int:
    if not birthday:
        return 0
    today = datetime.date.today()
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))


def public_pet(p) -> dict:
    return {
        "id": p.id,
        "ownerId": p.owner_id,
        "name": p.name,
        "species": p.species,
        "breed": p.breed or "",
        "breedId": p.breed_id,
        "gender": p.gender or "未知",
        "birthday": p.birthday.isoformat() if p.birthday else None,
        "age": _compute_age(p.birthday),
        "weight": _to_float(p.weight),
        "avatar": p.avatar,
        "avatarUrl": p.avatar,
        "neuter": bool(p.neuter),
        "tagline": p.tagline or "",
        "healthScore": int(p.health_score or 80),
        "nextVaccine": p.next_vaccine.isoformat() if p.next_vaccine else None,
    }


def _schedule_state(item, now: datetime.datetime) -> str:
    if item.done:
        return "done"
    if item.due_at < now:
        return "overdue"
    today_start = datetime.datetime(now.year, now.month, now.day)
    if item.due_at < today_start + datetime.timedelta(days=1):
        return "today"
    if item.due_at < now + datetime.timedelta(days=7):
        return "soon"
    return "future"


def public_schedule(item, pet=None, now: datetime.datetime | None = None) -> dict:
    now = now or datetime.datetime.now()
    return {
        "id": item.id,
        "petId": item.pet_id,
        "petName": pet.name if pet else None,
        "title": item.title,
        "type": item.category,
        "date": item.due_at.strftime("%Y-%m-%d"),
        "cycle": item.cycle,
        "custom": bool(item.custom),
        "done": bool(item.done),
        "state": _schedule_state(item, now),
        "note": item.note,
    }


def public_doctor(d) -> dict:
    return {
        "id": d.id,
        "name": d.name,
        "title": d.title,
        "dept": d.department,
        "deptLabel": d.dept_label or d.department,
        "hospital": d.hospital,
        "years": int(d.years or 0),
        "rating": _to_float(d.rating),
        "consults": int(d.consult_count or 0),
        "online": bool(d.online),
        "responseMin": int(d.response_min or 0),
        "tags": d.specialties or [],
        "good": d.good_at or [],
        "slot": d.slot,
        "avatarUrl": d.avatar,
        "intro": d.intro,
        "certs": d.certs or [],
    }
