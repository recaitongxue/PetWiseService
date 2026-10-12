"""LLM 客户端。

只做三件事：发请求、强制 JSON 输出、失败时给出可读错误。
刻意不引入 LangChain 的抽象——毕业设计里裸调用 + 显式 schema 校验更容易讲清楚，
也更方便在答辩时解释"为什么不会因为幻觉导致前端解析失败"。
"""

from __future__ import annotations

import json
import re
from typing import Any

from app.config import settings

_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class LLMError(RuntimeError):
    pass


class LLMClient:
    """OpenAI 兼容接口的极简封装。"""

    def __init__(self) -> None:
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        self.base_url = settings.LLM_BASE_URL.rstrip("/")
        self.api_key = settings.LLM_API_KEY
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.timeout = settings.LLM_TIMEOUT

    @property
    def mock_mode(self) -> bool:
        return settings.mock_mode

    # ── 原始对话 ─────────────────────────────────────────────
    async def chat(
        self,
        system: str,
        user: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """返回文本内容。mock 模式下抛出异常，由调用方走规则兜底。"""
        if self.mock_mode:
            raise LLMError("LLM 未配置（mock 模式）")

        import httpx  # 惰性导入

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        if response.status_code >= 400:
            raise LLMError(f"LLM 返回 {response.status_code}: {response.text[:200]}")

        data = response.json()
        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError) as exc:
            raise LLMError(f"LLM 响应结构异常: {data}") from exc

    # ── 流式对话 ─────────────────────────────────────────────
    async def stream_chat(self, system: str, user: str):  # -> AsyncIterator[str]
        """逐块产出文本片段（SSE 转发用）。"""
        if self.mock_mode:
            raise LLMError("LLM 未配置（mock 模式）")

        import httpx

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            ) as response:
                if response.status_code >= 400:
                    raise LLMError(f"LLM 返回 {response.status_code}")
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        chunk = json.loads(raw)
                        delta = chunk["choices"][0]["delta"].get("content")
                    except (ValueError, KeyError, IndexError):
                        continue
                    if delta:
                        yield delta

    # ── JSON 模式 ────────────────────────────────────────────
    async def chat_json(
        self,
        system: str,
        user: str,
        *,
        retries: int | None = None,
    ) -> dict[str, Any]:
        """强制 JSON 输出并校验。

        失败重试时会把上一次的错误回传给模型——实测这比单纯重试有效得多。
        """
        attempts = (settings.LLM_JSON_RETRIES if retries is None else retries) + 1
        last_error = ""

        for attempt in range(attempts):
            hint = (
                f"\n\n上一次输出不是合法 JSON：{last_error}。"
                "请严格只输出一个 JSON 对象，不要包含代码块标记与解释文字。"
                if last_error
                else ""
            )
            content = await self.chat(system, user + hint)
            try:
                return parse_json(content)
            except ValueError as exc:
                last_error = str(exc)

        raise LLMError(f"LLM 未能输出合法 JSON（重试 {attempts} 次）: {last_error}")


def parse_json(content: str) -> dict[str, Any]:
    """从可能带代码块围栏的文本里提取 JSON 对象。"""
    stripped = content.strip()
    match = _JSON_FENCE.search(stripped)
    candidate = match.group(1) if match else stripped

    # 极端情况下模型会在 JSON 前后加寒暄，截取首尾花括号
    start, end = candidate.find("{"), candidate.rfind("}")
    if start > 0 or (end != -1 and end < len(candidate) - 1):
        candidate = candidate[start : end + 1]

    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 解析失败: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("输出不是 JSON 对象")
    return data
