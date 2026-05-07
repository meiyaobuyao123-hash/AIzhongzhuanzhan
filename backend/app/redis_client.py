"""Async Redis client + dependency.

Uses redis.asyncio.Redis singleton (created at module import). Tests can override
by patching `_redis` before any helper is called.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import redis.asyncio as redis

from app.config import settings

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """Lazy-init singleton."""
    global _redis
    if _redis is None:
        _redis = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            encoding="utf-8",
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


async def redis_dep() -> AsyncIterator[redis.Redis]:
    """FastAPI dependency: yields the singleton Redis client."""
    yield get_redis()
