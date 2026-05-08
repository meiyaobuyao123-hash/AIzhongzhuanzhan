"""Shared pytest fixtures.

We override the database to a per-test-process in-memory SQLite, override
settings before importing app modules, and patch the Redis singleton with
fakeredis so tests never touch a real Redis.
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
os.environ["PRISM_JWT_SECRET"] = "test-jwt-secret-do-not-use-in-prod"
# v0.3: disable background loops by default. Tests that exercise them will
# call the helpers directly rather than through the lifespan.
os.environ["PRISM_CHAIN_MONITORS"] = ""
os.environ["PRISM_CAPACITY_CHECK_INTERVAL_S"] = "999999"


@pytest.fixture(autouse=True)
def _patch_redis_with_fakeredis(monkeypatch):
    """Replace the Redis singleton with fakeredis so tests never connect to real Redis."""
    import fakeredis.aioredis

    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    from app import redis_client

    monkeypatch.setattr(redis_client, "_redis", fake, raising=False)
    yield
    # Note: we don't aclose() the fake here — fakeredis instance is per-test,
    # and aclose is async; teardown via monkeypatch reverts the singleton.


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
