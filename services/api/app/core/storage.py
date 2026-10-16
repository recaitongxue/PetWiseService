"""本地文件存储：上传落盘 + 可访问 URL（演示环境）。

production 应替换为对象存储直传签名 + CDN，接口形状保持一致即可。
"""

from __future__ import annotations

import datetime
import os
import time

from fastapi import UploadFile

# services/api/app/uploads/{yyyy-mm-dd}/{ts}{ext}
_UPLOAD_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
)


def save_upload(file: UploadFile) -> tuple[str, int]:
    """保存上传文件，返回 (相对路径, 字节数)。相对路径可直接拼 /uploads 前缀访问。"""
    os.makedirs(_UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "img.jpg")[1] or ".jpg"
    sub = datetime.date.today().isoformat()
    abs_dir = os.path.join(_UPLOAD_DIR, sub)
    os.makedirs(abs_dir, exist_ok=True)
    fname = f"{int(time.time() * 1000)}{ext}"
    abs_path = os.path.join(abs_dir, fname)
    data = file.file.read()
    with open(abs_path, "wb") as f:
        f.write(data)
    return f"uploads/{sub}/{fname}", len(data)
