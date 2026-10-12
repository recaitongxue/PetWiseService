"""知识库数据模型。

两张表足够覆盖毕业设计的规模：
- kb_document：一篇文档的元数据（来源类型、物种、标签、版本）
- kb_chunk  ：被切分后的最小检索单元，携带向量

为什么分块表单独存在：
1. 向量检索的最小粒度是语义完整的段落，不是整篇文档；
2. 回答里要引用来源，必须知道命中了哪一段；
3. 文档更新时按 document_id 整体替换即可，不需要重建整个库。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import settings

try:  # pragma: no cover - 依赖缺失时的降级路径
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover
    from sqlalchemy.types import NullType

    def Vector(dim: int | None = None) -> Any:  # type: ignore[misc]
        """未安装 pgvector 时的占位列类型，保证模型定义可导入。"""
        return NullType()


class Base(DeclarativeBase):
    pass


class KBDocument(Base):
    """一篇知识文档。"""

    __tablename__ = "kb_document"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_type: Mapped[str] = mapped_column(
        String(32), index=True, comment="breed | disease | care | faq | first_aid"
    )
    title: Mapped[str] = mapped_column(String(200))
    species: Mapped[str] = mapped_column(String(16), index=True, default="all", comment="dog | cat | all")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_uri: Mapped[str] = mapped_column(String(500), default="")
    version: Mapped[str] = mapped_column(String(32), default="v1")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    chunks: Mapped[list["KBChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<KBDocument {self.id} {self.title}>"


class KBChunk(Base):
    """一个可被检索的知识片段。"""

    __tablename__ = "kb_chunk"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_chunk_doc_index"),
    )

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("kb_document.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    heading: Mapped[str] = mapped_column(String(200), default="")
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    # 向量维度由 EMBEDDING_DIM 决定，换 embedding 模型必须重建表
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.EMBEDDING_DIM))

    document: Mapped[KBDocument] = relationship(back_populates="chunks")

    @property
    def citation(self) -> str:
        """给回答用的短引用，形如《犬瘟热》· 症状识别。"""
        title = self.document.title if self.document else self.document_id
        return f"《{title}》· {self.heading}" if self.heading else f"《{title}》"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
