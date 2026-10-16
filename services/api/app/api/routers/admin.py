"""管理端路由：后台总览、公告 CRUD、反馈处理、用户管理、问诊单、识别审核、内容审核、平台设置。

全部接口要求 role=admin（依赖 AdminUser），管理端用管理员手机号走同一套验证码登录即可。
列表接口统一走 paged() 信封；注意 paged() 内部已包 ok()，不要再套一层 ok()。
"""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Query

from app.core.deps import AdminUser, DbSession
from app.core.envelope import ok, paged
from app.core.errors import AppError, ErrorCode
from app.models.announcement import Announcement
from app.models.consult_model import ConsultOrder
from app.models.doctor import Doctor
from app.models.extra import Recognition, Setting
from app.models.feedback import Feedback
from app.models.pet import Pet
from app.models.social import PostReport
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])

DEFAULT_SETTINGS = {
    "aiDailyFree": 3,
    "consultEnabled": True,
    "communityEnabled": True,
    "recognizeEnabled": True,
}


def _fmt(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M") if dt else ""


def _date(dt) -> str:
    return dt.strftime("%Y-%m-%d") if dt else ""


def _ago_days(n: int) -> datetime.datetime:
    return datetime.datetime.now() - datetime.timedelta(days=n)


# ── 总览 ────────────────────────────────────────────────
@router.get("/overview", summary="后台总览（首页看板）")
def overview(_: AdminUser, db: DbSession) -> dict:
    now = datetime.datetime.now()
    today_start = datetime.datetime(now.year, now.month, now.day)

    users = db.query(User).count()
    pets = db.query(Pet).filter(Pet.deleted_at.is_(None)).count()
    doctors = db.query(Doctor).count()
    consults = db.query(ConsultOrder).count()
    ongoing = db.query(ConsultOrder).filter(ConsultOrder.state.in_(["pending", "replied"])).count()
    recognitions = db.query(Recognition).count()
    pending_feedback = db.query(Feedback).filter(Feedback.status == "pending").count()
    pending_reports = db.query(PostReport).filter(PostReport.status == "pending").count()
    pending_corrections = db.query(Recognition).filter(Recognition.status == "review").count()

    def cnt(model, col):
        return db.query(model).filter(col >= today_start).count()

    # 近 7 日趋势
    trend = []
    for i in range(6, -1, -1):
        day = datetime.datetime(now.year, now.month, now.day) - datetime.timedelta(days=i)
        nxt = day + datetime.timedelta(days=1)
        trend.append(
            {
                "day": day.strftime("%m-%d"),
                "consults": db.query(ConsultOrder)
                .filter(ConsultOrder.created_at >= day, ConsultOrder.created_at < nxt)
                .count(),
                "recognitions": db.query(Recognition)
                .filter(Recognition.created_at >= day, Recognition.created_at < nxt)
                .count(),
            }
        )

    def feedback_shape(f: Feedback) -> dict:
        u = db.get(User, f.user_id) if f.user_id else None
        return {
            "id": f.id,
            "userId": f.user_id,
            "userName": (u.nickname if u else None) or f"用户{f.user_id}",
            "type": f.type,
            "content": f.content,
            "contact": f.contact,
            "status": f.status,
            "createdAt": _fmt(f.created_at),
        }

    def report_shape(r: PostReport) -> dict:
        return {
            "id": r.id,
            "postId": r.post_id,
            "postAuthor": r.post_author,
            "postText": r.post_text,
            "reason": r.reason,
            "note": r.note,
            "status": r.status,
            "createdAt": _fmt(r.created_at),
        }

    def rec_shape(r: Recognition) -> dict:
        return {
            "id": r.id,
            "species": r.species,
            "predicted": r.predicted,
            "corrected": r.corrected,
            "confidence": round(float(r.confidence or 0), 2),
            "status": r.status,
            "imageRef": r.image_ref,
            "time": _fmt(r.created_at),
        }

    return ok(
        {
            "stats": {
                "users": users,
                "pets": pets,
                "doctors": doctors,
                "consults": consults,
                "ongoingConsults": ongoing,
                "recognitions": recognitions,
                "pendingFeedback": pending_feedback,
                "pendingReports": pending_reports,
                "pendingCorrections": pending_corrections,
            },
            "today": {
                "newUsers": cnt(User, User.created_at),
                "newConsults": cnt(ConsultOrder, ConsultOrder.created_at),
                "newRecognitions": cnt(Recognition, Recognition.created_at),
                "newFeedback": cnt(Feedback, Feedback.created_at),
            },
            "trend": trend,
            "recentFeedback": [
                feedback_shape(f)
                for f in db.query(Feedback)
                .order_by(Feedback.created_at.desc())
                .limit(5)
                .all()
            ],
            "recentReports": [
                report_shape(r)
                for r in db.query(PostReport)
                .order_by(PostReport.created_at.desc())
                .limit(5)
                .all()
            ],
            "pendingCorrections": [
                rec_shape(r)
                for r in db.query(Recognition)
                .filter(Recognition.status == "review")
                .order_by(Recognition.created_at.desc())
                .limit(5)
                .all()
            ],
        }
    )


# ── 公告 ────────────────────────────────────────────────
def _ann_shape(a: Announcement) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "content": a.content,
        "level": a.level,
        "pinned": bool(a.pinned),
        "publishedAt": _fmt(a.published_at),
        "date": _date(a.published_at),
    }


