"""调用 services/vision 的客户端（唯一出口）。

识别是**可降级**的能力：超时或不可用时上层应返回低置信度兜底，而不是报错。
因此这里同时提供 recognize() 与 try_recognize()。
"""

from __future__ import annotations

from typing import Any

import httpx

from app.clients.base import InternalClient
from app.core.config import settings
from app.core.logging import get_logger, log_extra

logger = get_logger(__name__)

_RECOGNIZE_PATH = "/internal/v1/recognize"
_HEALTH_PATH = "/health"


class VisionClient(InternalClient):
    service_name = "vision"

    def __init__(self) -> None:
        super().__init__(
            settings.VISION_BASE_URL,
            timeout=settings.VISION_TIMEOUT,
            token=settings.INTERNAL_TOKEN,
            retries=1,  # 一次性抖动值得重试一次；仍失败就降级
        )

    async def ping(self) -> bool:
        """健康检查，用于 /health/ready，失败不抛异常。"""
        try:
            status, _ = await self.get_json(_HEALTH_PATH)
            return status == 200
        except Exception:  # noqa: BLE001 - 健康检查必须不抛
            return False

    async def recognize(
        self,
        *,
        image_bytes: bytes,
        filename: str,
        kind: str = "auto",
        top_k: int = 3,
    ) -> dict[str, Any]:
        """同步识别。

        返回 vision 的 data 结构（RecognitionResult），非 200 抛 AppError。
        """
        # multipart 不走 request() 的 JSON 通道，直接复用底层 client
        files = {"image": (filename, image_bytes, "image/jpeg")}
        try:
            response = await self._client.post(
                _RECOGNIZE_PATH,
                files=files,
                data={"kind": kind, "topK": top_k},
                headers=self._headers(),
            )
        except Exception as exc:
            raise self._translate(exc) from exc

        if response.status_code != 200:
            self._raise_for_status(response)

        payload = self._safe_json(response) or {}
        logger.info(
            "识别完成 top=%.3f",
            (payload.get("data") or {}).get("confidence", 0),
            extra=log_extra(kind=kind, top_k=top_k),
        )
        return payload.get("data") or {}

    async def try_recognize(self, **kwargs: Any) -> dict[str, Any] | None:
        """降级版：任何失败都返回 None，由上层兜底。"""
        try:
            return await self.recognize(**kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.warning("识别降级：%s", exc, extra=log_extra(reason=type(exc).__name__))
            return None
