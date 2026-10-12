"""全局异常处理器：把三类异常收敛成同一个信封结构。

这是「失败只有一个出口」的落地点——业务代码只需要 raise AppError，
不需要关心它最终长什么样。
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from app.core.envelope import Envelope
from app.core.errors import AppError, ErrorCode
from app.core.logging import get_logger, log_extra, trace_id_var

logger = get_logger(__name__)


def _envelope(code: int, message: str, data=None) -> dict:
    return Envelope(code=code, message=message, data=data, traceId=trace_id_var.get()).model_dump()


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "业务异常 code=%s message=%s",
            exc.code,
            exc.message,
            extra=log_extra(biz_code=exc.code, status=exc.status),
        )
        return JSONResponse(
            status_code=exc.status,
            content=_envelope(exc.code, exc.message, exc.data),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # 转为契约 10002，details 供前端逐字段高亮
        details = [
            {"field": ".".join(str(p) for p in err["loc"][1:]) or "body", "issue": err["msg"]}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=400,
            content=_envelope(ErrorCode.VALIDATION_FAILED, "参数校验失败", {"details": details}),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        # 契约 1.6.5：message 不得回显堆栈、SQL、内网地址
        logger.exception("未捕获异常: %s", exc)
        return JSONResponse(
            status_code=500,
            content=_envelope(ErrorCode.INTERNAL_ERROR, "服务繁忙，请稍后再试"),
        )
