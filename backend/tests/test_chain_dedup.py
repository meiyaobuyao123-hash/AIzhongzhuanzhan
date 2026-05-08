"""Dedup behavior: same tx_hash credited only once."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models.orm import BalanceTransaction, PaymentIntent, User
from app.payments.base import IncomingTx, match_and_credit


@pytest.mark.asyncio
async def test_second_credit_attempt_is_noop(db_session):
    """Once an intent has been credited, a second tx with the same tx_hash
    is recognized via the `tx_hash` lookup and silently skipped — no
    duplicate balance bump, no second BalanceTransaction."""
    user = User(email="d@x.com", email_verified=True, balance_micro_cents=0)
    db_session.add(user)
    await db_session.flush()
    intent = PaymentIntent(
        user_id=user.id,
        channel="usdt-trc20",
        amount_micro_cents=100_000_000,
        fee_micro_cents=1_500_000,
        credited_micro_cents=98_500_000,
        status="pending",
        receiver_address="TT24g41HLptouzxGycZxQKmWaTENK4K4HG",
        expected_amount_micro_cents=100_001_234,
        memo="1234",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db_session.add(intent)
    await db_session.flush()

    tx = IncomingTx(
        network="tron",
        tx_hash="dedupe_tx_001",
        from_address="from",
        to_address="TT24g41HLptouzxGycZxQKmWaTENK4K4HG",
        amount_micro_cents=100_001_234,
    )

    applied1 = await match_and_credit(tx, db_session)
    await db_session.commit()
    assert applied1 is True

    # Same tx, processed again
    applied2 = await match_and_credit(tx, db_session)
    await db_session.commit()
    assert applied2 is False

    # Balance still credited only once
    await db_session.refresh(user)
    assert user.balance_micro_cents == 98_500_000

    btxs = (await db_session.execute(select(BalanceTransaction))).scalars().all()
    assert len(btxs) == 1


@pytest.mark.asyncio
async def test_no_pending_intent_is_noop(db_session):
    """An incoming tx that doesn't match any pending intent → no credit, no error."""
    user = User(email="d@x.com", email_verified=True, balance_micro_cents=0)
    db_session.add(user)
    await db_session.flush()

    tx = IncomingTx(
        network="tron",
        tx_hash="orphan_tx",
        from_address="from",
        to_address="TT24g41HLptouzxGycZxQKmWaTENK4K4HG",
        amount_micro_cents=100_000_000,
    )
    applied = await match_and_credit(tx, db_session)
    assert applied is False

    btxs = (await db_session.execute(select(BalanceTransaction))).scalars().all()
    assert btxs == []


@pytest.mark.asyncio
async def test_unknown_network_skipped(db_session):
    tx = IncomingTx(
        network="dogecoin",
        tx_hash="x",
        from_address="a",
        to_address="b",
        amount_micro_cents=1,
    )
    applied = await match_and_credit(tx, db_session)
    assert applied is False


@pytest.mark.asyncio
async def test_multiple_pending_match_oldest(db_session):
    """If two pending intents have the same expected amount (theoretical race),
    the OLDEST is credited first."""
    user1 = User(email="a@x.com", email_verified=True, balance_micro_cents=0)
    user2 = User(email="b@x.com", email_verified=True, balance_micro_cents=0)
    db_session.add_all([user1, user2])
    await db_session.flush()

    common = dict(
        channel="usdt-trc20",
        amount_micro_cents=100_000_000,
        fee_micro_cents=1_500_000,
        credited_micro_cents=98_500_000,
        status="pending",
        expected_amount_micro_cents=100_001_234,
        memo="1234",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    older = PaymentIntent(user_id=user1.id, **common)
    db_session.add(older)
    await db_session.flush()

    # Newer intent (different user, same expected amount — collision case)
    newer = PaymentIntent(user_id=user2.id, **common)
    db_session.add(newer)
    await db_session.flush()

    tx = IncomingTx(
        network="tron",
        tx_hash="race_tx",
        from_address="f",
        to_address="t",
        amount_micro_cents=100_001_234,
    )
    applied = await match_and_credit(tx, db_session)
    await db_session.commit()
    assert applied is True

    await db_session.refresh(older)
    await db_session.refresh(newer)
    assert older.status == "paid"
    assert newer.status == "pending"
