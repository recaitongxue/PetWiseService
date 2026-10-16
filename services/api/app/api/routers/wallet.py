"""钱包路由：余额、充值、提现与流水。

演示环境不接真实支付渠道：充值直接到账，提现直接扣减，
但余额与流水都是真实落库的数据（User.balance 为权威值，流水可对账）。

production 应替换为支付网关下单 + 回调，接口形状保持一致即可。
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok
from app.core.errors import AppError, ErrorCode
from app.models.extra import WalletTx
from app.models.user import User

router = APIRouter(prefix="/wallet", tags=["wallet"])

_MAX_AMOUNT = 100000.0


def _uid(user: CurrentUser) -> int:
    return int(user.user_id)


def _tx_shape(t: WalletTx) -> dict:
    return {
        "id": t.id,
        "type": t.type,  # topup | withdraw
        "amount": float(t.amount or 0),
        "note": t.note or "",
        "time": t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "",
    }


def _amount_of(body: dict) -> float:
    try:
        amount = round(float(body.get("amount", 0)), 2)
    except (TypeError, ValueError) as err:
        raise AppError(ErrorCode.BAD_REQUEST, "金额格式不正确") from err
    if amount <= 0 or amount > _MAX_AMOUNT:
        raise AppError(ErrorCode.BAD_REQUEST, f"金额需在 0 ~ {_MAX_AMOUNT:.0f} 元之间")
    return amount


@router.get("", summary="钱包概况（余额 + 流水）")
def wallet_overview(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
) -> dict:
    uid = _uid(user)
    u = db.get(User, uid)
    if u is None:
        raise AppError(ErrorCode.UNAUTHORIZED, "用户不存在")
    q = db.query(WalletTx).filter(WalletTx.user_id == uid)
    total = q.count()
    rows = q.order_by(WalletTx.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    data = {
        "balance": float(u.balance or 0),
        "list": [_tx_shape(t) for t in rows],
        "total": total,
        "page": page,
        "pageSize": page_size,
        "hasMore": page * page_size < total,
    }
    return ok(data)


@router.post("/topup", summary="充值（演示：直接到账）")
def topup(body: dict, user: CurrentUser, db: DbSession) -> dict:
    uid = _uid(user)
    u = db.get(User, uid)
    if u is None:
        raise AppError(ErrorCode.UNAUTHORIZED, "用户不存在")
    amount = _amount_of(body)
    u.balance = float(u.balance or 0) + amount
    tx = WalletTx(user_id=uid, type="topup", amount=amount, note=str(body.get("note") or "余额充值"))
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return ok({"balance": float(u.balance or 0), "tx": _tx_shape(tx)})


@router.post("/withdraw", summary="提现（校验余额后扣减）")
def withdraw(body: dict, user: CurrentUser, db: DbSession) -> dict:
    uid = _uid(user)
    u = db.get(User, uid)
    if u is None:
        raise AppError(ErrorCode.UNAUTHORIZED, "用户不存在")
    amount = _amount_of(body)
    if amount > float(u.balance or 0):
        raise AppError(ErrorCode.CONFLICT, "余额不足")
    u.balance = float(u.balance or 0) - amount
    tx = WalletTx(user_id=uid, type="withdraw", amount=amount, note=str(body.get("note") or "提现到微信"))
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return ok({"balance": float(u.balance or 0), "tx": _tx_shape(tx)})
