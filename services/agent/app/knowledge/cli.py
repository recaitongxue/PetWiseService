"""知识库命令行工具。

用法：
    python -m app.knowledge.cli init-db                 # 建表与索引
    python -m app.knowledge.cli ingest                  # 灌入库
    python -m app.knowledge.cli ingest --rebuild        # 清空后重建
    python -m app.knowledge.cli search "猫呕吐怎么办"    # 检索自测
    python -m app.knowledge.cli stats                   # 统计
    python -m app.knowledge.cli reset                   # 清空（危险）
"""

from __future__ import annotations

import argparse
import json
import sys

from app.config import settings
from app.knowledge import db as db_utils
from app.knowledge.pipeline import KnowledgePipeline, ensure_schema
from app.knowledge.retriever import KnowledgeRetriever
from app.knowledge.vectorstore import KnowledgeStore


def _cmd_init_db(_: argparse.Namespace) -> int:
    steps = ensure_schema()
    print("[init-db] 执行完成：")
    for step in steps[:6]:
        print("  -", step)
    print(f"  ... 共 {len(steps)} 项")
    return 0


def _cmd_ingest(args: argparse.Namespace) -> int:
    pipeline = KnowledgePipeline()
    report = pipeline.ingest_dir(args.dir, rebuild=args.rebuild)
    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    if report.skipped:
        print(f"[warn] {report.skipped} 篇文档未入库，详见 errors 字段", file=sys.stderr)
    return 0 if not report.skipped else 1


def _cmd_search(args: argparse.Namespace) -> int:
    retriever = KnowledgeRetriever()
    store = KnowledgeStore()
    with db_utils.session_scope() as session:
        items = retriever.retrieve(
            session,
            args.query,
            top_k=args.top_k,
            source_types=args.source_type.split(",") if args.source_type else None,
            species=args.species,
        )
        if not items:
            print("[search] 无召回结果")
            return 0
        for i, item in enumerate(items, 1):
            print(f"\n[{i}] score={item.score:.4f}  {item.citation}")
            print(item.content[:300].replace("\n", " "))
    return 0


def _cmd_stats(_: argparse.Namespace) -> int:
    store = KnowledgeStore()
    with db_utils.session_scope() as session:
        stats = store.stats(session)
        breakdown = store.source_breakdown(session)
    payload = {
        "corpusDir": str(settings.KB_CORPUS_DIR),
        "embeddingProvider": settings.EMBEDDING_PROVIDER,
        "embeddingDim": settings.EMBEDDING_DIM,
        "stats": stats,
        "bySourceType": breakdown,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _cmd_reset(_: argparse.Namespace) -> int:
    """清空知识库。"""
    confirm = input("将清空全部知识库数据，输入 yes 确认：")
    if confirm.strip().lower() != "yes":
        print("已取消")
        return 0
    store = KnowledgeStore()
    with db_utils.session_scope() as session:
        docs, chunks = store.clear(session)
    print(f"已清空 {docs} 篇文档 / {chunks} 段知识")
    return 0


def build_parser() -> argparse.ArgumentParser:
    from pathlib import Path

    parser = argparse.ArgumentParser(prog="petwise-knowledge", description="宠物知识库工具")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="建表与索引").set_defaults(func=_cmd_init_db)

    ingest = sub.add_parser("ingest", help="灌入语料目录")
    ingest.add_argument("--dir", type=Path, default=None, help="语料目录，默认取配置")
    ingest.add_argument("--rebuild", action="store_true", help="先清空再灌入")
    ingest.set_defaults(func=_cmd_ingest)

    search = sub.add_parser("search", help="检索自测")
    search.add_argument("query", type=str)
    search.add_argument("--top-k", type=int, default=5)
    search.add_argument("--source-type", type=str, default="")
    search.add_argument("--species", type=str, default=None)
    search.set_defaults(func=_cmd_search)

    sub.add_parser("stats", help="查看统计").set_defaults(func=_cmd_stats)
    sub.add_parser("reset", help="清空知识库").set_defaults(func=_cmd_reset)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
