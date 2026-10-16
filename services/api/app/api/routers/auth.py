"""鉴权路由：短信验证码登录（演示环境支持调试码）、刷新、登出。

演示环境（PW_SMS_DEBUG=true）下，任何手机号可用固定调试码 888888 登录，
且服务端会打印真实验证码到日志，方便联调。生产需关闭调试码并接真实短信网关。
"""

from __future__ import annotations

import datetime
import hashlib
import random

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok
from app.core.errors import AppError, ErrorCode
from app.core.logging import get_logger
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.sms import DEBUG_CODE, verify_code
from app.models.sms_code import SmsCode
from app.models.user import User
from app.schemas.user import LoginSmsIn, SmsSendIn, sms_debug_enabled

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def _gen_code() -> str:
    return f"{random.randint(0, 999999):06d}"


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _user_claims(user: User) -> dict:
    nickname = user.nickname or f"宠主{user.phone[-4:]}"
    return {
        "id": user.id,
        "phone": user.phone,
        "nickname": nickname,
        "name": nickname,
        "handle": user.handle or f"@user{user.phone[-4:]}",
        "avatar": user.avatar,
        "avatarUrl": user.avatar,
        "role": user.role,
        "bio": user.bio,
        "followers": user.followers or 0,
        "following": user.following or 0,
        "initials": (nickname or "宠")[0],
        "balance": float(user.balance or 0),
    }


@router.post("/sms/send", summary="发送短信验证码")
def send_sms(body: SmsSendIn, db: DbSession) -> dict:
    code = DEBUG_CODE if sms_debug_enabled() else _gen_code()
    expires = datetime.datetime.now() + datetime.timedelta(minutes=5)
    db.add(SmsCode(phone=body.phone, code=code, scene=body.scene, expires_at=expires))
    db.commit()
    if sms_debug_enabled():
        logger.info("DEV 验证码 phone=%s code=%s", body.phone, code)
    return ok({"sent": True, "debugCode": code if sms_debug_enabled() else None})


@router.post("/verification-codes", summary="发送短信验证码（契约路径）")
def send_verification_codes(body: SmsSendIn, db: DbSession) -> dict:
    return send_sms(body, db)


@router.post("/login/sms", summary="短信验证码登录")
def login_sms(body: LoginSmsIn, db: DbSession) -> dict:
    return _do_login(body.phone, body.code, db)


@router.post("/login", summary="登录（短信 / 密码）")
def login(body: dict, db: DbSession) -> dict:
    mode = (body or {}).get("mode", "sms")
    phone = (body or {}).get("phone")
    if mode == "password":
        password = (body or {}).get("password") or ""
        if not phone or not password:
            raise AppError(ErrorCode.BAD_REQUEST, "缺少手机号或密码")
        return _do_password_login(phone, password, db)
    code = (body or {}).get("code")
    if not phone or not code:
        raise AppError(ErrorCode.BAD_REQUEST, "缺少手机号或验证码")
    return _do_login(phone, code, db)


def _do_password_login(phone: str, password: str, db: DbSession) -> dict:
    user = db.query(User).filter(User.phone == phone).first()
    if user is None or not user.password_hash:
        raise AppError(ErrorCode.BAD_REQUEST, "该手机号未注册或未设置密码，请用验证码登录")
    if _sha256(password) != user.password_hash:
        raise AppError(ErrorCode.BAD_REQUEST, "手机号或密码错误")
    return _issue_tokens(user)


def _do_login(phone: str, code: str, db: DbSession) -> dict:
    if not verify_code(db, phone, code, scene="login"):
        raise AppError(ErrorCode.BAD_REQUEST, "验证码错误或已过期")

    user = db.query(User).filter(User.phone == phone).first()
    if user is None:
        user = User(phone=phone, nickname=f"宠主{phone[-4:]}")
        db.add(user)
        db.commit()
        db.refresh(user)
    return _issue_tokens(user)


def _issue_tokens(user: User) -> dict:
    access, expires_in = create_access_token(str(user.id), role=user.role)
    refresh, _ = create_refresh_token(str(user.id))
    return ok(
        {
            "accessToken": access,
            "refreshToken": refresh,
            "expiresIn": expires_in,
            "user": _user_claims(user),
        }
    )


@router.post("/refresh", summary="刷新 access token")
def refresh(body: dict, db: DbSession) -> dict:
    token = (body or {}).get("refreshToken")
    if not token:
        raise AppError(ErrorCode.BAD_REQUEST, "缺少 refreshToken")
    payload = decode_token(token, expected_type="refresh")
    user = db.get(User, int(payload.user_id))
    if user is None:
        raise AppError(ErrorCode.UNAUTHORIZED, "用户不存在")
    access, expires_in = create_access_token(str(user.id), role=user.role)
    return ok({"accessToken": access, "expiresIn": expires_in})


@router.post("/logout", summary="登出（无状态，客户端丢弃令牌即可）")
def logout(_: CurrentUser) -> dict:
    return ok({"loggedOut": True})
