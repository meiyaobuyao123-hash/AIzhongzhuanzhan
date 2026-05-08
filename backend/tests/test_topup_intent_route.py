"""POST /account/topup-intent: end-to-end via test client + JWT auth."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.models.orm import PaymentIntent, User


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


async def _create_user_and_jwt(Session, email="topup-intent@x.com"):
    from argon2 import PasswordHasher

    from app.jwt_auth import create_session_record, issue_token

    ph = PasswordHasher()
    async with Session() as db:
        user = User(
            email=email,
            password_hash=ph.hash("long-password-123"),
            email_verified=True,
            balance_micro_cents=0,
        )
        db.add(user)
        await db.flush()
        token, jti, expires_at = issue_token(user.id, tier=user.tier)
        await create_session_record(
            db, user_id=user.id, jti=jti, expires_at=expires_at,
            user_agent=None, ip=None,
        )
        await db.commit()
        return user.id, token


@pytest.mark.asyncio
async def test_topup_intent_creates_pending_intent_with_memo(db_engine):
    _, Session = db_engine
    user_id, token = await _create_user_and_jwt(Session)

    async with _build_app(db_engine) as app, AsyncClient(
        transport=ASGITransport(app=app), base_url="http://t",
    ) as client:
        resp = await client.post(
            "/account/topup-intent",
            json={"channel": "usdt-trc20", "amount_usd": 100.0},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["channel"] == "usdt-trc20"
    assert body["network"] == "tron"
    assert body["address"] == "TT24g41HLptouzxGycZxQKmWaTENK4K4HG"
    assert body["amount_usd"] == 100.0
    assert body["fee_usd"] == 0.05            # 100 * 5bps = $0.05
    assert body["credited_usd"] == 99.95
    assert body["memo"]
    assert len(body["memo"]) == 4
    assert body["expected_amount_micro_cents"] > 100 * 100_000_000
    assert body["expected_amount_micro_cents"] < 101 * 100_000_000
    assert body["expires_at"]

    # Persisted
    async with Session() as db:
        intent = (await db.execute(
            select(PaymentIntent).where(PaymentIntent.user_id == user_id)
        )).scalar_one()
        assert intent.status == "pending"
        assert intent.memo == body["memo"]
        assert intent.expected_amount_micro_cents == body["expected_amount_micro_cents"]
        assert intent.expires_at is not None
        # Should be timezone-aware UTC
        if intent.expires_at.tzinfo is not None:
            assert intent.expires_at.tzinfo.utcoffset(intent.expires_at).total_seconds() == 0
        # Credited = amount - fee
        assert intent.credited_micro_cents == intent.amount_micro_cents - intent.fee_micro_cents


@pytest.mark.asyncio
async def test_topup_intent_unique_expected_amounts_for_concurrent_requests(db_engine):
    """Two pending intents on the same channel for same base amount → memos differ
    so expected_amount_micro_cents are unique (the dedup loop in the route)."""
    _, Session = db_engine
    _, token = await _create_user_and_jwt(Session)

    async with _build_app(db_engine) as app, AsyncClient(
        transport=ASGITransport(app=app), base_url="http://t",
    ) as client:
        r1 = await client.post(
            "/account/topup-intent",
            json={"channel": "usdt-trc20", "amount_usd": 100.0},
            headers={"Authorization": f"Bearer {token}"},
        )
        r2 = await client.post(
            "/account/topup-intent",
            json={"channel": "usdt-trc20", "amount_usd": 100.0},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r1.status_code == 200 and r2.status_code == 200
    b1, b2 = r1.json(), r2.json()
    assert b1["expected_amount_micro_cents"] != b2["expected_amount_micro_cents"]
    assert b1["memo"] != b2["memo"]


@pytest.mark.asyncio
async def test_topup_intent_evm_returns_correct_address(db_engine):
    _, Session = db_engine
    _, token = await _create_user_and_jwt(Session)

    async with _build_app(db_engine) as app, AsyncClient(
        transport=ASGITransport(app=app), base_url="http://t",
    ) as client:
        resp = await client.post(
            "/account/topup-intent",
            json={"channel": "usdt-evm", "amount_usd": 50.0},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["channel"] == "usdt-evm"
    assert body["network"] == "bsc"  # default sub-chain
    assert body["address"] == "0xC862ff9Fd79D180950E546DBB8b108d5c9c38582"


@pytest.mark.asyncio
async def test_topup_intent_unsupported_channel(db_engine):
    _, Session = db_engine
    _, token = await _create_user_and_jwt(Session)

    async with _build_app(db_engine) as app, AsyncClient(
        transport=ASGITransport(app=app), base_url="http://t",
    ) as client:
        resp = await client.post(
            "/account/topup-intent",
            json={"channel": "alipay", "amount_usd": 10},
            headers={"Authorization": f"Bearer {token}"},
        )
    # Pydantic regex rejects this → 422 with our handler turning it into 400
    assert resp.status_code in (400, 422)


@pytest.mark.asyncio
async def test_topup_intent_requires_auth(db_engine):
    async with _build_app(db_engine) as app, AsyncClient(
        transport=ASGITransport(app=app), base_url="http://t",
    ) as client:
        resp = await client.post(
            "/account/topup-intent",
            json={"channel": "usdt-trc20", "amount_usd": 10},
        )
    assert resp.status_code == 401
