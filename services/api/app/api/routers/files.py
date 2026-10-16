"""文件上传路由：通用上传入口（头像 / 帖子图 / 识别图 / 问诊图 / 聊天图）。

对应 fileApi.upload → POST /files。
本地演示：保存到 services/api/uploads/{date}/，并挂载 /uploads 静态目录返回可访问 URL。
production 应替换为对象存储直传签名 + CDN。
"""

from __future__ import annotations

import datetime
import mimetypes
import os

from fastapi import APIRouter, File, Form, UploadFile

from app.core.deps import CurrentUser
from app.core.envelope import ok
from app.core.errors import AppError, ErrorCode
from app.core.storage import save_upload

router = APIRouter(prefix="/files", tags=["files"])

_ALLOWED = {
    "avatar": {"image/jpeg", "image/png", "image/webp"},
    "post": {"image/jpeg", "image/png", "image/webp", "image/gif"},
    "chat": {"image/jpeg", "image/png", "image/webp", "image/gif"},
    "recognition": {"image/jpeg", "image/png", "image/webp"},
    "consult": {"image/jpeg", "image/png", "image/webp"},
}


@router.post("", summary="上传文件（返回可访问 URL）")
async def upload_file(
    user: CurrentUser,
    file: UploadFile = File(...),
    scene: str = Form(default="post"),
) -> dict:
    allowed = _ALLOWED.get(scene, _ALLOWED["post"])
    mime = file.content_type or mimetypes.guess_type(file.filename or "")[0] or ""
    if mime not in allowed:
        raise AppError(ErrorCode.BAD_REQUEST, f"scene={scene} 不允许的文件类型 {mime}")

    rel, size = save_upload(file)
    sub = datetime.date.today().isoformat()
    fname = os.path.basename(rel)
    url = f"/uploads/{sub}/{fname}"
    return ok(
        {
            "url": url,
            "key": rel,
            "size": size,
            "mimeType": mime,
            "width": None,
            "height": None,
        }
    )
