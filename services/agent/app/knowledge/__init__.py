"""知识库子系统。

组成模块与阅读顺序：

    models.py     两张 ORM 表：kb_document / kb_chunk
    db.py         惰性连接、会话作用域、建表与 DDL
    loaders/      语料加载（md / json / csv，目录名即分类）
    chunkers/     标题感知 + 滑窗切分
    embeddings/   可插拔向量化（hash / local / openai）
    vectorstore/  写入、向量粗召回、关键词补充
    rerank/       精排（启发式 / cross-encoder）
    retriever/    检索主流程，唯一对外入口
    pipeline/     灌库流水线
    cli.py        命令行工具
    api.py        对内 HTTP 接口

数据流：

    语料目录 → loaders → chunkers → embeddings → kb_chunk (pgvector)
                                                      ↓
                                query → embeddings → 粗召回 → rerank → 上下文
"""

from app.knowledge.retriever import KnowledgeRetriever, build_context
from app.knowledge.pipeline import KnowledgePipeline

__all__ = ["KnowledgeRetriever", "KnowledgePipeline", "build_context"]
