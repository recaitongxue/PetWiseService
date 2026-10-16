"""用户与账号管理路由：资料、偏好、黑名单、注销校验、改密、换号、第三方绑定。"""

from __future__ import annotations

import datetime
import hashlib

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok
from app.core.errors import AppError, ErrorCode
from app.core.serialize import public_user
from app.core.sms import verify_code
from app.models.consult_model import ConsultMessage, ConsultOrder, ConsultReport
from app.models.doctor import DoctorReview
from app.models.extra import (
    AiUsage,
    AnnouncementDismiss,
    Memo,
    Recognition,
    WalletTx,
)
from app.models.feedback import Feedback
from app.models.health import HealthRecord
from app.models.pet import Pet
from app.models.schedule import ScheduleItem
from app.models.social import (
    Comment,
    Contact,
    Conversation,
    Favorite,
    Message,
    Post,
    PostLike,
    PostReport,
)
from app.models.user import User
from app.schemas.user import (
    BindingsIn,
    ChangePasswordIn,
    ChangePhoneIn,
    PreferencesIn,
    PreferencesOut,
    default_prefs,
)


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


router = APIRouter(prefix="/users", tags=["users"])


def _uid(user: CurrentUser) -> int:
    return int(user.user_id)


def _get_user(db: DbSession, uid: int) -> User:
    u = db.get(User, uid)
    if u is None:
        raise AppError(ErrorCode.UNAUTHORIZED, "用户不存在")
    return u


@router.get("/me", summary="当前用户资料")
def me(user: CurrentUser, db: DbSession) -> dict:
    return ok(public_user(_get_user(db, _uid(user))))


@router.patch("/me", summary="更新昵称/头像/简介")
def update_me(body: dict, user: CurrentUser, db: DbSession) -> dict:
    u = _get_user(db, _uid(user))
    for f in ("nickname", "avatar", "handle", "bio"):
        if f in body and body[f] is not None:
            setattr(u, f, body[f])
    db.commit()
    return ok(public_user(u))


@router.get("/preferences", summary="账号偏好")
def get_prefs(user: CurrentUser, db: DbSession) -> dict:
    u = _get_user(db, _uid(user))
    base = default_prefs()
    if isinstance(u.prefs, dict):
        base.update({k: v for k, v in u.prefs.items() if k in base})
        if isinstance(u.prefs.get("binds"), dict):
            base["binds"].update(u.prefs["binds"])
    return ok(PreferencesOut(**base).model_dump())


@router.put("/preferences", summary="更新账号偏好")
def put_prefs(body: PreferencesIn, user: CurrentUser, db: DbSession) -> dict:
    u = _get_user(db, _uid(user))
    cur = default_prefs()
    if isinstance(u.prefs, dict):
        cur.update({k: v for k, v in u.prefs.items() if k in cur})
    if body.personalized is not None:
        cur["personalized"] = body.personalized
    if body.visibility is not None:
        cur["visibility"] = body.visibility
    if body.binds is not None:
        cur["binds"].update(body.binds)
    u.prefs = cur
    db.commit()
    return ok(PreferencesOut(**cur).model_dump())


@router.get("/blocked", summary="黑名单列表")
def list_blocked(user: CurrentUser, db: DbSession) -> dict:
    u = _get_user(db, _uid(user))
    return ok({"list": u.blocked if isinstance(u.blocked, list) else []})


@router.post("/blocked", summary="加入黑名单")
def add_blocked(body: dict, user: CurrentUser, db: DbSession) -> dict:
    cid = str(body.get("id", ""))
    if not cid:
        raise AppError(ErrorCode.BAD_REQUEST, "缺少联系人 id")
    u = _get_user(db, _uid(user))
    blocked = u.blocked if isinstance(u.blocked, list) else []
    if not any(b.get("id") == cid for b in blocked):
        blocked.append({"id": cid, "name": str(body.get("name", ""))})
    u.blocked = blocked
    db.commit()
    return ok({"list": blocked})


@router.delete("/blocked/{contact_id}", summary="移出黑名单")
def remove_blocked(contact_id: str, user: CurrentUser, db: DbSession) -> dict:
    u = _get_user(db, _uid(user))
    blocked = [b for b in (u.blocked or []) if b.get("id") != contact_id]
    u.blocked = blocked
    db.commit()
    return ok({"list": blocked})


