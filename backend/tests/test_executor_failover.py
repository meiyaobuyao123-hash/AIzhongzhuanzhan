"""Executor: full retry chain + cooldown integration with mocked upstream."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response


@asynccontextmanager
async def _build_app(db_engine):
    from app.deps import get_db
    from app.main import app

    _, Session = db_engine

    async def override_get_db():
        async with Session() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield app
    finally:
        app.dependency_overrides.clear()


async def _seed_user_with_two_channels(Session):
    from argon2 import PasswordHasher
    from app.config import settings
    from app.crypto import encrypt
    from app.auth import generate_prism_key
    from app.models.orm import ApiKey, Channel, Model, User

    ph = PasswordHasher()
    async with Session() as db:
        user = User(
            email="failover@example.com",
            password_hash=ph.hash("long-pwd-12345"),
            email_verified=True,
            balance_micro_cents=100_000_000_00,  # $100
        )
        db.add(user)
        await db.flush()

        full, hashed, prefix, last4 = generate_prism_key()
        ak = ApiKey(user_id=user.id, key_hash=hashed, key_prefix=prefix, key_last4=last4)
        db.add(ak)

        db.add(Model(
            model_id="claude-haiku-4-5", display_name="Haiku", provider="anthropic",
            price_input_per_million=80_000_000,
            price_output_per_million=400_000_000,
        ))

        # Two channels — both for same upstream URL but different "names"
        # We'll use respx to make the first one fail
        db.add(Channel(
            name="ch-A",
            provider="anthropic",
            base_url="https://api.anthropic.com",
            upstream_key_encrypted=encrypt("key-A", settings.master_key),
            models=json.dumps(["claude-haiku-4-5"]),
            priority=200, weight=100,
        ))
        db.add(Channel(
            name="ch-B",
            provider="anthropic",
            base_url="https://api-b.anthropic.com",  # different host, mockable
            upstream_key_encrypted=encrypt("key-B", settings.master_key),
            models=json.dumps(["claude-haiku-4-5"]),
            priority=100, weight=100,
        ))
        await db.commit()
        return full


@pytest.mark.asyncio
@respx.mock
async def test_failover_5xx_to_next_channel(db_engine):
    _, Session = db_engine
    full_key = await _seed_user_with_two_channels(Session)

    # Channel A returns 500, Channel B returns 200
    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=Response(500, json={"error": {"message": "boom"}})
    )
    respx.post("https://api-b.anthropic.com/v1/messages").mock(
        return_value=Response(200, json={
            "id": "msg_x", "model": "claude-haiku-4-5",
            "content": [{"type": "text", "text": "ok"}],
            "usage": {"input_tokens": 5, "output_tokens": 2},
        })
    )

    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post(
                "/v1/messages",
                headers={"Authorization": f"Bearer {full_key}"},
                json={"model": "claude-haiku-4-5",
                      "messages": [{"role": "user", "content": "hi"}]},
            )

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == "msg_x"

    # Verify usage_log records both channels were tried
    from app.models.orm import UsageLog
    from sqlalchemy import select
    async with Session() as db:
        log = (await db.execute(select(UsageLog))).scalar_one()
        assert log.status == "ok"
        # tried_channels should contain both
        tried = json.loads(log.tried_channels)
        assert len(tried) == 2
        assert tried[0]["status"] == 500
        assert tried[1]["status"] == 200


@pytest.mark.asyncio
@respx.mock
async def test_failover_429_with_retry_after(db_engine):
    _, Session = db_engine
    full_key = await _seed_user_with_two_channels(Session)

    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=Response(
            429,
            headers={"retry-after": "120"},
            json={"error": {"message": "rate"}},
        )
    )
    respx.post("https://api-b.anthropic.com/v1/messages").mock(
        return_value=Response(200, json={
            "id": "msg_y", "model": "claude-haiku-4-5",
            "content": [], "usage": {"input_tokens": 1, "output_tokens": 1},
        })
    )

    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post(
                "/v1/messages",
                headers={"Authorization": f"Bearer {full_key}"},
                json={"model": "claude-haiku-4-5",
                      "messages": [{"role": "user", "content": "hi"}]},
            )
    assert r.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_all_channels_fail_returns_502(db_engine):
    _, Session = db_engine
    full_key = await _seed_user_with_two_channels(Session)

    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=Response(500, text="A down")
    )
    respx.post("https://api-b.anthropic.com/v1/messages").mock(
        return_value=Response(503, text="B down")
    )

    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post(
                "/v1/messages",
                headers={"Authorization": f"Bearer {full_key}"},
                json={"model": "claude-haiku-4-5",
                      "messages": [{"role": "user", "content": "hi"}]},
            )
    assert r.status_code == 502
    assert r.json()["error"]["code"] == "all_channels_failed"


@pytest.mark.asyncio
@respx.mock
async def test_4xx_passed_through_no_retry(db_engine):
    """A 400 from the first channel should NOT trigger retry — it's a client error."""
    _, Session = db_engine
    full_key = await _seed_user_with_two_channels(Session)

    a_route = respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=Response(400, json={"error": {"message": "bad request"}})
    )
    b_route = respx.post("https://api-b.anthropic.com/v1/messages").mock(
        return_value=Response(200, json={"id": "msg", "usage": {"input_tokens": 1, "output_tokens": 1}})
    )

    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post(
                "/v1/messages",
                headers={"Authorization": f"Bearer {full_key}"},
                json={"model": "claude-haiku-4-5",
                      "messages": [{"role": "user", "content": "hi"}]},
            )

    assert r.status_code == 400
    # Verify A tried, B NOT tried
    assert a_route.called
    assert not b_route.called


@pytest.mark.asyncio
@respx.mock
async def test_401_marks_cooldown_no_retry(db_engine):
    """401 from upstream means our key is bad — cooldown that channel + return error to client."""
    _, Session = db_engine
    full_key = await _seed_user_with_two_channels(Session)

    a_route = respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=Response(401, json={"error": {"message": "auth bad"}})
    )

    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post(
                "/v1/messages",
                headers={"Authorization": f"Bearer {full_key}"},
                json={"model": "claude-haiku-4-5",
                      "messages": [{"role": "user", "content": "hi"}]},
            )

    assert r.status_code == 401  # passed through to client


@pytest.mark.asyncio
@respx.mock
async def test_attempts_recorded_in_usage_log(db_engine):
    """tried_channels JSON should reflect each attempt."""
    _, Session = db_engine
    full_key = await _seed_user_with_two_channels(Session)

    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=Response(500, text="boom")
    )
    respx.post("https://api-b.anthropic.com/v1/messages").mock(
        return_value=Response(200, json={
            "id": "msg", "model": "claude-haiku-4-5",
            "content": [], "usage": {"input_tokens": 10, "output_tokens": 5},
        })
    )

    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post(
                "/v1/messages",
                headers={"Authorization": f"Bearer {full_key}"},
                json={"model": "claude-haiku-4-5",
                      "messages": [{"role": "user", "content": "hi"}]},
            )

    assert r.status_code == 200
    from app.models.orm import UsageLog
    from sqlalchemy import select
    async with Session() as db:
        log = (await db.execute(select(UsageLog))).scalar_one()
        tried = json.loads(log.tried_channels)
        assert len(tried) == 2
        assert log.attempt_index == 1  # 0-indexed; second attempt succeeded
