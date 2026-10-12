"""知识向量的读写层。

检索策略：**向量粗召回 → Python 侧混合打分**。

为什么不在 SQL 里做完整混合检索：
1. Postgres 的 to_tsvector 对中文分词几乎没有效果，必须用外部词元做匹配；
2. 混合权重在调试期需要频繁调整，放在 Python 侧可以热改、可单测；
3. 粗召回量本身有限（默认 30 条），Python 侧重排开销可以忽略。

向量相似度用 pgvector 的 <=> （余弦距离），相似度 = 1 - 距离。
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, func, select, text

from app.config import settings
from app.knowledge.models import KBChunk, KBDocument


class KnowledgeStore:
    """封装所有对 kb_* 表的 IO。"""

    def __init__(self, dim: int | None = None) -> None:
        self.dim = dim or settings.EMBEDDING_DIM

    # ── 写入 ─────────────────────────────────────────────────
    def upsert_document(
        self,
        session: Any,
        doc: KBDocument,
        chunks: list[dict[str, Any]],
        vectors: list[list[float]],
    ) -> int:
        """幂等写入：同 id 文档先删后插，保证重复灌库不会膨胀。

        返回写入的分块数。
        """
        self.delete_document(session, doc.id)
        session.add(doc)
        session.flush()

        for payload, vector in zip(chunks, vectors, strict=True):
            session.add(
                KBChunk(
                    id=f"{doc.id}#{payload['index']}",
                    document_id=doc.id,
                    chunk_index=payload["index"],
                    heading=payload["heading"],
                    content=payload["content"],
                    token_count=payload["token_count"],
                    meta=payload.get("meta", {}),
                    embedding=vector,
                )
            )
        session.flush()
        return len(vectors)

    def delete_document(self, session: Any, doc_id: str) -> int:
        session.execute(delete(KBChunk).where(KBChunk.document_id == doc_id))
        result = session.execute(delete(KBDocument).where(KBDocument.id == doc_id))
        session.flush()
        return result.rowcount or 0

    def clear(self, session: Any) -> tuple[int, int]:
        """清空知识库，返回 (文档数, 分块数)。"""
        stats = self.stats(session)
        session.execute(delete(KBChunk))
        session.execute(delete(KBDocument))
        session.flush()
        return stats["documents"], stats["chunks"]

    # ── 检索 ─────────────────────────────────────────────────
    def vector_candidates(
        self,
        session: Any,
        query_vector: list[float],
        *,
        limit: int | None = None,
        source_types: list[str] | None = None,
        species: str | None = None,
    ) -> list[tuple[KBChunk, float]]:
        """向量粗召回，返回 [(chunk, cosine_similarity)]。"""
        limit = limit or settings.RETRIEVAL_CANDIDATES

        # <=> 是余弦距离，相似度取 1 - distance
        similarity = (1 - KBChunk.embedding.cosine_distance(query_vector)).label("similarity")
        stmt = select(KBChunk, similarity).join(KBDocument, KBDocument.id == KBChunk.document_id)

        if source_types:
            stmt = stmt.where(KBDocument.source_type.in_(source_types))
        if species and species != "all":
            stmt = stmt.where(KBDocument.species.in_([species, "all"]))

        stmt = stmt.order_by(similarity.desc()).limit(limit)

        rows = session.execute(stmt).all()
        return [(row[0], float(row[1])) for row in rows]

    def keyword_recall(
        self,
        session: Any,
        terms: list[str],
        *,
        limit: int = 20,
    ) -> dict[str, int]:
        """纯关键词召回：用于向量结果不理想时的补充通道。

        返回 {chunk_id: 命中词元数}。
        """
        if not terms:
            return {}

        fragments = [KBChunk.content.ilike(f"%{t}%") for t in terms]
        stmt = select(KBChunk.id, KBChunk.content).limit(limit * 4)
        rows = session.execute(stmt).all()

        hits: dict[str, int] = {}
        for chunk_id, content in rows:
            score = sum(1 for t in terms if t in content)
            if score:
                hits[chunk_id] = score
        return dict(sorted(hits.items(), key=lambda kv: kv[1], reverse=True)[:limit])

    # ── 统计 ─────────────────────────────────────────────────
    def stats(self, session: Any) -> dict[str, int]:
        documents = session.scalar(select(func.count()).select_from(KBDocument)) or 0
        chunks = session.scalar(select(func.count()).select_from(KBChunk)) or 0
        return {"documents": documents, "chunks": chunks}

    def source_breakdown(self, session: Any) -> dict[str, int]:
        rows = session.execute(
            select(KBDocument.source_type, func.count()).group_by(KBDocument.source_type)
        ).all()
        return {row[0]: int(row[1]) for row in rows}

    def health(self, session: Any) -> bool:
        try:
            session.execute(text("SELECT 1"))
            return True
        except Exception:  # noqa: BLE001
            return False


def new_document_id(prefix: str = "doc") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"
