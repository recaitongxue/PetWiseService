"""医生路由：在线医生列表 / 详情 / 评价。

契约路径 GET /doctors、GET /doctors/{id}、GET /doctors/{id}/reviews（无 /consult 前缀）。
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.deps import DbSession
from app.core.envelope import ok
from app.core.errors import AppError, ErrorCode
from app.core.serialize import public_doctor
from app.models.doctor import Doctor

router = APIRouter(prefix="/doctors", tags=["doctors"])

_DEMO_REVIEWS = [
    {"id": "rv1", "user": "橘座本座", "rating": 5, "text": "问得很细，最后只是小问题，省了一趟医院。", "time": "2 天前"},
    {"id": "rv2", "user": "豆豆妈", "rating": 5, "text": "有耐心，把用药剂量写得清清楚楚。", "time": "5 天前"},
]


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


@router.get("/{doctor_id}", summary="医生详情")
def doctor_detail(doctor_id: int, db: DbSession) -> dict:
    d = db.get(Doctor, doctor_id)
    if d is None:
        raise AppError(ErrorCode.NOT_FOUND, "医生不存在")
    data = public_doctor(d)
    data["reviews"] = list(_DEMO_REVIEWS)
    return ok(data)


@router.get("/{doctor_id}/reviews", summary="医生评价列表")
def doctor_reviews(doctor_id: int, db: DbSession, page: int = 1, page_size: int = 20) -> dict:
    return ok(
        {
            "list": list(_DEMO_REVIEWS),
            "total": len(_DEMO_REVIEWS),
            "page": page,
            "pageSize": page_size,
            "hasMore": False,
        }
    )
