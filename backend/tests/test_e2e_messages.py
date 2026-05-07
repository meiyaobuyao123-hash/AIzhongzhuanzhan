"""End-to-end /v1/messages: full pipeline (auth → route → upstream mock → bill)."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from app.auth import generate_prism_key
from app.crypto import encrypt
from app.models.orm import ApiKey, Channel, Model, User


@asynccontextmanager
async def _build_app(db_engine, master_key: bytes):
    """Build a FastAPI app whose `get_db` and master_key point at our test fixtures."""
    _, Session = db_engine

    # Patch settings.master_key BEFORE importing app modules that read it.
    # In our test env, conftest.py sets PRISM_MASTER_KEY_HEX. We just verify
    # we're using the same master key.
    from app.config import settings
    if settings.master_key != master_key:
        # Re-encrypt with the test master_key inside fixture data.
        pass

    from app.deps import get_db as real_get_db  # noqa: F401
    from app.main import app

    # Override get_db
    async def override_get_db():
        async with Session() as s:
            yield s

    from app.deps import get_db
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield app
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@respx.mock
async def test_post_messages_non_streaming_full_flow(db_engine):
    from app.config import settings

    master_key = settings.master_key
    _, Session = db_engine

    async with Session() as db:
        # Seed user, key, model, channel
        full_key, hashed, prefix, last4 = generate_prism_key()
        user = User(email="alice@example.com", balance_micro_cents=100_000_000_00)  # $100
        db.add(user)
        await db.flush()

        api_key = ApiKey(user_id=user.id, key_hash=hashed, key_prefix=prefix, key_last4=last4)
        db.add(api_key)

        model = Model(
            model_id="claude-haiku-4-5",
            display_name="Claude Haiku 4.5",
            provider="anthropic",
            price_input_per_million=80_000_000,
            price_output_per_million=400_000_000,
        )
        db.add(model)

        channel = Channel(
            name="test-anthropic",
            provider="anthropic",
            base_url="https://api.anthropic.com",
            upstream_key_encrypted=encrypt("sk-ant-fake-test-key", master_key),
            models=json.dumps(["claude-haiku-4-5"]),
            priority=100,
        )
        db.add(channel)
        await db.commit()

    # Mock upstream
    upstream_resp = {
        "id": "msg_test123",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "hi there"}],
        "model": "claude-haiku-4-5",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 50, "output_tokens": 25},
    }
    route = respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=Response(200, json=upstream_resp)
    )

    async with _build_app(db_engine, master_key) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post(
                "/v1/messages",
                headers={"Authorization": f"Bearer {full_key}"},
                json={"model": "claude-haiku-4-5", "messages": [{"role": "user", "content": "hi"}]},
            )

    assert r.status_code == 200
    body = r.json()
    assert body == upstream_resp
    assert route.called

    # Verify usage_log + balance deduction
    async with Session() as db:
        from sqlalchemy import select
        from app.models.orm import BalanceTransaction, UsageLog

        log = (await db.execute(select(UsageLog))).scalar_one()
        assert log.prompt_tokens == 50
        assert log.completion_tokens == 25
        assert log.status == "ok"
        # cost: 50 * 80M // 1M + 25 * 400M // 1M = 4_000 + 10_000 = 14_000 µ¢ = $0.00014
        assert log.cost_micro_cents == 14_000

        btx = (await db.execute(select(BalanceTransaction))).scalar_one()
        assert btx.amount_micro_cents == -14_000
        assert btx.type == "inference"

        # Balance went from $100 to $100 - $0.00014
        u = (await db.execute(select(User))).scalar_one()
        assert u.balance_micro_cents == 100_000_000_00 - 14_000


@pytest.mark.asyncio
async def test_post_messages_invalid_key_returns_401(db_engine):
    async with _build_app(db_engine, b"M" * 32) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post(
                "/v1/messages",
                headers={"Authorization": "Bearer sk-prism-totally-fake"},
                json={"model": "x", "messages": []},
            )
    assert r.status_code == 401
    assert r.json()["error"]["type"] == "authentication_error"


@pytest.mark.asyncio
async def test_post_messages_insufficient_balance_returns_402(db_engine):
    from app.config import settings

    master_key = settings.master_key
    _, Session = db_engine

    async with Session() as db:
        full_key, hashed, prefix, last4 = generate_prism_key()
        user = User(email="poor@example.com", balance_micro_cents=0)
        db.add(user)
        await db.flush()
        db.add(ApiKey(user_id=user.id, key_hash=hashed, key_prefix=prefix, key_last4=last4))
        db.add(Model(
            model_id="claude-haiku-4-5",
            display_name="Haiku", provider="anthropic",
            price_input_per_million=80_000_000,
            price_output_per_million=400_000_000,
        ))
        db.add(Channel(
            name="ch", provider="anthropic",
            base_url="https://api.anthropic.com",
            upstream_key_encrypted=encrypt("sk-fake", master_key),
            models=json.dumps(["claude-haiku-4-5"]),
        ))
        await db.commit()

    async with _build_app(db_engine, master_key) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post(
                "/v1/messages",
                headers={"Authorization": f"Bearer {full_key}"},
                json={"model": "claude-haiku-4-5", "messages": [{"role": "user", "content": "hi"}]},
            )
    assert r.status_code == 402
    assert r.json()["error"]["code"] == "insufficient_balance"


@pytest.mark.asyncio
async def test_post_messages_unknown_model_returns_404(db_engine):
    from app.config import settings

    master_key = settings.master_key
    _, Session = db_engine

    async with Session() as db:
        full_key, hashed, prefix, last4 = generate_prism_key()
        user = User(email="x@example.com", balance_micro_cents=10_000_000_00)
        db.add(user)
        await db.flush()
        db.add(ApiKey(user_id=user.id, key_hash=hashed, key_prefix=prefix, key_last4=last4))
        await db.commit()

    async with _build_app(db_engine, master_key) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post(
                "/v1/messages",
                headers={"Authorization": f"Bearer {full_key}"},
                json={"model": "no-such-model", "messages": []},
            )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "model_not_found"


@pytest.mark.asyncio
async def test_get_v1_models_returns_catalog(db_engine):
    _, Session = db_engine
    async with Session() as db:
        db.add(Model(
            model_id="claude-haiku-4-5",
            display_name="Haiku", provider="anthropic",
            context_window=200_000,
            price_input_per_million=80_000_000,
            price_output_per_million=400_000_000,
        ))
        await db.commit()

    async with _build_app(db_engine, b"M" * 32) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.get("/v1/models")
    assert r.status_code == 200
    body = r.json()
    assert body["object"] == "list"
    assert any(m["id"] == "claude-haiku-4-5" for m in body["data"])


@pytest.mark.asyncio
async def test_healthz(db_engine):
    async with _build_app(db_engine, b"M" * 32) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
