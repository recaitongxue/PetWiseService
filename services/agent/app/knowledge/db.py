"""数据库会话与知识库表初始化。

连接是**惰性**的：健康检查、图构建都不触库，
只有真正检索或灌库时才建立连接，这样没有 Postgres 也能跑通服务冒烟。
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.knowledge.models import Base

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None

# 建表之后的额外 DDL：扩展、索引、全文检索辅助列，
# 都放在 SQL 文件里，避免 ORM 侧被方言细节污染。
_SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def get_engine() -> Engine:
    """单例引擎；首次调用才真正创建连接池。"""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            future=True,
        )
        if settings.DATABASE_URL.startswith("sqlite"):  # 本地轻量调试
            event.listen(_engine, "connect", _enable_sqlite_pragma)
    return _engine


def _enable_sqlite_pragma(dbapi_conn, _connection_record) -> None:  # pragma: no cover
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(), autoflush=False, expire_on_commit=False, future=True
        )
    return _session_factory


@contextlib.contextmanager
def session_scope() -> Iterator[Session]:
    """事务性会话：正常提交、异常回滚、用完必关。"""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> list[str]:
    """建表并建立索引，返回执行摘要（供 CLI 打印）。

    幂等：重复执行不会出错，重复灌库则由 pipeline 层的幂等键控制。
    """
    engine = get_engine()
    executed: list[str] = []

    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgvector"'))
            executed.append("extension:pgvector")

        Base.metadata.create_all(conn)
        executed.append("tables:" + ",".join(sorted(Base.metadata.tables)))

        if engine.dialect.name == "postgresql" and _SCHEMA_FILE.is_file():
            for statement in _split_sql(_SCHEMA_FILE.read_text(encoding="utf-8")):
                if statement:
                    conn.execute(text(statement))
                    executed.append("ddl:ok")

    return executed


def healthcheck() -> bool:
    """健康检查用的轻量连通性探测，失败不抛。"""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False


def _split_sql(raw: str) -> list[str]:
    """按 ;; 分隔多条语句，并剔除注释。"""
    chunks = []
    for block in raw.split(";;"):
        cleaned = "\n".join(
            line for line in block.splitlines() if not line.strip().startswith("--")
        ).strip()
        if cleaned:
            chunks.append(cleaned)
    return chunks
