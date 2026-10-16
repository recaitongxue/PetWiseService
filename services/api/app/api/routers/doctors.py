"""医生路由：在线医生列表 / 详情 / 评价。

评价为真实数据：用户在问诊单结束后提交（POST /consult/orders/{id}/rating 落库），
医生评分 = 全部真实评价的均值，无评价时展示种子评分。
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.deps import DbSession
from app.core.envelope import ok, paged
from app.core.errors import AppError, ErrorCode
from app.core.serialize import public_doctor
from app.models.doctor import Doctor, DoctorReview

router = APIRouter(prefix="/doctors", tags=["doctors"])


def _review_shape(r: DoctorReview) -> dict:
    return {
        "id": r.id,
        "user": r.user_name or "宠主",
        "rating": int(r.score or 5),
        "text": r.text or "",
        "tags": r.tags or [],
        "time": r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
    }


def _reviews_of(db: DbSession, doctor_id) -> list[DoctorReview]:
    return (
        db.query(DoctorReview)
        .filter(DoctorReview.doctor_id == str(doctor_id))
        .order_by(DoctorReview.id.desc())
        .all()
    )


@router.get("", summary="在线医生列表")
def list_doctors(
    db: DbSession,
    department: str | None = Query(default=None),
    online: bool | None = Query(default=None),
    q: str | None = Query(default=None),
) -> dict:
    qry = db.query(Doctor)
    if department and department != "all":
        qry = qry.filter(Doctor.department == department)
    if online is not None:
        qry = qry.filter(Doctor.online.is_(online))
    if q:
        qk = f"%{q}%"
        qry = qry.filter(Doctor.name.ilike(qk))
    rows = qry.order_by(Doctor.rating.desc()).all()
    return ok([public_doctor(r) for r in rows])


@router.get("/{doctor_id}", summary="医生详情（含真实评价）")
def doctor_detail(doctor_id: int, db: DbSession) -> dict:
    d = db.get(Doctor, doctor_id)
    if d is None:
        raise AppError(ErrorCode.NOT_FOUND, "医生不存在")
    data = public_doctor(d)
    data["reviews"] = [_review_shape(r) for r in _reviews_of(db, d.id)[:5]]
    return ok(data)


@router.get("/{doctor_id}/reviews", summary="医生评价列表（分页）")
def doctor_reviews(
    doctor_id: int,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
) -> dict:
    d = db.get(Doctor, doctor_id)
    if d is None:
        raise AppError(ErrorCode.NOT_FOUND, "医生不存在")
    q = db.query(DoctorReview).filter(DoctorReview.doctor_id == str(doctor_id))
    total = q.count()
    rows = (
        q.order_by(DoctorReview.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return paged([_review_shape(r) for r in rows], total=total, page=page, page_size=page_size)
