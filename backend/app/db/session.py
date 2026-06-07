from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _engine_url() -> str:
    return get_settings().database_url


engine = create_engine(
    _engine_url(),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"check_same_thread": False} if _engine_url().startswith("sqlite") else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
_initialized = False


def get_db() -> Generator[Session, None, None]:
    init_database()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database() -> None:
    global _initialized
    if _initialized:
        return
    # Local SQLite can bootstrap itself. Supabase/Postgres should use SQL migrations.
    if _engine_url().startswith("sqlite"):
        from app.db import models  # noqa: F401

        Base.metadata.create_all(bind=engine)
    _initialized = True
