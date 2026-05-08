"""v0.3 C1: prompt cache sticky routing tests."""

from __future__ import annotations

import fakeredis.aioredis
import pytest

from app.models.orm import Model
from app.routing.sticky import (
    STICKY_TTL_SECONDS,
    compute_fingerprint,
    has_cache_control,
    lookup_sticky,
    record_sticky,
)


def _model() -> Model:
    return Model(
        model_id="claude-opus-4-5",
        display_name="X",
        provider="anthropic",
        price_input_per_million=1_500_000_000,
        price_output_per_million=7_500_000_000,
    )


@pytest.fixture
async def redis_client():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.aclose()


# ─── has_cache_control ────────────────────────────────────────────────────────


def test_has_cache_control_in_messages_text_block():
    body = {
        "messages": [
            {"role": "user", "content": [
                {"type": "text", "text": "long context", "cache_control": {"type": "ephemeral"}},
            ]},
        ],
    }
    assert has_cache_control(body) is True


def test_has_cache_control_in_system_block():
    body = {
        "system": [{"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": "hi"}],
    }
    assert has_cache_control(body) is True


def test_has_cache_control_in_tool_definition():
    body = {
        "tools": [{"name": "x", "description": "y", "input_schema": {}, "cache_control": {}}],
        "messages": [{"role": "user", "content": "hi"}],
    }
    assert has_cache_control(body) is True


def test_no_cache_control():
    body = {"messages": [{"role": "user", "content": "hi"}]}
    assert has_cache_control(body) is False


# ─── compute_fingerprint ──────────────────────────────────────────────────────


def test_fingerprint_deterministic():
    body1 = {
        "system": "Be helpful",
        "messages": [{"role": "user", "content": "What is 2+2?"}],
    }
    body2 = {
        "system": "Be helpful",
        "messages": [
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "4"},
            {"role": "user", "content": "and 3+3?"},
        ],
    }
    # Different conversations but SAME prefix (system + first user) → same fingerprint
    assert compute_fingerprint(body1) == compute_fingerprint(body2)


def test_fingerprint_different_for_different_system():
    body1 = {"system": "Be helpful", "messages": [{"role": "user", "content": "hi"}]}
    body2 = {"system": "Be terse",   "messages": [{"role": "user", "content": "hi"}]}
    assert compute_fingerprint(body1) != compute_fingerprint(body2)


def test_fingerprint_different_for_different_first_user():
    body1 = {"messages": [{"role": "user", "content": "hi"}]}
    body2 = {"messages": [{"role": "user", "content": "hello"}]}
    assert compute_fingerprint(body1) != compute_fingerprint(body2)


def test_fingerprint_empty_for_no_prefix():
    assert compute_fingerprint({}) == ""
    assert compute_fingerprint({"messages": []}) == ""


# ─── lookup / record sticky ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_lookup_returns_none_without_cache_control(redis_client):
    body = {"__prism_user_id": 42, "messages": [{"role": "user", "content": "hi"}]}
    assert await lookup_sticky(_model(), body, redis_client) is None


@pytest.mark.asyncio
async def test_lookup_returns_none_when_no_record(redis_client):
    body = {
        "__prism_user_id": 42,
        "messages": [{
            "role": "user", "content": [
                {"type": "text", "text": "hi", "cache_control": {"type": "ephemeral"}},
            ],
        }],
    }
    assert await lookup_sticky(_model(), body, redis_client) is None


@pytest.mark.asyncio
async def test_record_then_lookup_roundtrip(redis_client):
    body = {
        "__prism_user_id": 42,
        "messages": [{
            "role": "user", "content": [
                {"type": "text", "text": "long context",
                 "cache_control": {"type": "ephemeral"}},
            ],
        }],
    }
    await record_sticky(_model(), body, channel_id=7, redis_client=redis_client)
    got = await lookup_sticky(_model(), body, redis_client)
    assert got == 7


@pytest.mark.asyncio
async def test_record_skipped_without_cache_control(redis_client):
    body = {"__prism_user_id": 42, "messages": [{"role": "user", "content": "hi"}]}
    await record_sticky(_model(), body, channel_id=7, redis_client=redis_client)
    # Nothing was written
    keys = await redis_client.keys("prism:sticky:*")
    assert keys == []


@pytest.mark.asyncio
async def test_sticky_isolated_per_user(redis_client):
    body_a = {
        "__prism_user_id": 1,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "ctx", "cache_control": {"type": "ephemeral"}},
        ]}],
    }
    body_b = {**body_a, "__prism_user_id": 2}
    await record_sticky(_model(), body_a, 5, redis_client)
    assert await lookup_sticky(_model(), body_a, redis_client) == 5
    # User 2 gets a separate sticky slot
    assert await lookup_sticky(_model(), body_b, redis_client) is None


@pytest.mark.asyncio
async def test_sticky_ttl_set(redis_client):
    body = {
        "__prism_user_id": 42,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "hi", "cache_control": {"type": "ephemeral"}},
        ]}],
    }
    await record_sticky(_model(), body, 5, redis_client)
    keys = await redis_client.keys("prism:sticky:*")
    assert len(keys) == 1
    ttl = await redis_client.ttl(keys[0])
    assert 0 < ttl <= STICKY_TTL_SECONDS
