"""会话短期记忆。

Redis 优先，不可用时退回进程内 LRU 字典。
为什么需要它：多轮追问时（"那它还能吃 XX 吗"），
没有上下文就无法判断这句话指的是谁、指哪个症状。
"""

from __future__ import annotations

import json
import time
from collections import OrderedDict
from typing import Any

from app.config import settings

_MAX_TURNS = 6
_TTL_SECONDS = 30 * 60


class InMemoryMemory:
    """零依赖兜底实现：进程内 LRU + TTL。

    注意：多副本部署时它不共享状态，仅适用于本地开发与演示。
    """

    name = "memory"

    def __init__(self, capacity: int = 1000) -> None:
        self._store: OrderedDict[str, tuple[float, list[dict[str, Any]]]] = OrderedDict()
        self.capacity = capacity

    def _evict(self) -> None:
        now = time.time()
        expired = [k for k, (ts, _) in self._store.items() if now - ts > _TTL_SECONDS]
        for key in expired:
            self._store.pop(key, None)
        while len(self._store) > self.capacity:
            self._store.popitem(last=False)

    def append_turn(self, session_id: str, turn: dict[str, Any]) -> None:
        _, turns = self._store.get(session_id, (time.time(), []))
        turns = (turns + [turn])[-_MAX_TURNS:]
        self._store[session_id] = (time.time(), turns)
        self._store.move_to_end(session_id)
        self._evict()

    def get_turns(self, session_id: str) -> list[dict[str, Any]]:
        ts, turns = self._store.get(session_id, (0.0, []))
        if time.time() - ts > _TTL_SECONDS:
            self._store.pop(session_id, None)
            return []
        return turns

    def clear(self, session_id: str) -> None:
        self._store.pop(session_id, None)


class RedisMemory:
    """Redis 实现：多副本共享，生产环境使用。"""

    name = "redis"

    def __init__(self) -> None:
        import redis  # 惰性导入

        self._client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    def _key(self, session_id: str) -> str:
        return f"petwise:agent:memory:{session_id}"

    def append_turn(self, session_id: str, turn: dict[str, Any]) -> None:
        key = self._key(session_id)
        pipeline = self._client.pipeline()
        pipeline.rpush(key, json.dumps(turn, ensure_ascii=False))
        pipeline.ltrim(key, -_MAX_TURNS, -1)
        pipeline.expire(key, _TTL_SECONDS)
        pipeline.execute()

    def get_turns(self, session_id: str) -> list[dict[str, Any]]:
        raw = self._client.lrange(self._key(session_id), 0, -1)
        turns: list[dict[str, Any]] = []
        for item in raw:
            try:
                turns.append(json.loads(item))
            except json.JSONDecodeError:
                continue
        return turns

    def clear(self, session_id: str) -> None:
        self._client.delete(self._key(session_id))


def get_memory():
    """优先 Redis，失败则降级到内存实现。"""
    try:
        memory = RedisMemory()
        # 主动探活：连不上就立刻降级，不要等到请求时才发现
        if not memory._client.ping():  # noqa: SLF001
            raise RuntimeError("redis ping failed")
        return memory
    except Exception:  # noqa: BLE001
        return InMemoryMemory()
