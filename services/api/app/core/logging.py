"""结构化日志与 traceId 上下文。

traceId 由 TraceIdMiddleware 在请求入口注入 ContextVar，
业务代码与 envelope 均从这里取值，保证日志、响应、下游调用三者可串联。
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="-")
user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="-")

# 契约里 PDElate traceId 形如 req_8f3a1b2c
_TRACE_PREFIX = "req_"


def new_trace_id() -> str:
    """生成新的链路 ID，格式与契约示例一致。"""
    return f"{_TRACE_PREFIX}{uuid.uuid4().hex[:12]}"


class _ContextFilter(logging.Filter):
    """把 traceId / userId 注入每条日志记录。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = trace_id_var.get()
        record.user_id = user_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """单行 JSON 日志，便于容器采集。

    注意：这里刻意不记录任何请求体原文，避免敏感信息落盘（契约 1.6.5）。
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "traceId": getattr(record, "trace_id", "-"),
            "userId": getattr(record, "user_id", "-"),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """本地开发用的可读格式。"""

    def format(self, record: logging.LogRecord) -> str:
        base = f"{record.levelname:<7} [{getattr(record, 'trace_id', '-')}] {record.getMessage()}"
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


def setup_logging(level: str = "INFO", json_format: bool = False) -> None:
    """初始化根 logger，重复调用安全。"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if json_format else TextFormatter())
    handler.addFilter(_ContextFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # 降低第三方库噪音
    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_extra(**fields: Any) -> dict[str, Any]:
    """向日志追加结构化字段：logger.info("...", extra=log_extra(kb_id=1))。"""
    return {"extra_fields": fields}
