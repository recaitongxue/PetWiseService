"""用户反馈路由：提交与我的反馈列表。"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok
from app.models.feedback import Feedback
from app.schemas.misc import FeedbackCreate, FeedbackOut

router = APIRouter(prefix="/feedbacks", tags=["feedbacks"])


@router.post("", summary="提交反馈")
def submit_feedback(body: FeedbackCreate, user: CurrentUser, db: DbSession) -> dict:
    uid = int(user.user_id)
    fb = Feedback(user_id=uid, type=body.type, content=body.text, contact=body.contact)
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return ok(FeedbackOut.model_validate(fb).model_dump())


@router.get("/mine", summary="我的反馈列表")
def my_feedback(user: CurrentUser, db: DbSession) -> dict:
    rows = (
        db.query(Feedback)
        .filter(Feedback.user_id == int(user.user_id))
        .order_by(Feedback.created_at.desc())
        .all()
    )
    return ok([FeedbackOut.model_validate(r).model_dump() for r in rows])
