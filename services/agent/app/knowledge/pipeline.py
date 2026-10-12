"""灌库流水线。

把目录里的语料 → 切分 → 向量化 → 落库，一次性完成。

两个设计要点：
1. **幂等**：文档 id 相同则整篇替换（先删 chunks 再插），重复执行不会产生脏数据；
2. **可观测**：返回每篇文档产生了多少片段，便于判断切分粒度是否合理。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.knowledge import db as db_utils
from app.knowledge.chunkers import chunk_text
from app.knowledge.embeddings import EmbeddingProvider, get_embedding_provider
from app.knowledge.loaders import CorpusDoc, load_corpus
from app.knowledge.models import KBDocument
from app.knowledge.vectorstore import KnowledgeStore


@dataclass
class IngestReport:
    """灌库结果摘要，CLI 与 HTTP 接口共用。"""

    documents: int = 0
    chunks: int = 0
    skipped: int = 0
    elapsed_ms: float = 0.0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "documents": self.documents,
            "chunks": self.chunks,
            "skipped": self.skipped,
            "elapsedMs": round(self.elapsed_ms, 1),
            "errors": self.errors,
        }


class KnowledgePipeline:
    """加载 → 切分 → 向量化 → 写入。"""

    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
        store: KnowledgeStore | None = None,
    ) -> None:
        self.provider = provider or get_embedding_provider()
        self.store = store or KnowledgeStore()

    # ── 单篇 ─────────────────────────────────────────────────
    def ingest_document(self, session: Session, doc: CorpusDoc) -> int:
        if not doc.content.strip():
            return 0

        pieces = chunk_text(doc.content)
        vectors = self.provider.embed_documents([piece.embed_text for piece in pieces])

        if vectors and len(vectors[0]) != self.store.dim:
            raise ValueError(
                f"向量维度 {len(vectors[0])} 与表结构 {self.store.dim} 不一致，"
                "请调整 EMBEDDING_DIM 后重建知识库"
            )

        orm_doc = KBDocument(
            id=doc.doc_id,
            source_type=doc.source_type,
            title=doc.title,
            species=doc.species,
            tags=doc.tags,
            source_uri=doc.source_uri,
            version=doc.version,
        )
        payloads = [
            {
                "index": piece.index,
                "heading": piece.heading,
                "content": piece.content,
                "token_count": piece.token_count,
                "meta": {"sourceUri": doc.source_uri},
            }
            for piece in pieces
        ]
        return self.store.upsert_document(session, orm_doc, payloads, vectors)

    # ── 批量 ─────────────────────────────────────────────────
    def ingest_dir(
        self,
        corpus_dir: Path | None = None,
        *,
        rebuild: bool = False,
    ) -> IngestReport:
        """灌入整个语料目录。"""
        root = corpus_dir or settings.KB_CORPUS_DIR
        report = IngestReport()
        started = time.perf_counter()

        try:
            docs = load_corpus(root)
        except FileNotFoundError as exc:
            report.errors.append(str(exc))
            report.elapsed_ms = (time.perf_counter() - started) * 1000
            return report

        with db_utils.session_scope() as session:
            if rebuild:
                removed_docs, removed_chunks = self.store.clear(session)
                report.errors.insert(
                    0, f"rebuild: 清理了 {removed_docs} 篇文档 / {removed_chunks} 段"
                )

            for doc in docs:
                try:
                    count = self.ingest_document(session, doc)
                except Exception as exc:  # noqa: BLE001 - 单篇失败不应中断整批
                    report.errors.append(f"{doc.doc_id}: {exc}")
                    report.skipped += 1
                    continue
                report.documents += 1
                report.chunks += count

        report.elapsed_ms = (time.perf_counter() - started) * 1000
        return report


def ensure_schema() -> list[str]:
    """对外暴露的建表入口（CLI init-db 用）。"""
    return db_utils.init_db()
