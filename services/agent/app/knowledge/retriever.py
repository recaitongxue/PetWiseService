"""知识检索入口。

对外只有 ``KnowledgeRetriever.retrieve()`` 一个方法，内部串起：
查询向量化 → 向量粗召回 → 关键词补充 → 混合打分 → 重排 → 阈值过滤 → 同文档去重。

这样做的收益：所有"为什么召回不好"的排查都集中在这一个文件里。
"""

from __future__ import annotations

import re
from typing import Any

from app.config import settings
from app.knowledge.embeddings import EmbeddingProvider, get_embedding_provider
from app.knowledge.rerank import RetrievedChunk, get_reranker
from app.knowledge.vectorstore import KnowledgeStore


class KnowledgeRetriever:
    """把"提问"翻译成"最相关的若干知识片段"。"""

    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
        store: KnowledgeStore | None = None,
    ) -> None:
        self.provider = provider or get_embedding_provider()
        self.store = store or KnowledgeStore()
        self.reranker = get_reranker()

    # ── 词元切分（与 HashingProvider 保持一致） ────────────────
    @staticmethod
    def _terms(query: str) -> list[str]:
        words = re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]", query.lower())
        bigrams = [f"{words[i]}{words[i + 1]}" for i in range(len(words) - 1)]
        # 单字噪声太大，关键词通道只用长度 ≥2 的词元
        return [t for t in dict.fromkeys(words + bigrams) if len(t) >= 2][:24]

    # ── 主流程 ───────────────────────────────────────────────
    def retrieve(
        self,
        session: Any,
        query: str,
        *,
        top_k: int | None = None,
        source_types: list[str] | None = None,
        species: str | None = None,
        threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        """检索知识片段。

        :param threshold: 低于该混合分数的片段会被丢弃，宁缺毋滥——
                          喂给 LLM 的噪声片段会直接变成幻觉来源。
        """
        top_k = top_k or settings.RETRIEVAL_TOP_K
        threshold = settings.SIMILARITY_THRESHOLD if threshold is None else threshold

        query_vector = self.provider.embed_query(query)
        candidates = self.store.vector_candidates(
            session,
            query_vector,
            limit=max(settings.RETRIEVAL_CANDIDATES, top_k * 4),
            source_types=source_types,
            species=species,
        )
        if not candidates:
            return []

        keyword_hits = self.store.keyword_recall(session, self._terms(query))

        scored: list[RetrievedChunk] = []
        for chunk, similarity in candidates:
            document = chunk.document
            keyword_score = keyword_hits.get(chunk.id, 0)
            keyword_norm = min(1.0, keyword_score / max(1, len(self._terms(query)))) * similarity
            mixed = settings.VECTOR_WEIGHT * similarity + settings.KEYWORD_WEIGHT * keyword_norm
            scored.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    doc_id=chunk.document_id,
                    title=document.title if document else chunk.document_id,
                    heading=chunk.heading,
                    content=chunk.content,
                    score=round(mixed, 4),
                    source_type=document.source_type if document else "",
                    species=document.species if document else "all",
                )
            )

        reranked = self.reranker.rerank(query, scored)
        filtered = [item for item in reranked if item.score >= threshold]
        return self._diversify(filtered, top_k)

    @staticmethod
    def _diversify(items: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
        """同一文档限量，防止上下文被一篇长文档占满。"""
        per_doc: dict[str, int] = {}
        result: list[RetrievedChunk] = []
        for item in items:
            used = per_doc.get(item.doc_id, 0)
            if used >= settings.MAX_CHUNKS_PER_DOC:
                continue
            per_doc[item.doc_id] = used + 1
            result.append(item)
            if len(result) >= top_k:
                break
        return result


def build_context(items: list[RetrievedChunk], *, limit_per_chunk: int = 400) -> str:
    """把检索结果拼成可直接塞进提示词的上下文块。

    每段都带来源标注，模型才能给出可追溯的引用。
    """
    if not items:
        return "（知识库中没有与该问题相关的条目）"
    return "\n\n".join(item.as_context(limit_per_chunk) for item in items)
