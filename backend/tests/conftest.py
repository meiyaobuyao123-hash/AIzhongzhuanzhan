"""Shared pytest fixtures.

We override the database to a per-test-process in-memory SQLite, and override
settings before importing app modules.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

# Set env BEFORE importing app modules that read settings at import time
os.environ["PRISM_DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["PRISM_MASTER_KEY_HEX"] = "0" * 63 + "1"  # 32 bytes, deterministic
os.environ["PRISM_DEBUG"] = "false"


@pytest_asyncio.fixture
async def db_engine():
    """Spin up a fresh in-memory engine + create schema."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.models.orm import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    yield engine, Session

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator:
    _, Session = db_engine
    async with Session() as session:
        yield session
