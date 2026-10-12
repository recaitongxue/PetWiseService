"""Embedding 抽象层。

统一接口 + 三种实现，切换只改环境变量：
- ``hash``   零依赖本地兜底，用于跑通链路与单元测试（**禁止用于效果评测**）
- ``local``  sentence-transformers 加载本地中文模型（推荐，离线可用）
- ``openai`` 任意 OpenAI 兼容的 /embeddings 端点

这样设计的理由：换 embedding 模型会导致向量空间整体失效，
必须重建索引；把提供者收口在一处，才能让 pipeline 明确地提醒"需要重建"。
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

from app.config import settings


class EmbeddingProvider(Protocol):
    """向量化协议的鸭子类型定义。"""

    name: str
    model: str
    dim: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class BaseProvider:
    """共享的属性占位，子类覆盖 dim。"""

    name = "base"
    model = "base"
    dim = settings.EMBEDDING_DIM

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


# ── 零依赖兜底实现 ───────────────────────────────────────────
class HashingProvider(BaseProvider):
    """基于词元哈希的确定性向量。

    同类词的哈希不会真的相近，因此**只有same词元才有相似度**，
    它的价值在于：无需下载模型即可验证灌库→检索→召回的完整链路。
    """

    name = "hash"

    def __init__(self, dim: int | None = None) -> None:
        self.dim = dim or settings.EMBEDDING_DIM
        self.model = f"hashing-{self.dim}"

    @staticmethod
    def _tokens(text: str) -> list[str]:
        lowered = text.lower()
        # 中文按单字与二字词切分，英文按单词，形成粗糙但有覆盖度的词元
        words = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", lowered)
        bigrams = [
            f"{words[i]}{words[i + 1]}"
            for i in range(len(words) - 1)
            if words[i][-1:] not in "0123456789"
        ]
        return words + bigrams

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        tokens = self._tokens(text)
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self.dim
            sign = 1.0 if digest[4] & 1 else -1.0
            weight = 1.0 + math.log(1 + digest[5] / 255)
            vector[index] += sign * weight

        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]


# ── 本地模型实现 ─────────────────────────────────────────────
class LocalProvider(BaseProvider):
    """sentence-transformers 本地推理。

    首次调用会下载/加载模型（约数百 MB），因此用类级缓存避免重复加载。
    """

    name = "local"
    _model_cache: object | None = None

    def __init__(self, model: str | None = None, dim: int | None = None) -> None:
        self.model = model or settings.EMBEDDING_MODEL
        self.dim = dim or settings.EMBEDDING_DIM
        self._load()

    def _load(self) -> None:
        if LocalProvider._model_cache is None:
            from sentence_transformers import SentenceTransformer  # 惰性导入

            LocalProvider._model_cache = SentenceTransformer(self.model)
        self._model = LocalProvider._model_cache

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(  # type: ignore[attr-defined]
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        return [list(map(float, v)) for v in vectors]


# ── 远程接口实现 ─────────────────────────────────────────────
class OpenAICompatibleProvider(BaseProvider):
    """OpenAI 兼容的 /embeddings 端点（含各类国产模型网关）。"""

    name = "openai"

    def __init__(
        self,
        *,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        dim: int | None = None,
    ) -> None:
        self.model = model or settings.EMBEDDING_MODEL
        self.base_url = (base_url or settings.EMBEDDING_BASE_URL).rstrip("/")
        self.api_key = api_key or settings.EMBEDDING_API_KEY
        self.dim = dim or settings.EMBEDDING_DIM

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        import httpx  # 惰性导入

        response = httpx.post(
            f"{self.base_url}/embeddings",
            json={"model": self.model, "input": texts},
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60.0,
        )
        response.raise_for_status()
        payload = response.json()
        # OpenAI 返回顺序与输入一致，按 index 回填更稳妥
        items = sorted(payload["data"], key=lambda x: x["index"])
        vectors = [item["embedding"] for item in items]

        if vectors and len(vectors[0]) != self.dim:
            raise ValueError(
                f"embedding 维度不匹配：模型返回 {len(vectors[0])}，配置 EMBEDDING_DIM={self.dim}"
            )
        return vectors


_PROVIDERS: dict[str, type[BaseProvider]] = {
    "hash": HashingProvider,
    "local": LocalProvider,
    "openai": OpenAICompatibleProvider,
}


def get_embedding_provider(name: str | None = None) -> EmbeddingProvider:
    """工厂方法。provider 名非法时抛出可读错误。"""
    key = (name or settings.EMBEDDING_PROVIDER).lower()
    if key not in _PROVIDERS:
        raise ValueError(f"未知的 embedding provider: {key}，可选 {list(_PROVIDERS)}")

    if key == "local":
        return LocalProvider()
    if key == "openai":
        return OpenAICompatibleProvider()
    return HashingProvider()
