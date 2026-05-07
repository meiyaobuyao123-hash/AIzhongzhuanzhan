"""Async SQLAlchemy engine + session factory."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings


def _make_engine():
    kwargs: dict = {"echo": settings.debug, "future": True}
    if settings.is_sqlite:
        # SQLite over aiosqlite: same-thread enforcement is per-connection,
        # async pool handles concurrency
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_async_engine(settings.database_url, **kwargs)


engine = _make_engine()

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a request-scoped DB session."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
