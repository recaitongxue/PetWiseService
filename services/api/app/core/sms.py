"""短信验证码校验（登录 / 换绑手机号共用，口径唯一）。"""

from __future__ import annotations

import datetime

from sqlalchemy.orm import Session

from app.models.sms_code import SmsCode
from app.schemas.user import sms_debug_enabled

DEBUG_CODE = "888888"


def verify_code(db: Session, phone: str, code: str, scene: str | None = None) -> bool:
    """校验并消费一次验证码。

    演示环境（PW_SMS_DEBUG=true）下固定调试码直接通过；
    否则取该手机号最新一条未消费且未过期的验证码比对，命中即消费。
    """
    if sms_debug_enabled() and code == DEBUG_CODE:
        return True
    now = datetime.datetime.now()
    q = db.query(SmsCode).filter(
        SmsCode.phone == phone,
        SmsCode.consumed.is_(False),
        SmsCode.expires_at > now,
    )
    if scene:
        q = q.filter(SmsCode.scene == scene)
    rec = q.order_by(SmsCode.id.desc()).first()
    if rec is None or rec.code != code:
        return False
    rec.consumed = True
    db.commit()
    return True
