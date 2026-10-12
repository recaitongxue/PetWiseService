"""调用 services/agent 的客户端（唯一出口）。

问诊有两类调用形态，都必须在这里收口：
- request_triage()  一次性返回结构化分诊结果
- stream_triage()   SSE 流式，逐帧 yield 给业务层再转发给客户端

注意：传给 agent 的上下文只能是 services/api 显式挑选过的字段，
绝不透传原始 Token —— 权限判定始终发生在这一侧。
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.clients.base import InternalClient
from app.core.config import settings
from app.core.errors import AppError, ErrorCode
from app.core.logging import get_logger, log_extra

logger = get_logger(__name__)

_TRIAGE_PATH = "/internal/v1/triage"
_STREAM_PATH = "/internal/v1/triage/stream"
_REPORT_STREAM_PATH = "/internal/v1/report/stream"
_HEALTH_PATH = "/health"


class AgentClient(InternalClient):
    service_name = "agent"

    def __init__(self) -> None:
        super().__init__(
            settings.AGENT_BASE_URL,
            timeout=settings.AGENT_TIMEOUT,
            token=settings.INTERNAL_TOKEN,
            retries=0,  # LLM 调用不适合自动重试：可能烧双倍 Token
        )

    async def ping(self) -> bool:
        try:
            status, _ = await self.get_json(_HEALTH_PATH)
            return status == 200
        except Exception:  # noqa: BLE001
            return False

    # ── 一次��返回 ────────────────────────────────────────────
    async def request_triage(self, payload: dict[str, Any]) -> dict[str, Any]:
        """一次性分诊。额度不足时下游返回 41001，这里转成契约错误码。"""
        status, body = await self.post_json(_TRIAGE_PATH, json_body=payload)
        data = (body or {}).get("data")

        if status == 429:
            raise AppError.ai_quota_exhausted()
        if status != 200 or data is None:
            logger.warning(
                "agent 分诊失败 status=%s",
                status,
                extra=log_extra(status=status, body=body),
            )
            raise AppError.downstream_unavailable(self.service_name)
        return data

    # ── SSE 流式 ─────────────────────────────────────────────
    async def stream_triage(self, payload: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        """流式分诊，逐帧 yield 解析后的 JSON。

        异常只在这一层处理：网络层错误转 60001/60002，
        由上层决定是否给用户一个「稍后重试」的兜底帧。
        """
        try:
            async with self._client.stream(
                "POST",
                _STREAM_PATH,
                json=payload,
                headers=self._headers({"Accept": "text/event-stream"}),
                timeout=httpx.Timeout(settings.AGENT_STREAM_TIMEOUT),
            ) as response:
                if response.status_code == 429:
                    raise AppError.ai_quota_exhausted()
                if response.status_code != 200:
                    raise AppError.downstream_unavailable(self.service_name)

                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if not raw:
                        continue
                    try:
                        frame = json.loads(raw)
                    except json.JSONDecodeError:
                        logger.warning("丢弃非法 SSE 帧: %s", raw[:80])
                        continue
                    yield frame
        except httpx.HTTPError as exc:
            raise self._translate(exc) from exc

    async def report_sse(self, payload: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        """报告生成走同一套流式机制，路径不同但契约一致。"""
        async for frame in self._stream(_REPORT_STREAM_PATH, payload):
            yield frame

    async def _stream(self, path: str, payload: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        try:
            async with self._client.stream(
                "POST",
                path,
                json=payload,
                headers=self._headers({"Accept": "text/event-stream"}),
                timeout=httpx.Timeout(settings.AGENT_STREAM_TIMEOUT),
            ) as response:
                if response.status_code != 200:
                    self._raise_for_status(response)
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        raw = line[5:].strip()
                        if raw:
                            yield json.loads(raw)
        except httpx.HTTPError as exc:
            raise self._translate(exc) from exc
