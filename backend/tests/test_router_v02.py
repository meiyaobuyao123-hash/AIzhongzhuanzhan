"""v0.2 multi-channel router: candidates, healthy filter, weighted pick."""

from __future__ import annotations

import json
from collections import Counter

import fakeredis.aioredis
import pytest

from app.crypto import encrypt
from app.errors import NoChannelAvailable
from app.limits import mark_channel_failure
from app.models.orm import Channel, Model
from app.routing import (
    filter_healthy,
    find_candidates,
    pick_one,
    weighted_pick,
)


@pytest.fixture
async def redis_client():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.aclose()


def _make_channel(name: str, models_list: list[str], priority: int = 100, weight: int = 100, channel_id: int | None = None):
    return Channel(
        id=channel_id,
        name=name,
        provider="anthropic",
        base_url="https://api.anthropic.com",
        upstream_key_encrypted=encrypt("sk-test", b"M" * 32),
        models=json.dumps(models_list),
        channel_group="default",
        priority=priority,
        weight=weight,
        enabled=True,
    )


@pytest.mark.asyncio
async def test_find_candidates_returns_all_matching(db_session):
    db_session.add(Model(
        model_id="claude-opus-4-5", display_name="X", provider="anthropic",
        price_input_per_million=1, price_output_per_million=1,
    ))
    db_session.add(_make_channel("a", ["claude-opus-4-5"], priority=200))
    db_session.add(_make_channel("b", ["claude-opus-4-5"], priority=100))
    db_session.add(_make_channel("c", ["other"]))  # different model
    await db_session.commit()
    model = (await db_session.execute(__import__("sqlalchemy").select(Model))).scalar_one()
    cands = await find_candidates(model, db_session)
    names = {c.name for c in cands}
    assert names == {"a", "b"}


@pytest.mark.asyncio
async def test_find_candidates_skips_disabled(db_session):
    db_session.add(Model(
        model_id="m", display_name="X", provider="anthropic",
        price_input_per_million=1, price_output_per_million=1,
    ))
    db_session.add(_make_channel("a", ["m"]))
    db_session.add(Channel(
        name="b", provider="anthropic", base_url="https://x",
        upstream_key_encrypted=encrypt("k", b"M" * 32),
        models=json.dumps(["m"]),
        channel_group="default", priority=100, weight=100,
        enabled=False,  # disabled
    ))
    await db_session.commit()
    model = (await db_session.execute(__import__("sqlalchemy").select(Model))).scalar_one()
    cands = await find_candidates(model, db_session)
    assert {c.name for c in cands} == {"a"}


@pytest.mark.asyncio
async def test_filter_healthy_excludes_cooling(redis_client):
    chans = [_make_channel("a", ["m"], channel_id=1), _make_channel("b", ["m"], channel_id=2)]
    # Cool channel 1
    await mark_channel_failure(1, redis_client, retry_after_s=300)

    healthy = await filter_healthy(chans, redis_client)
    assert {c.name for c in healthy} == {"b"}


def test_weighted_pick_distribution_skewed():
    """A channel with weight 90 vs weight 10 should win ~90% of the time."""
    a = _make_channel("a", ["m"], weight=90, channel_id=1)
    b = _make_channel("b", ["m"], weight=10, channel_id=2)

    counts = Counter()
    for _ in range(2000):
        c = weighted_pick([a, b])
        counts[c.name] += 1

    # Very loose check: a wins clearly more
    assert counts["a"] > counts["b"] * 5


def test_weighted_pick_empty_raises():
    with pytest.raises(NoChannelAvailable):
        weighted_pick([])


def test_weighted_pick_single_candidate():
    a = _make_channel("only", ["m"], channel_id=1)
    chosen = weighted_pick([a])
    assert chosen is a


@pytest.mark.asyncio
async def test_pick_one_excludes_tried(db_session, redis_client):
    db_session.add(Model(
        model_id="m", display_name="X", provider="anthropic",
        price_input_per_million=1, price_output_per_million=1,
    ))
    a = _make_channel("a", ["m"])
    b = _make_channel("b", ["m"])
    db_session.add_all([a, b])
    await db_session.commit()
    model = (await db_session.execute(__import__("sqlalchemy").select(Model))).scalar_one()
    await db_session.refresh(a)
    await db_session.refresh(b)

    # exclude a's id → must pick b
    chosen = await pick_one(model, db_session, redis_client, exclude={a.id})
    assert chosen.name == "b"


@pytest.mark.asyncio
async def test_pick_one_all_excluded_raises(db_session, redis_client):
    db_session.add(Model(
        model_id="m", display_name="X", provider="anthropic",
        price_input_per_million=1, price_output_per_million=1,
    ))
    a = _make_channel("a", ["m"])
    db_session.add(a)
    await db_session.commit()
    model = (await db_session.execute(__import__("sqlalchemy").select(Model))).scalar_one()
    await db_session.refresh(a)

    with pytest.raises(NoChannelAvailable):
        await pick_one(model, db_session, redis_client, exclude={a.id})


@pytest.mark.asyncio
async def test_pick_one_all_unhealthy_degrades_to_least_cooled(db_session, redis_client):
    """If all channels are cooling, pick the one with earliest cooldown."""
    db_session.add(Model(
        model_id="m", display_name="X", provider="anthropic",
        price_input_per_million=1, price_output_per_million=1,
    ))
    a = _make_channel("a", ["m"])
    b = _make_channel("b", ["m"])
    db_session.add_all([a, b])
    await db_session.commit()
    model = (await db_session.execute(__import__("sqlalchemy").select(Model))).scalar_one()
    await db_session.refresh(a)
    await db_session.refresh(b)

    await mark_channel_failure(a.id, redis_client, retry_after_s=100)
    await mark_channel_failure(b.id, redis_client, retry_after_s=500)

    chosen = await pick_one(model, db_session, redis_client)
    # 'a' has earlier cooldown_until → should be chosen as the least-bad option
    assert chosen.name == "a"
