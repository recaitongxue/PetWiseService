"""内部服务调用基类。

设计约束（见架构文档 4.2）：
1. IO 出网只能走 clients 层，业务代码禁止裸写 httpx；
2. 超时 / 重试 / 降级 / 埋点必须在这里统一实现；
3. traceId 必须透传，否则跨服务日志无法串联。

失败一律转为契约错误码 60001 / 60002，并附带哪个下游出问题的语义，
由上层决定是否降级（识别可降级，鉴权类不可）。
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.errors import AppError, ErrorCode
from app.core.logging import get_logger, log_extra, trace_id_var

logger = get_logger(__name__)

_INTERNAL_TOKEN_HEADER = "X-Internal-Token"
_TRACE_HEADER = "X-Trace-Id"


class InternalClient:
    """内部 HTTP 客户端：统一的超时、重试、错误翻译。"""

    service_name: str = "unknown"

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float,
        token: str,
        retries: int = 0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.token = token
        self.retries = retries
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers={_INTERNAL_TOKEN_HEADER: token},
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {_TRACE_HEADER: trace_id_var.get()}
        if extra:
            headers.update(extra)
        return headers

    def _translate(self, exc: Exception) -> AppError:
        if isinstance(exc, httpx.TimeoutException):
            return AppError.downstream_timeout(self.service_name)
        if isinstance(exc, httpx.HTTPError):  # 连接失败、协议错误等
            return AppError.downstream_unavailable(self.service_name)
        raise exc  # 非 IO 异常不吞，交给全局处理器

    async def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """发送 JSON 请求。失败抛 AppError(60001/60002)。"""
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = await self._client.request(
                    method,
                    path,
                    json=json_body,
                    params=params,
                    headers=self._headers(headers),
                )
                if response.status_code >= 500 and attempt < self.retries:
                    last_error = RuntimeError(f"{response.status_code}")
                    continue
                logger.debug(
                    "%s %s -> %d",
                    method,
                    path,
                    response.status_code,
                    extra=log_extra(service=self.service_name, path=path),
                )
                return response
            except httpx.HTTPError as exc:  # noqa: PERF203 - 重试循环本就该宽
                last_error = exc
                logger.warning(
                    "%s 调用失败(第 %d 次): %s",
                    self.service_name,
                    attempt + 1,
                    exc,
                    extra=log_extra(service=self.service_name, path=path),
                )
        raise self._translate(last_error or RuntimeError("unknown downstream error"))

    async def get_json(self, path: str, **kwargs: Any) -> tuple[int, Any]:
        response = await self.request("GET", path, **kwargs)
        return response.status_code, self._safe_json(response)

    async def post_json(self, path: str, *, json_body: Any, **kwargs: Any) -> tuple[int, Any]:
        response = await self.request("POST", path, json_body=json_body, **kwargs)
        return response.status_code, self._safe_json(response)

    @staticmethod
    def _safe_json(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return None

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            # 下游已声明的语义错误（如 402 额度）应原样向上抛，
            # 由 services 层决定是否需要转成 AI_QUOTA_EXHAUSTED。
            detail = self._safe_json(response) or {}
            raise AppError(
                ErrorCode.DOWNSTREAM_UNAVAILABLE,
                str(detail.get("message") or f"{self.service_name} 返回 {response.status_code}"),
                data=detail.get("data"),
            )
