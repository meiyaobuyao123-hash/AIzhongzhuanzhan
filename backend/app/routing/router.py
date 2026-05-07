"""v0.2 router.

Two-step flow used by the executor:
  1. find_candidates(model) → all enabled channels that can serve this model
  2. pick_one(candidates, exclude=, redis=)
        - filter unhealthy (Redis circuit-breaker state)
        - if all unhealthy → degrade to "least-cooled" channel (best-effort)
        - weighted random pick (by Channel.weight)

For v0.3 this expands to: layer-1 tier filter (default/dev/team-shared/team-{id}),
price²-inverse weighting, prompt-cache stickiness.
"""

from __future__ import annotations

import json
import random
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ModelNotFound, NoChannelAvailable
from app.limits import get_channel_health, is_channel_available
from app.models.orm import Channel, Model


async def find_model(model_id: str, db: AsyncSession) -> Model:
    row = await db.execute(
        select(Model).where(Model.model_id == model_id, Model.enabled.is_(True))
    )
    model = row.scalar_one_or_none()
    if not model:
        raise ModelNotFound(f"Model not found: {model_id}", param="model")
    return model


async def find_candidates(model: Model, db: AsyncSession) -> list[Channel]:
    """All enabled channels for the model's provider that list this model_id."""
    rows = await db.execute(
        select(Channel)
        .where(Channel.provider == model.provider)
        .where(Channel.enabled.is_(True))
        .order_by(Channel.priority.desc(), Channel.id.asc())
    )
    out: list[Channel] = []
    for ch in rows.scalars():
        try:
            ch_models = json.loads(ch.models)
        except (json.JSONDecodeError, TypeError):
            continue
        if model.model_id in ch_models:
            out.append(ch)
    return out


async def filter_healthy(
    candidates: Iterable[Channel], redis_client
) -> list[Channel]:
    healthy: list[Channel] = []
    for c in candidates:
        if await is_channel_available(c.id, redis_client):
            healthy.append(c)
    return healthy


def weighted_pick(candidates: list[Channel]) -> Channel:
    """Pick one by Channel.weight as random.choices weights.

    v0.2: simple weighted random. v0.3 will overlay price²-inverse weighting +
    health bias.
    """
    if not candidates:
        raise NoChannelAvailable("No candidate channels to pick from")
    weights = [max(1, c.weight) for c in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


async def pick_one(
    model: Model,
    db: AsyncSession,
    redis_client,
    *,
    exclude: set[int] | None = None,
) -> Channel:
    """End-to-end candidate selection. Used inside the executor's retry loop.

    Strategy:
      1. Filter to model+enabled candidates
      2. Subtract already-tried (`exclude`)
      3. Filter unhealthy (Redis circuit breaker)
      4. Take the HIGHEST-priority group (channels share priority tiers)
      5. Weighted-random pick inside that tier

    Higher priority always wins over lower priority when both are healthy.
    Within the same priority tier, weight is the random tiebreaker.

    Graceful degrade: if all channels are cooling, pick the one whose cooldown
    expires soonest (best-effort attempt rather than 503).
    """
    exclude = exclude or set()
    candidates = await find_candidates(model, db)
    candidates = [c for c in candidates if c.id not in exclude]
    if not candidates:
        raise NoChannelAvailable(
            f"No upstream channel available for model {model.model_id} "
            f"(all {len(exclude)} candidates exhausted)"
        )

    healthy = await filter_healthy(candidates, redis_client)
    if not healthy:
        # All cooling — pick the one closest to recovery
        scored: list[tuple[int, Channel]] = []
        for c in candidates:
            h = await get_channel_health(c.id, redis_client)
            scored.append((h.cooldown_until or 0, c))
        scored.sort(key=lambda t: t[0])
        return scored[0][1]

    # Take only the highest-priority tier
    max_priority = max(c.priority for c in healthy)
    top_tier = [c for c in healthy if c.priority == max_priority]
    return weighted_pick(top_tier)


# Backwards-compat shim for v0.1 tests (single-channel `route`)
async def route(model: Model, db: AsyncSession) -> Channel:
    """v0.1-style: pick highest-priority enabled channel ignoring health.

    Kept for backwards compat with existing tests; v0.2 callers should use
    `pick_one(model, db, redis)` which honours the circuit breaker.
    """
    candidates = await find_candidates(model, db)
    if not candidates:
        raise NoChannelAvailable(
            f"No upstream channel available for model {model.model_id}"
        )
    return candidates[0]
