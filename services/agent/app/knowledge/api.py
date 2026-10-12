"""知识库 HTTP 接口（仅对内）。

暴露三件事，让知识与"回答"链路解耦：
- search：给任意节点/工具按语义取片段
- ingest ：触发重新灌库（管理端接知识运营）
- stats  ：观察库的健康度

注意：这些端点在 api 服务侧不会被直接转发给客户端，
管理端要用需要通过 services/api 做一层权限封装。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.guard import InternalAuth
from app.knowledge import db as db_utils
from app.knowledge.pipeline import KnowledgePipeline
from app.knowledge.retriever import KnowledgeRetriever
from app.knowledge.vectorstore import KnowledgeStore

router = APIRouter(prefix="/internal/v1/knowledge", tags=["knowledge"])


@router.get("/stats", dependencies=[InternalAuth], summary="知识库统计")
async def stats() -> dict:
    store = KnowledgeStore()
    try:
        with db_utils.session_scope() as session:
            payload = {
                "stats": store.stats(session),
                "bySourceType": store.source_breakdown(session),
                "embeddingProvider": settings.EMBEDDING_PROVIDER,
                "embeddingDim": settings.EMBEDDING_DIM,
            }
    except Exception as exc:  # noqa: BLE001 - 数据库不可用时给可读错误
        raise HTTPException(status_code=503, detail=f"知识库不可用: {exc}") from exc
    return {"code": 0, "message": "ok", "data": payload}


@router.post("/search", dependencies=[InternalAuth], summary="语义检索")
async def search(payload: dict[str, Any]) -> dict:
    query = str(payload.get("query") or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query 不能为空")

    retriever = KnowledgeRetriever()
    try:
        with db_utils.session_scope() as session:
            items = retriever.retrieve(
                session,
                query,
                top_k=int(payload.get("topK") or settings.RETRIEVAL_TOP_K),
                source_types=payload.get("sourceTypes"),
                species=payload.get("species"),
            )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"检索失败: {exc}") from exc

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "items": [
                {
                    "chunkId": item.chunk_id,
                    "docId": item.doc_id,
                    "title": item.title,
                    "heading": item.heading,
                    "content": item.content,
                    "score": item.score,
                    "sourceType": item.source_type,
                    "citation": item.citation,
                }
                for item in items
            ]
        },
    }


@router.post("/ingest", dependencies=[InternalAuth], summary="触发灌库")
async def ingest(rebuild: bool = Query(default=False)) -> dict:
    """同步执行灌库。语料规模在数千段以内时耗时可接受。"""
    pipeline = KnowledgePipeline()
    try:
        report = pipeline.ingest_dir(rebuild=rebuild)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"灌库失败: {exc}") from exc

    status = 0 if not report.skipped else 207  # 207 表示部分成功
    return {"code": status, "message": "ok" if status == 0 else "部分文档失败", "data": report.as_dict()}
