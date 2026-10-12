"""统一响应信封（契约 1.2）。

成功出口只有一个 ``ok()``，失败出口只有一个 ``AppError``，
两者都由 Exception handlers 转成同一结构，前端因此只需认一套解析逻辑。
"""

from __future__ import annotations

import time
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.core.logging import trace_id_var

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    """{ code, message, data, timestamp, traceId } 与契约逐字段对齐。"""

    model_config = ConfigDict(populate_by_name=True)

    code: int = Field(default=0, description="0 成功，非 0 见契约错误码表")
    message: str = Field(default="ok")
    data: Optional[T] = Field(default=None)
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    traceId: str = Field(default_factory=trace_id_var.get)


class PageMeta(BaseModel):
    """分页元信息（契约 1.3 Page 结构）。"""

    total: int = 0
    page: int = 1
    pageSize: int = 20
    hasMore: bool = False


def ok(data: Any = None, *, message: str = "ok") -> dict[str, Any]:
    """构造成功信封。

    在路由里 ``return ok(result)``；traceId 从 ContextVar 自动取（由中间件注入）。
    """
    return Envelope[Any](code=0, message=message, data=data, traceId=trace_id_var.get()).model_dump()


def paged(items: list[Any], *, total: int, page: int, page_size: int) -> dict[str, Any]:
    """带分页的成功信封，data 为 { list, ...PageMeta } 形态（契约各列表接口一致）。"""
    data = {
        "list": items,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "hasMore": page * page_size < total,
    }
    return ok(data)
