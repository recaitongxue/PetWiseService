"""文件上传路由：通用对象存储入口（头像 / 帖子图 / 识别图 / 问诊图）。

对应 fileApi.upload → POST /files。
本地演示：保存到 services/api/uploads/{date}/，并挂载 /uploads 静态目录返回可访问 URL。
production 应替换为对象存储直传签名 + CDN。
"""

from __future__ import annotations

import datetime
import mimetypes
import os
import time

from fastapi import APIRouter, File, Form, Request, UploadFile

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok
from app.core.errors import AppError, ErrorCode

router = APIRouter(prefix="/files", tags=["files"])

_UPLOAD_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
)

_ALLOWED = {
    "avatar": {"image/jpeg", "image/png", "image/webp"},
    "post": {"image/jpeg", "image/png", "image/webp", "image/gif"},
    "recognition": {"image/jpeg", "image/png", "image/webp"},
    "consult": {"image/jpeg", "image/png", "image/webp"},
}


def _uid(user: CurrentUser) -> int:
    return int(user.user_id)


@router.post("")
async def upload_file(
    user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
    scene: str = Form(default="post"),
    request: Request = None,
) -> dict:
    allowed = _ALLOWED.get(scene, _ALLOWED["post"])
    mime = file.content_type or mimetypes.guess_type(file.filename or "")[0] or ""
    if mime not in allowed:
        raise AppError(ErrorCode.BAD_REQUEST, f"scene={scene} 不允许的文件类型 {mime}")

    os.makedirs(_UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "file.bin")[1] or ".bin"
    sub = datetime.date.today().isoformat()
    abs_dir = os.path.join(_UPLOAD_DIR, sub)
    os.makedirs(abs_dir, exist_ok=True)
    fname = f"{int(time.time() * 1000)}{ext}"
    abs_path = os.path.join(abs_dir, fname)
    data = file.file.read()
    with open(abs_path, "wb") as f:
        f.write(data)

    rel = f"uploads/{sub}/{fname}"
    base = str(request.base_url).rstrip("/") if request else ""
    url = f"{base}/{rel}" if base else f"/{rel}"
    return ok(
        {
            "url": url,
            "key": rel,
            "size": len(data),
            "mimeType": mime,
            "width": None,
            "height": None,
        }
    )