@router.get("/balance", summary="账户余额（注销前校验）")
def get_balance(user: CurrentUser, db: DbSession) -> dict:
    u = _get_user(db, _uid(user))
    return ok({"balance": float(u.balance or 0)})


@router.put("/password", summary="修改密码（sha256 存储）")
def change_password(body: ChangePasswordIn, user: CurrentUser, db: DbSession) -> dict:
    u = _get_user(db, _uid(user))
    if u.password_hash and _sha(body.old_password) != u.password_hash:
        raise AppError(ErrorCode(41003), "原密码错误")
    if body.old_password == body.new_password:
        raise AppError(ErrorCode(42203), "新密码不能与原密码相同")
    u.password_hash = _sha(body.new_password)
    db.commit()
    return ok({"changed": True})


@router.post("/phone", summary="更换手机号（需验证新手机号收到的验证码）")
def change_phone(body: ChangePhoneIn, user: CurrentUser, db: DbSession) -> dict:
    if not verify_code(db, body.phone, body.code):
        raise AppError(ErrorCode.BAD_REQUEST, "验证码错误或已过期")
    if db.query(User).filter(User.phone == body.phone).first():
        raise AppError(ErrorCode.CONFLICT, "该手机号已被占用")
    u = _get_user(db, _uid(user))
    u.phone = body.phone
    db.commit()
    return ok(public_user(u))


@router.post("/bindings/{provider}", summary="第三方账号绑定/解绑")
def set_binding(provider: str, body: BindingsIn, user: CurrentUser, db: DbSession) -> dict:
    if provider not in ("wechat", "apple"):
        raise AppError(ErrorCode.BAD_REQUEST, "不支持的绑定类型")
    u = _get_user(db, _uid(user))
    cur = default_prefs()
    if isinstance(u.prefs, dict):
        cur.update(u.prefs)
    binds = cur.setdefault("binds", {"wechat": True, "apple": False})
    binds[provider] = bool(body.bound)
    u.prefs = cur
    db.commit()
    return ok(PreferencesOut(**cur).model_dump())


@router.post("/deactivate", summary="注销账号（余额清零后清除全部个人数据）")
def deactivate(body: dict, user: CurrentUser, db: DbSession) -> dict:
    u = _get_user(db, _uid(user))
    if float(u.balance or 0) > 0:
        raise AppError(ErrorCode.CONFLICT, f"账户仍有余额 ¥{u.balance:.2f}，请先提现或消费后再注销")

    uid = u.id
    order_ids = db.query(ConsultOrder.id).filter(ConsultOrder.user_id == uid).scalar_subquery()
    db.query(ConsultMessage).filter(ConsultMessage.order_id.in_(order_ids)).delete(synchronize_session=False)
    db.query(ConsultReport).filter(ConsultReport.user_id == uid).delete()
    db.query(ConsultOrder).filter(ConsultOrder.user_id == uid).delete()
    db.query(Message).filter(Message.owner_id == uid).delete()
    db.query(Conversation).filter(Conversation.owner_id == uid).delete()
    db.query(Contact).filter(Contact.owner_id == uid).delete()
    db.query(Comment).filter(Comment.user_id == uid).delete()
    db.query(PostReport).filter(PostReport.user_id == uid).delete()
    db.query(Post).filter(Post.user_id == uid).delete()
    db.query(PostLike).filter(PostLike.user_id == uid).delete()
    db.query(DoctorReview).filter(DoctorReview.user_id == uid).delete()
    db.query(Favorite).filter(Favorite.user_id == uid).delete()
    db.query(Recognition).filter(Recognition.user_id == uid).delete()
    db.query(Memo).filter(Memo.user_id == uid).delete()
    db.query(WalletTx).filter(WalletTx.user_id == uid).delete()
    db.query(AiUsage).filter(AiUsage.user_id == uid).delete()
    db.query(AnnouncementDismiss).filter(AnnouncementDismiss.user_id == uid).delete()
    db.query(ScheduleItem).filter(ScheduleItem.owner_id == uid).delete()
    db.query(HealthRecord).filter(HealthRecord.owner_id == uid).delete()
    db.query(Pet).filter(Pet.owner_id == uid).update({Pet.deleted_at: datetime.datetime.now()})
    db.query(Feedback).filter(Feedback.user_id == uid).delete()

    u.nickname = "已注销用户"
    u.password_hash = None
    u.prefs = default_prefs()
    u.blocked = []
    u.handle = None
    u.bio = None
    db.commit()
    return ok({"deactivated": True})
