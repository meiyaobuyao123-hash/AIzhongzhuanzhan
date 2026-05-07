"""Router v0.1: simple model→channel."""

from __future__ import annotations

import json

import pytest

from app.crypto import encrypt
from app.errors import ModelNotFound, NoChannelAvailable
from app.models.orm import Channel, Model
from app.routing import find_model, route


@pytest.mark.asyncio
async def test_find_model_success(db_session):
    db_session.add(Model(
        model_id="claude-opus-4-5",
        display_name="Claude Opus 4.5",
        provider="anthropic",
        price_input_per_million=1_500_000_000,
        price_output_per_million=7_500_000_000,
    ))
    await db_session.commit()
    m = await find_model("claude-opus-4-5", db_session)
    assert m.model_id == "claude-opus-4-5"


@pytest.mark.asyncio
async def test_find_model_not_found(db_session):
    with pytest.raises(ModelNotFound):
        await find_model("does-not-exist", db_session)


@pytest.mark.asyncio
async def test_find_model_disabled_skipped(db_session):
    db_session.add(Model(
        model_id="claude-opus-4-5",
        display_name="X", provider="anthropic",
        price_input_per_million=1, price_output_per_million=1,
        enabled=False,
    ))
    await db_session.commit()
    with pytest.raises(ModelNotFound):
        await find_model("claude-opus-4-5", db_session)


@pytest.mark.asyncio
async def test_route_picks_priority_desc(db_session):
    master = b"M" * 32
    model = Model(
        model_id="claude-opus-4-5", display_name="X", provider="anthropic",
        price_input_per_million=1, price_output_per_million=1,
    )
    db_session.add(model)
    db_session.add(Channel(
        name="low-pri", provider="anthropic",
        base_url="https://api.anthropic.com",
        upstream_key_encrypted=encrypt("k", master),
        models=json.dumps(["claude-opus-4-5"]),
        priority=50,
    ))
    db_session.add(Channel(
        name="high-pri", provider="anthropic",
        base_url="https://api.anthropic.com",
        upstream_key_encrypted=encrypt("k", master),
        models=json.dumps(["claude-opus-4-5"]),
        priority=200,
    ))
    await db_session.commit()
    await db_session.refresh(model)

    chosen = await route(model, db_session)
    assert chosen.name == "high-pri"


@pytest.mark.asyncio
async def test_route_skips_when_model_not_in_channel_models(db_session):
    master = b"M" * 32
    model = Model(
        model_id="claude-opus-4-5", display_name="X", provider="anthropic",
        price_input_per_million=1, price_output_per_million=1,
    )
    db_session.add(model)
    # Channel exists for anthropic but doesn't list this model
    db_session.add(Channel(
        name="ch", provider="anthropic",
        base_url="https://api.anthropic.com",
        upstream_key_encrypted=encrypt("k", master),
        models=json.dumps(["other-model"]),
        priority=100,
    ))
    await db_session.commit()
    await db_session.refresh(model)

    with pytest.raises(NoChannelAvailable):
        await route(model, db_session)


@pytest.mark.asyncio
async def test_route_skips_disabled_channel(db_session):
    master = b"M" * 32
    model = Model(
        model_id="claude-opus-4-5", display_name="X", provider="anthropic",
        price_input_per_million=1, price_output_per_million=1,
    )
    db_session.add(model)
    db_session.add(Channel(
        name="disabled", provider="anthropic",
        base_url="https://api.anthropic.com",
        upstream_key_encrypted=encrypt("k", master),
        models=json.dumps(["claude-opus-4-5"]),
        priority=200, enabled=False,
    ))
    await db_session.commit()
    await db_session.refresh(model)

    with pytest.raises(NoChannelAvailable):
        await route(model, db_session)
