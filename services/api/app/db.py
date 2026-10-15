"""MySQL 引擎与会话层（本地 MySQL 9.7，root/123456）。

采用同步 SQLAlchemy + pymysql 驱动：FastAPI 的 sync def 路由会自动跑在线程池，
避免在事件循环里阻塞。create_all 仅用于本地建表；生产环境应由 alembic 迁移接管。
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


def _make_engine():
    # MySQL 走 TCP，不需要 check_same_thread 之类 sqlite 专属参数
    return create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        pool_pre_ping=True,
        echo=settings.DB_ECHO,
        future=True,
    )


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """所有 ORM 模型的声明基类。"""


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：每次请求一个会话，结束时回池并关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all() -> None:
    """建库建表（仅本地/演示用）。生产请改用 alembic。"""
    # 延迟导入，避免循环依赖
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
