"""Rate limiting + circuit breaker helpers backed by Redis.

# Rate limit (sliding 60s window using fixed-bucket INCR + EXPIRE)
- key: prism:rpm:{api_key_id}
- INCR; if first call (returned 1), set EXPIRE 60s
- if value > limit → 429

# Circuit breaker (per channel)
- prism:channel:{id}:state           "healthy" | "cooling" | "half-open"
- prism:channel:{id}:cooldown_until  unix timestamp seconds
- prism:channel:{id}:fail_streak     count of consecutive failures (resets on success)

State transitions:
    HEALTHY → COOLING        on 5xx/429/timeout
    COOLING → HALF-OPEN      on cooldown expiry (next request triggers it)
    HALF-OPEN → HEALTHY      on success
    HALF-OPEN → COOLING      on failure (cooldown × 2, capped 1h)
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from app.config import settings
from app.errors import PrismException

# ──────────────────────────────────────────────────────────────────────────────
# Tier defaults
# ──────────────────────────────────────────────────────────────────────────────


def default_rpm_for_user(total_topped_up_micro_cents: int, tier: str) -> int:
    """Convert cumulative top-up USD into a default RPM bucket.

    Team tier: ceil at GE_5000 (lots of headroom; teams can override per-key).
    Self-serve: stair-step.
    """
    if tier == "team":
        return settings.rpm_tier_ge_5000

    usd = total_topped_up_micro_cents / 100_000_000
    if usd < 50:
        return settings.rpm_tier_lt_50
    if usd < 500:
        return settings.rpm_tier_lt_500
    if usd < 5000:
        return settings.rpm_tier_lt_5000
    return settings.rpm_tier_ge_5000


# ──────────────────────────────────────────────────────────────────────────────
# Rate limit
# ──────────────────────────────────────────────────────────────────────────────


class RateLimited(PrismException):
    status_code = 429
    error_type = "rate_limit_error"
    code = "rate_limit_exceeded"

    def __init__(self, message: str, *, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after or 60


async def check_rpm_limit(
    api_key_id: int, rpm_limit: int | None, redis_client
) -> None:
    """Increment counter and raise RateLimited if exceeded.

    rpm_limit=None or <=0 → no limit.
    """
    if not rpm_limit or rpm_limit <= 0:
        return
    key = f"prism:rpm:{api_key_id}"
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, 60, nx=True)  # Only set TTL if not already set
    cnt, _ = await pipe.execute()
    if cnt > rpm_limit:
        raise RateLimited(
            f"Rate limit exceeded: {cnt} > {rpm_limit} RPM",
            retry_after=60,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Circuit breaker
# ──────────────────────────────────────────────────────────────────────────────


COOLDOWN_INITIAL_S = 30
COOLDOWN_MAX_S = 3600  # 1 hour cap


@dataclass
class ChannelHealth:
    state: str  # healthy / cooling / half-open
    cooldown_until: int  # 0 if not in cooldown
    fail_streak: int


async def get_channel_health(channel_id: int, redis_client) -> ChannelHealth:
    keys = [
        f"prism:channel:{channel_id}:state",
        f"prism:channel:{channel_id}:cooldown_until",
        f"prism:channel:{channel_id}:fail_streak",
    ]
    state, cooldown, streak = await redis_client.mget(*keys)
    state = state or "healthy"
    cooldown_until = int(cooldown or 0)

    # Auto-transition: if cooling but expiry passed, become half-open
    now = int(time.time())
    if state == "cooling" and cooldown_until <= now:
        state = "half-open"
        await redis_client.set(f"prism:channel:{channel_id}:state", "half-open")

    return ChannelHealth(
        state=state,
        cooldown_until=cooldown_until,
        fail_streak=int(streak or 0),
    )


async def is_channel_available(channel_id: int, redis_client) -> bool:
    """True iff state is healthy or half-open (= can attempt a request).
    False if cooling and cooldown not yet expired."""
    h = await get_channel_health(channel_id, redis_client)
    return h.state != "cooling" or h.cooldown_until <= int(time.time())


async def mark_channel_success(channel_id: int, redis_client) -> None:
    """Reset to healthy + clear streak."""
    keys_prefix = f"prism:channel:{channel_id}"
    await redis_client.set(f"{keys_prefix}:state", "healthy")
    await redis_client.delete(f"{keys_prefix}:cooldown_until", f"{keys_prefix}:fail_streak")


async def mark_channel_failure(
    channel_id: int, redis_client, *, retry_after_s: int | None = None
) -> int:
    """Record a failure; transitions to COOLING with progressive backoff.

    Returns the new cooldown duration (seconds).
    """
    keys_prefix = f"prism:channel:{channel_id}"
    streak = await redis_client.incr(f"{keys_prefix}:fail_streak")

    if retry_after_s is not None:
        # Honour upstream Retry-After (usually for 429)
        cooldown_s = max(retry_after_s, COOLDOWN_INITIAL_S)
    else:
        # Progressive: 30s → 60s → 120s → 240s → ... capped 1h
        cooldown_s = min(COOLDOWN_INITIAL_S * (2 ** (streak - 1)), COOLDOWN_MAX_S)

    cooldown_until = int(time.time()) + cooldown_s
    pipe = redis_client.pipeline()
    pipe.set(f"{keys_prefix}:state", "cooling")
    pipe.set(f"{keys_prefix}:cooldown_until", cooldown_until)
    pipe.expire(f"{keys_prefix}:cooldown_until", COOLDOWN_MAX_S * 2)  # GC
    pipe.expire(f"{keys_prefix}:fail_streak", COOLDOWN_MAX_S * 2)
    await pipe.execute()
    return cooldown_s
