"""重排序。

检索出候选后做一次精排，显著提升"排在第一位的段落是否真的相关"。
两档实现：
- cross-encoder（sentence-transformers 加载 reranker 模型，效果最好）
- 启发式（零依赖，给标题命中、短语命中、来源类型加权）

启发式不是凑数：在知识库规模只有几百段时，它已经能覆盖大部分排序收益，
同时让整个链路在无 GPU 环境里依然可跑。
"""

from __future__ import annotations

import re
from typing import Protocol

from app.config import settings


class RetrievedChunk:
    """检索结果的统一载体。"""

    def __init__(
        self,
        chunk_id: str,
        doc_id: str,
        title: str,
        heading: str,
        content: str,
        score: float,
        source_type: str = "",
        species: str = "all",
    ) -> None:
        self.chunk_id = chunk_id
        self.doc_id = doc_id
        self.title = title
        self.heading = heading
        self.content = content
        self.score = score
        self.source_type = source_type
        self.species = species

    @property
    def citation(self) -> str:
        return f"《{self.title}》· {self.heading}" if self.heading else f"《{self.title}》"

    def as_context(self, limit: int = 400) -> str:
        """放进 LLM 上下文里的文本，带来源标注以便模型引用。"""
        body = self.content if len(self.content) <= limit else self.content[:limit] + "…"
        return f"[{self.citation}]\n{body}"

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Retrieved {self.chunk_id} score={self.score:.3f}>"


class Reranker(Protocol):
    def rerank(self, query: str, items: list[RetrievedChunk]) -> list[RetrievedChunk]: ...


class HeuristicReranker:
    """零依赖重排：在最可能被忽略的几个信号上加权。"""

    name = "heuristic"

    # 来源类型的先验权重：同一提问下，急救与症状类通常比品种科普更紧急
    SOURCE_BONUS: dict[str, float] = {
        "first_aid": 0.06,
        "disease": 0.05,
        "faq": 0.03,
        "care": 0.02,
        "breed": 0.0,
    }

    @staticmethod
    def _terms(query: str) -> list[str]:
        words = re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]", query.lower())
        return list({w for w in words if len(w) > 0})

    def rerank(self, query: str, items: list[RetrievedChunk]) -> list[RetrievedChunk]:
        terms = self._terms(query)
        query_headings = set(re.findall(r"[\u4e00-\u9fff]{2,6}", query))

        for item in items:
            bonus = 0.0
            # 标题（含小节标题）命中：说明这段讲的就是这个问题
            haystack_title = f"{item.title}{item.heading}"
            if any(t in haystack_title for t in terms):
                bonus += 0.15
            # 连续短语命中比单字散落更强
            if query.strip() and query.strip() in item.content:
                bonus += 0.10
            # 覆盖度：命中词元种类越多越相关
            coverage = sum(1 for t in terms if t in item.content) / max(1, len(terms))
            bonus += 0.08 * coverage
            # 过度冗长的段落稀释主题，轻微惩罚
            if len(item.content) > 600:
                bonus -= 0.03
            bonus += self.SOURCE_BONUS.get(item.source_type, 0.0)
            _ = query_headings

            item.score = round(item.score + bonus, 4)

        return sorted(items, key=lambda x: x.score, reverse=True)


class CrossEncoderReranker:
    """bge-reranker 系列模型，需 sentence-transformers 支持。"""

    name = "cross-encoder"
    _cache: object | None = None

    def __init__(self, model: str = "BAAI/bge-reranker-base") -> None:
        self.model_name = model
        self._load()

    def _load(self) -> None:
        if CrossEncoderReranker._cache is None:
            from sentence_transformers import CrossEncoder

            CrossEncoderReranker._cache = CrossEncoder(self.model_name)
        self._model = CrossEncoderReranker._cache

    def rerank(self, query: str, items: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if not items:
            return items
        pairs = [[query, item.content] for item in items]
        scores = self._model.predict(pairs)  # type: ignore[attr-defined]
        for item, score in zip(items, scores, strict=True):
            item.score = round(float(score), 4)
        return sorted(items, key=lambda x: x.score, reverse=True)


def get_reranker(strategy: str | None = None) -> Reranker:
    """工厂：默认启发式，显式要求 cross-encoder 时才加载模型。"""
    if (strategy or settings.RERANK_STRATEGY) == "cross-encoder":
        try:
            return CrossEncoderReranker()
        except Exception:  # noqa: BLE001 - 模型不可用时静默降级
            pass
    return HeuristicReranker()
