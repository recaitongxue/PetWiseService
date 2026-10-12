"""图像预处理。

只负责把任意来源的图片字节 → 模型要求的 NCHW 张量。
不做任何业务判断（那是 postprocess 的事）。
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageOps

from app.config import settings


class ImageTooLargeError(ValueError):
    pass


class InvalidImageError(ValueError):
    pass


def load_image(image_bytes: bytes) -> Image.Image:
    """解码并纠正 EXIF 方向。

    手机直出照片几乎都带 EXIF 方向，不纠正会导致模型看到躺着的猫。
    """
    if len(image_bytes) > settings.max_image_bytes:
        raise ImageTooLargeError(f"图片超过 {settings.MAX_IMAGE_MB}MB")

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except Exception as exc:  # noqa: BLE001 - PIL 的异常类型过于分散
        raise InvalidImageError("无法解析图片") from exc

    return ImageOps.exif_transpose(image).convert("RGB")


def to_tensor(
    image: Image.Image,
    *,
    image_size: int,
    mean: tuple[float, float, float],
    std: tuple[float, float, float],
) -> np.ndarray:
    """缩放 → 归一化 → NCHW float32。

    与训练侧 transforms 必须保持一致，否则精度会无声下降。
    """
    resized = ImageOps.fit(image, (image_size, image_size), Image.Resampling.BICUBIC)
    array = np.asarray(resized, dtype=np.float32) / 255.0

    mean_arr = np.asarray(mean, dtype=np.float32)
    std_arr = np.asarray(std, dtype=np.float32)
    normalized = (array - mean_arr) / std_arr

    # HWC -> CHW -> NCHW
    return np.expand_dims(np.transpose(normalized, (2, 0, 1)), axis=0)
