"""Rate limiting + circuit breaker tests using fakeredis."""

from __future__ import annotations

import time

import fakeredis.aioredis
import pytest

from app.limits import (
    COOLDOWN_INITIAL_S,
    RateLimited,
    check_rpm_limit,
    default_rpm_for_user,
    get_channel_health,
    is_channel_available,
    mark_channel_failure,
    mark_channel_success,
)


@pytest.fixture
async def redis_client():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.aclose()


# ---- Tier defaults ----------------------------------------------------------


def test_tier_default_rpm_self_serve_brackets():
    assert default_rpm_for_user(0, "self-serve") == 60
    assert default_rpm_for_user(50_00_000_000 - 1, "self-serve") == 60      # < $50
    assert default_rpm_for_user(50_00_000_000, "self-serve") == 240         # $50
    assert default_rpm_for_user(500_00_000_000 - 1, "self-serve") == 240
    assert default_rpm_for_user(500_00_000_000, "self-serve") == 600        # $500
    assert default_rpm_for_user(5000_00_000_000, "self-serve") == 1200      # $5000


def test_tier_team_always_top():
    assert default_rpm_for_user(0, "team") == 1200


# ---- Rate limit -------------------------------------------------------------


@pytest.mark.asyncio
async def test_check_rpm_no_limit_when_zero(redis_client):
    # rpm_limit=None / 0 → no-op
    await check_rpm_limit(api_key_id=1, rpm_limit=None, redis_client=redis_client)
    await check_rpm_limit(api_key_id=1, rpm_limit=0, redis_client=redis_client)


@pytest.mark.asyncio
async def test_check_rpm_under_limit_passes(redis_client):
    for _ in range(5):
        await check_rpm_limit(api_key_id=42, rpm_limit=10, redis_client=redis_client)


@pytest.mark.asyncio
async def test_check_rpm_over_limit_raises(redis_client):
    for _ in range(10):
        await check_rpm_limit(api_key_id=99, rpm_limit=10, redis_client=redis_client)
    with pytest.raises(RateLimited) as exc_info:
        await check_rpm_limit(api_key_id=99, rpm_limit=10, redis_client=redis_client)
    assert exc_info.value.retry_after == 60


@pytest.mark.asyncio
async def test_check_rpm_per_key_isolation(redis_client):
    # Hit limit on key A, key B unaffected
    for _ in range(10):
        await check_rpm_limit(api_key_id=1, rpm_limit=10, redis_client=redis_client)
    with pytest.raises(RateLimited):
        await check_rpm_limit(api_key_id=1, rpm_limit=10, redis_client=redis_client)
    # B still works
    await check_rpm_limit(api_key_id=2, rpm_limit=10, redis_client=redis_client)


# ---- Circuit breaker --------------------------------------------------------


@pytest.mark.asyncio
async def test_default_state_healthy(redis_client):
    h = await get_channel_health(1, redis_client)
    assert h.state == "healthy"
    assert h.cooldown_until == 0
    assert h.fail_streak == 0


@pytest.mark.asyncio
async def test_failure_marks_cooling(redis_client):
    cooldown = await mark_channel_failure(7, redis_client)
    assert cooldown == COOLDOWN_INITIAL_S  # first failure: 30s
    h = await get_channel_health(7, redis_client)
    assert h.state == "cooling"
    assert h.fail_streak == 1
    assert h.cooldown_until > int(time.time())


@pytest.mark.asyncio
async def test_progressive_cooldown(redis_client):
    cd1 = await mark_channel_failure(8, redis_client)
    cd2 = await mark_channel_failure(8, redis_client)
    cd3 = await mark_channel_failure(8, redis_client)
    assert cd1 == 30
    assert cd2 == 60
    assert cd3 == 120


@pytest.mark.asyncio
async def test_explicit_retry_after_honoured(redis_client):
    cooldown = await mark_channel_failure(11, redis_client, retry_after_s=200)
    assert cooldown == 200


@pytest.mark.asyncio
async def test_success_resets(redis_client):
    await mark_channel_failure(9, redis_client)
    await mark_channel_failure(9, redis_client)
    assert (await get_channel_health(9, redis_client)).fail_streak == 2

    await mark_channel_success(9, redis_client)
    h = await get_channel_health(9, redis_client)
    assert h.state == "healthy"
    assert h.fail_streak == 0
    assert h.cooldown_until == 0


@pytest.mark.asyncio
async def test_is_available_when_cooling(redis_client):
    await mark_channel_failure(15, redis_client, retry_after_s=300)
    assert not await is_channel_available(15, redis_client)


@pytest.mark.asyncio
async def test_is_available_when_healthy(redis_client):
    assert await is_channel_available(123, redis_client)


@pytest.mark.asyncio
async def test_cooldown_expiry_transitions_to_half_open(redis_client):
    """When cooldown_until is in the past, state becomes half-open via auto-transition."""
    # Simulate by setting cooldown to 1 second ago
    await redis_client.set("prism:channel:21:state", "cooling")
    await redis_client.set("prism:channel:21:cooldown_until", int(time.time()) - 5)

    h = await get_channel_health(21, redis_client)
    assert h.state == "half-open"
