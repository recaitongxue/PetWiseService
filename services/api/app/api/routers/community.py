"""社区路由：帖子列表/发布、点赞切换、评论、举报。

对应 communityApi.* → /posts。
点赞采用「全局计数 + 帖子 liked 标记」的演示实现：单用户演示足够，多用户场景下
liked 仅反映最后一次操作，正式环境应改为每用户点赞表（post_likes）。
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok, paged
from app.core.errors import AppError, ErrorCode
from app.models.social import Comment, Post
from app.models.user import User

router = APIRouter(prefix="/posts", tags=["community"])


def _uid(user: CurrentUser) -> int:
    return int(user.user_id)


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


def _post_shape(p: Post) -> dict:
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
        "liked": bool(p.liked),
    }


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
    return paged([_post_shape(p) for p in rows], total=total, page=page, page_size=page_size)


@router.get("/{post_id}")
def get_post(post_id: str, user: CurrentUser, db: DbSession) -> dict:
    p = db.get(Post, post_id)
    if p is None:
        raise AppError(ErrorCode.NOT_FOUND, "帖子不存在")
    return ok(_post_shape(p))


@router.post("")
def publish_post(body: dict, user: CurrentUser, db: DbSession) -> dict:
    me = db.get(User, _uid(user))
    name = me.nickname if me else "宠主"
    p = Post(
        id=_new_id("p"),
        user_id=_uid(user),
        author=name,
        role=me.role if me else "user",
        avatar=me.avatar if me else None,
        text=str(body.get("text", "")),
        images=body.get("images") or [],
        tags=body.get("tags") or [],
        likes=0,
        comments=0,
        liked=False,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return ok(_post_shape(p))


@router.post("/{post_id}/like")
def like_post(post_id: str, user: CurrentUser, db: DbSession) -> dict:
    p = db.get(Post, post_id)
    if p is None:
        raise AppError(ErrorCode.NOT_FOUND, "帖子不存在")
    if not p.liked:
        p.liked = True
        p.likes = int(p.likes or 0) + 1
        db.commit()
    return ok({"id": p.id, "liked": bool(p.liked), "likes": int(p.likes or 0)})


@router.delete("/{post_id}/like")
def unlike_post(post_id: str, user: CurrentUser, db: DbSession) -> dict:
    p = db.get(Post, post_id)
    if p is None:
        raise AppError(ErrorCode.NOT_FOUND, "帖子不存在")
    if p.liked:
        p.liked = False
        p.likes = max(0, int(p.likes or 0) - 1)
        db.commit()
    return ok({"id": p.id, "liked": bool(p.liked), "likes": int(p.likes or 0)})


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


@router.post("/{post_id}/report", summary="举报帖子")
def report_post(post_id: str, body: dict, user: CurrentUser, db: DbSession) -> dict:
    p = db.get(Post, post_id)
    if p is None:
        raise AppError(ErrorCode.NOT_FOUND, "帖子不存在")
    return ok({"id": post_id, "reported": True})
