"""慢请求告警中间件。

超过阈值的请求打 WARNING 并记录额外的慢字段，便于定位 AI 链路的性能瓶颈。
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger, log_extra

logger = get_logger(__name__)

SLOW_THRESHOLD_MS = 1000.0


class SlowRequestMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, threshold_ms: float = SLOW_THRESHOLD_MS) -> None:
        super().__init__(app)
        self.threshold_ms = threshold_ms

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        raw = response.headers.get("X-Response-Time", "")
        try:
            elapsed = float(raw.removesuffix("ms"))
        except ValueError:
            return response

        if elapsed >= self.threshold_ms:
            logger.warning(
                "慢请求 %s %s 耗时 %.1fms",
                request.method,
                request.url.path,
                elapsed,
                extra=log_extra(elapsed_ms=round(elapsed, 1), path=request.url.path),
            )
        return response
