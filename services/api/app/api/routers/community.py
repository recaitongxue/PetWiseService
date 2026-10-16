"""社区路由：帖子列表/发布、点赞切换、评论、举报。

点赞按用户维度落库（post_likes 表）：liked 状态与点赞总数都对当前用户真实有效。
功能开关 communityEnabled 维护时禁止发帖/点赞/评论（管理端「设置」页可控）。
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok, paged
from app.core.errors import AppError, ErrorCode
from app.models.extra import Setting
from app.models.social import Comment, Post, PostLike, PostReport
from app.models.user import User

router = APIRouter(prefix="/posts", tags=["community"])


def _uid(user: CurrentUser) -> int:
    return int(user.user_id)


def _feature_enabled(db: DbSession) -> bool:
    row = db.get(Setting, "platform")
    return bool((row.value if row and isinstance(row.value, dict) else {}).get("communityEnabled", True))


def _ago(dt) -> str:
    if dt is None:
        return ""
    delta = (time.time() - dt.timestamp()) if hasattr(dt, "timestamp") else 0
    if delta < 60:
        return "刚刚"
    if delta < 3600:
        return f"{int(delta // 60)} 分钟前"
    if delta < 86400:
        return f"{int(delta // 3600)} 小时前"
    return f"{int(delta // 86400)} 天前"


def _post_shape(p: Post, liked_by_me: bool) -> dict:
    return {
        "id": p.id,
        "author": p.author,
        "authorId": p.user_id,
        "role": p.role,
        "avatarUrl": p.avatar,
        "time": _ago(p.created_at),
        "text": p.text,
        "images": p.images or [],
        "tags": p.tags or [],
        "likes": int(p.likes or 0),
        "comments": int(p.comments or 0),
        "liked": liked_by_me,
    }


def _liked_post_ids(db: DbSession, uid: int, post_ids: list[str]) -> set[str]:
    if not post_ids:
        return set()
    rows = (
        db.query(PostLike.post_id)
        .filter(PostLike.user_id == uid, PostLike.post_id.in_(post_ids))
        .all()
    )
    return {r[0] for r in rows}


def _comment_shape(c: Comment) -> dict:
    return {
        "id": c.id,
        "userId": c.user_id,
        "name": c.name,
        "text": c.text,
        "time": _ago(c.created_at),
        "liked": bool(c.liked),
    }


def _new_id(prefix: str) -> str:
    return f"{prefix}{int(time.time() * 1000)}"


@router.get("")
def list_posts(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
    tag: str | None = Query(default=None),
) -> dict:
    q = db.query(Post)
    if tag:
        q = q.filter(Post.tags.any(tag))
    total = q.count()
    rows = (
        q.order_by(Post.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    liked = _liked_post_ids(db, _uid(user), [p.id for p in rows])
    return paged([_post_shape(p, p.id in liked) for p in rows], total=total, page=page, page_size=page_size)


@router.get("/{post_id}")
def get_post(post_id: str, user: CurrentUser, db: DbSession) -> dict:
    p = db.get(Post, post_id)
    if p is None:
        raise AppError(ErrorCode.NOT_FOUND, "帖子不存在")
    liked = _liked_post_ids(db, _uid(user), [p.id])
    return ok(_post_shape(p, p.id in liked))


@router.post("")
def publish_post(body: dict, user: CurrentUser, db: DbSession) -> dict:
    if not _feature_enabled(db):
        raise AppError(ErrorCode.FORBIDDEN, "社区维护中，暂不可发布")
    me = db.get(User, _uid(user))
    p = Post(
        id=_new_id("p"),
        user_id=_uid(user),
        author=me.nickname if me else "宠主",
        role=me.role if me else "user",
        avatar=me.avatar if me else None,
        text=str(body.get("text", "")),
        images=body.get("images") or [],
        tags=body.get("tags") or [],
        likes=0,
        comments=0,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return ok(_post_shape(p, False))


@router.post("/{post_id}/like", summary="点赞 / 取消点赞（同一端点切换）")
def like_post(post_id: str, user: CurrentUser, db: DbSession) -> dict:
    if not _feature_enabled(db):
        raise AppError(ErrorCode.FORBIDDEN, "社区维护中，暂不可互动")
    uid = _uid(user)
    p = db.get(Post, post_id)
    if p is None:
        raise AppError(ErrorCode.NOT_FOUND, "帖子不存在")
    exist = (
        db.query(PostLike)
        .filter(PostLike.post_id == post_id, PostLike.user_id == uid)
        .first()
    )
    if exist is None:
        db.add(PostLike(post_id=post_id, user_id=uid))
        p.likes = int(p.likes or 0) + 1
        liked = True
    else:
        db.delete(exist)
        p.likes = max(0, int(p.likes or 0) - 1)
        liked = False
    db.commit()
    return ok({"id": p.id, "liked": liked, "likes": int(p.likes or 0)})


@router.get("/{post_id}/comments", summary="帖子评论列表")
def list_comments(
    post_id: str,
    user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, le=200),
) -> dict:
    q = db.query(Comment).filter(Comment.post_id == post_id)
    total = q.count()
    rows = (
        q.order_by(Comment.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return paged([_comment_shape(c) for c in rows], total=total, page=page, page_size=page_size)


@router.post("/{post_id}/comments", summary="发表评论")
def add_comment(post_id: str, body: dict, user: CurrentUser, db: DbSession) -> dict:
    if not _feature_enabled(db):
        raise AppError(ErrorCode.FORBIDDEN, "社区维护中，暂不可互动")
    p = db.get(Post, post_id)
    if p is None:
        raise AppError(ErrorCode.NOT_FOUND, "帖子不存在")
    me = db.get(User, _uid(user))
    c = Comment(
        id=_new_id("cm"),
        post_id=post_id,
        user_id=_uid(user),
        name=me.nickname if me else "宠主",
        text=str(body.get("text", "")),
    )
    db.add(c)
    p.comments = int(p.comments or 0) + 1
    db.commit()
    db.refresh(c)
    return ok(_comment_shape(c))


@router.post("/{post_id}/report", summary="举报帖子（落库，供管理端审核）")
def report_post(post_id: str, body: dict, user: CurrentUser, db: DbSession) -> dict:
    p = db.get(Post, post_id)
    if p is None:
        raise AppError(ErrorCode.NOT_FOUND, "帖子不存在")
    r = PostReport(
        post_id=post_id,
        post_author=p.author,
        post_text=(p.text or "")[:200],
        user_id=_uid(user),
        reason=body.get("reason") or "other",
        note=body.get("note"),
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return ok({"id": r.id, "reported": True})
