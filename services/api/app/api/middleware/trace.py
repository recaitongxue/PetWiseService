"""traceId 中间件。

- 入口生成（或沿用上游）traceId 并写入 ContextVar 与 request.state
- 响应回写 X-Trace-Id，前端报错时可直接提供给用户
- 调用下游服务时由 clients/base.py 透传，串联整条链路
"""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger, new_trace_id, trace_id_var

logger = get_logger(__name__)

TRACE_HEADER = "X-Trace-Id"


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(TRACE_HEADER)
        trace_id = incoming if (incoming and incoming.startswith("req_")) else new_trace_id()

        token = trace_id_var.set(trace_id)
        request.state.trace_id = trace_id
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            trace_id_var.reset(token)

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers[TRACE_HEADER] = trace_id
        response.headers["X-Response-Time"] = f"{elapsed_ms:.1f}ms"

        logger.info(
            "%s %s -> %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