@router.get("/announcements", summary="公告列表（管理端）")
def list_announcements(
    _: AdminUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
) -> dict:
    q = db.query(Announcement)
    total = q.count()
    rows = (
        q.order_by(Announcement.pinned.desc(), Announcement.published_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return paged([_ann_shape(a) for a in rows], total=total, page=page, page_size=page_size)


@router.post("/announcements", summary="发布公告")
def create_announcement(body: dict, _: AdminUser, db: DbSession) -> dict:
    title = str(body.get("title", "")).strip()
    if not title:
        raise AppError(ErrorCode.BAD_REQUEST, "公告标题不能为空")
    a = Announcement(
        title=title,
        content=str(body.get("content", "")),
        level=body.get("level", "info"),
        pinned=bool(body.get("pinned", False)),
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return ok(_ann_shape(a))


@router.patch("/announcements/{ann_id}", summary="编辑公告")
def update_announcement(ann_id: int, body: dict, _: AdminUser, db: DbSession) -> dict:
    a = db.get(Announcement, ann_id)
    if a is None:
        raise AppError(ErrorCode.NOT_FOUND, "公告不存在")
    for f in ("title", "content", "level"):
        if f in body and body[f] is not None:
            setattr(a, f, body[f])
    if "pinned" in body:
        a.pinned = bool(body["pinned"])
    db.commit()
    return ok(_ann_shape(a))


@router.delete("/announcements/{ann_id}", summary="删除公告")
def delete_announcement(ann_id: int, _: AdminUser, db: DbSession) -> dict:
    a = db.get(Announcement, ann_id)
    if a is None:
        raise AppError(ErrorCode.NOT_FOUND, "公告不存在")
    db.delete(a)
    db.commit()
    return ok({"deleted": True})


# ── 用户反馈 ─────────────────────────────────────────────
@router.get("/feedbacks", summary="反馈列表（可按状态筛选）")
def list_feedbacks(
    _: AdminUser,
    db: DbSession,
    state: str | None = Query(default=None, description="pending|processing|resolved|rejected"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
) -> dict:
    q = db.query(Feedback)
    if state and state != "all":
        q = q.filter(Feedback.status == state)
    total = q.count()
    rows = (
        q.order_by(Feedback.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    users = {u.id: u for u in db.query(User).all()}
    items = []
    for f in rows:
        u = users.get(f.user_id)
        items.append(
            {
                "id": f.id,
                "userId": f.user_id,
                "userName": (u.nickname if u else None) or (f"用户{f.user_id}" if f.user_id else "匿名用户"),
                "type": f.type,
                "content": f.content,
                "contact": f.contact,
                "status": f.status,
                "createdAt": _fmt(f.created_at),
            }
        )
    return paged(items, total=total, page=page, page_size=page_size)


@router.patch("/feedbacks/{fb_id}", summary="处理反馈（改状态）")
def handle_feedback(fb_id: int, body: dict, _: AdminUser, db: DbSession) -> dict:
    f = db.get(Feedback, fb_id)
    if f is None:
        raise AppError(ErrorCode.NOT_FOUND, "反馈不存在")
    status = body.get("status")
    allowed = ("pending", "processing", "resolved", "rejected")
    if status and status in allowed:
        f.status = status
    db.commit()
    return ok(
        {
            "id": f.id,
            "status": f.status,
            "type": f.type,
            "content": f.content,
            "contact": f.contact,
            "userId": f.user_id,
            "createdAt": _fmt(f.created_at),
        }
    )


# ── 用户管理 ─────────────────────────────────────────────
@router.get("/users", summary="用户列表")
def list_users(
    _: AdminUser,
    db: DbSession,
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
) -> dict:
    qry = db.query(User)
    if q:
        like = f"%{q}%"
        qry = qry.filter((User.phone.like(like)) | (User.nickname.like(like)))
    total = qry.count()
    rows = (
        qry.order_by(User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = []
    for u in rows:
        pet_count = db.query(Pet).filter(Pet.owner_id == u.id, Pet.deleted_at.is_(None)).count()
        items.append(
            {
                "id": u.id,
                "phone": u.phone,
                "nickname": u.nickname,
                "name": u.nickname,
                "role": u.role,
                "bio": u.bio or "",
                "balance": float(u.balance or 0),
                "followers": int(u.followers or 0),
                "following": int(u.following or 0),
                "petCount": pet_count,
                "createdAt": _fmt(u.created_at),
            }
        )
    return paged(items, total=total, page=page, page_size=page_size)


@router.patch("/users/{user_id}", summary="修改用户（角色 / 昵称 / 简介）")
def update_user(user_id: int, body: dict, _: AdminUser, db: DbSession) -> dict:
    u = db.get(User, user_id)
    if u is None:
        raise AppError(ErrorCode.NOT_FOUND, "用户不存在")
    if "nickname" in body and body["nickname"]:
        u.nickname = body["nickname"]
    if "bio" in body:
        u.bio = body["bio"]
    if "role" in body and body["role"] in ("user", "admin"):
        u.role = body["role"]
    db.commit()
    return ok(
        {
            "id": u.id,
            "phone": u.phone,
            "nickname": u.nickname,
            "name": u.nickname,
            "role": u.role,
            "bio": u.bio or "",
            "balance": float(u.balance or 0),
        }
    )


# ── 问诊单 ───────────────────────────────────────────────
@router.get("/consults", summary="问诊单列表（管理端，支持关键字搜索）")
def list_consults(
    _: AdminUser,
    db: DbSession,
    state: str | None = Query(default=None),
    q: str | None = Query(default=None, description="宠物名 / 医生名 / 用户名模糊匹配"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
) -> dict:
    qry = db.query(ConsultOrder)
    if state and state != "all":
        qry = qry.filter(ConsultOrder.state == state)
    rows_all = qry.order_by(ConsultOrder.created_at.desc()).all()
    if q:
        like = f"%{q}%"
        matched = []
        for o in rows_all:
            pet = db.get(Pet, o.pet_id) if o.pet_id else None
            doc = db.get(Doctor, o.doctor_id) if str(o.doctor_id or "").isdigit() else None
            usr = db.get(User, o.user_id) if o.user_id else None
            names = (pet.name if pet else "", doc.name if doc else "", usr.nickname if usr else "")
            hay = " ".join(x for x in names if x)
            if like.strip("%") in hay:
                matched.append(o)
        rows_all = matched
    total = len(rows_all)
    rows = rows_all[(page - 1) * page_size: page * page_size]
    items = []
    for o in rows:
        doc = db.get(Doctor, o.doctor_id) if str(o.doctor_id or "").isdigit() else None
        pet = db.get(Pet, o.pet_id) if o.pet_id else None
        user = db.get(User, o.user_id) if o.user_id else None
        items.append(
            {
                "id": o.id,
                "userId": o.user_id,
                "userName": (user.nickname if user else None) or "—",
                "petId": o.pet_id,
                "petName": pet.name if pet else "—",
                "doctorId": o.doctor_id,
                "doctorName": doc.name if doc else "—",
                "mode": o.mode,
                "state": o.state,
                "price": float(o.price or 0),
                "summary": o.summary,
                "createdAt": _fmt(o.created_at),
            }
        )
    return paged(items, total=total, page=page, page_size=page_size)


# ── 识别记录审核 ──────────────────────────────────────────
def _rec_shape(r: Recognition) -> dict:
    return {
        "id": r.id,
        "userId": r.user_id,
        "petId": r.pet_id,
        "species": r.species,
        "predicted": r.predicted,
        "corrected": r.corrected,
        "confidence": round(float(r.confidence or 0), 2),
        "status": r.status,
        "imageRef": r.image_ref,
        "time": _fmt(r.created_at),
    }


@router.get("/records", summary="识别记录列表（含用户纠正）")
def list_records(
    _: AdminUser,
    db: DbSession,
    status: str | None = Query(default=None, description="done|review|confirmed"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
) -> dict:
    q = db.query(Recognition)
    if status and status != "all":
        q = q.filter(Recognition.status == status)
    total = q.count()
    rows = (
        q.order_by(Recognition.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return paged([_rec_shape(r) for r in rows], total=total, page=page, page_size=page_size)


@router.patch("/records/{rec_id}", summary="审核识别纠正（采纳/驳回）")
def review_record(rec_id: str, body: dict, _: AdminUser, db: DbSession) -> dict:
    r = db.get(Recognition, rec_id)
    if r is None:
        raise AppError(ErrorCode.NOT_FOUND, "识别记录不存在")
    status = body.get("status")
    if status in ("done", "review", "confirmed", "rejected"):
        r.status = status
    if "corrected" in body:
        r.corrected = body["corrected"]
    db.commit()
    return ok(_rec_shape(r))


# ── 内容审核（帖子举报） ───────────────────────────────────
def _report_shape(r: PostReport) -> dict:
    return {
        "id": r.id,
        "postId": r.post_id,
        "postAuthor": r.post_author,
        "postText": r.post_text,
        "userId": r.user_id,
        "reason": r.reason,
        "note": r.note,
        "status": r.status,
        "createdAt": _fmt(r.created_at),
    }


@router.get("/reports", summary="举报列表")
def list_reports(
    _: AdminUser,
    db: DbSession,
    status: str | None = Query(default=None, description="pending|resolved|rejected"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
) -> dict:
    q = db.query(PostReport)
    if status and status != "all":
        q = q.filter(PostReport.status == status)
    total = q.count()
    rows = (
        q.order_by(PostReport.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return paged([_report_shape(r) for r in rows], total=total, page=page, page_size=page_size)


@router.patch("/reports/{report_id}", summary="处理举报")
def handle_report(report_id: int, body: dict, _: AdminUser, db: DbSession) -> dict:
    r = db.get(PostReport, report_id)
    if r is None:
        raise AppError(ErrorCode.NOT_FOUND, "举报不存在")
    status = body.get("status")
    if status in ("pending", "resolved", "rejected"):
        r.status = status
    db.commit()
    return ok(_report_shape(r))


# ── 平台设置 ─────────────────────────────────────────────
@router.get("/settings", summary="平台设置")
def get_settings(_: AdminUser, db: DbSession) -> dict:
    data = dict(DEFAULT_SETTINGS)
    for s in db.query(Setting).all():
        if isinstance(s.value, dict):
            # 只接受契约内键，忽略历史遗留的未实现键
            data.update({k: v for k, v in s.value.items() if k in DEFAULT_SETTINGS})
    return ok(data)


@router.put("/settings", summary="更新平台设置")
def put_settings(body: dict, _: AdminUser, db: DbSession) -> dict:
    patch = {k: v for k, v in (body or {}).items() if k in DEFAULT_SETTINGS}
    row = db.get(Setting, "platform")
    cur = dict(DEFAULT_SETTINGS)
    if row and isinstance(row.value, dict):
        cur.update({k: v for k, v in row.value.items() if k in DEFAULT_SETTINGS})
    cur.update(patch)
    if row is None:
        db.add(Setting(key="platform", value=cur))
    else:
        row.value = cur
    db.commit()
    return ok(cur)
