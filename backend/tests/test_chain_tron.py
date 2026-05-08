"""TRC20 monitor: parsing + matching with mocked TronGrid responses."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import respx
from httpx import Response
from sqlalchemy import select

from app.models.orm import (
    BalanceTransaction,
    ChainMonitorState,
    PaymentIntent,
    User,
)


# ─── Helpers ────────────────────────────────────────────────────────────────


async def _seed_pending_intent(db_session, user_email="t@x.com",
                                expected_µc=10_000_001_234, channel="usdt-trc20"):
    user = User(email=user_email, email_verified=True, balance_micro_cents=0)
    db_session.add(user)
    await db_session.flush()
    intent = PaymentIntent(
        user_id=user.id,
        channel=channel,
        amount_micro_cents=10_000_000_000,  # $100
        fee_micro_cents=150_000_000,        # $1.50 (1.5%)
        credited_micro_cents=9_850_000_000,  # $98.50
        status="pending",
        receiver_address="TT24g41HLptouzxGycZxQKmWaTENK4K4HG",
        expected_amount_micro_cents=expected_µc,
        memo="1234",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db_session.add(intent)
    await db_session.flush()
    return user, intent


def _trongrid_response(value_units: str, tx_hash: str = "abc123",
                       to: str = "TT24g41HLptouzxGycZxQKmWaTENK4K4HG",
                       block_ts_ms: int = 1_700_000_000_000) -> dict:
    return {
        "success": True,
        "data": [
            {
                "transaction_id": tx_hash,
                "block_timestamp": block_ts_ms,
                "from": "TFakeSenderXXXXXXXXXXXXXXXXXXXXXX",
                "to": to,
                "value": value_units,
                "token_info": {
                    "address": "TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8",
                    "symbol": "USDT",
                    "decimals": 6,
                },
            }
        ],
    }


# ─── Tests ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_tron_parse_and_credit(db_session):
    """A TronGrid response with a matching amount → user balance bumped."""
    from app.payments.base import match_and_credit
    from app.payments.tron import TronMonitor

    user, intent = await _seed_pending_intent(
        db_session, expected_µc=10_000_001_234,  # $100.00001234
    )
    state = ChainMonitorState(network="tron")
    db_session.add(state)
    await db_session.flush()

    # value_units = 100.00001234 USDT * 10^6 = 100_000_012 raw
    respx.get(
        "https://api.trongrid.io/v1/accounts/TT24g41HLptouzxGycZxQKmWaTENK4K4HG/transactions/trc20"
    ).mock(return_value=Response(200, json=_trongrid_response(
        value_units="100000012",  # = 100.000012 USDT (= 10_000_001_200 µ¢)
        tx_hash="tron_tx_abc",
    )))

    mon = TronMonitor()
    txs = await mon.fetch_new_incoming(state)
    assert len(txs) == 1
    tx = txs[0]
    assert tx.tx_hash == "tron_tx_abc"
    # Round-trip µ¢
    assert tx.amount_micro_cents == 10_000_001_200

    # The seeded intent expected 10_000_001_234. Slight mismatch — should NOT credit.
    applied = await match_and_credit(tx, db_session)
    assert applied is False
    assert user.balance_micro_cents == 0
    await mon.close()


@pytest.mark.asyncio
@respx.mock
async def test_tron_exact_match_credits_user(db_session):
    """Exact amount match → credit applied, intent paid, BalanceTransaction written."""
    from app.payments.base import match_and_credit
    from app.payments.tron import TronMonitor

    user, intent = await _seed_pending_intent(
        db_session, expected_µc=10_000_001_200,  # = 100.000012 USDT in µ¢
    )
    state = ChainMonitorState(network="tron")
    db_session.add(state)
    await db_session.flush()

    respx.get(
        "https://api.trongrid.io/v1/accounts/TT24g41HLptouzxGycZxQKmWaTENK4K4HG/transactions/trc20"
    ).mock(return_value=Response(200, json=_trongrid_response(
        value_units="100000012",
        tx_hash="tron_tx_match",
    )))

    mon = TronMonitor()
    txs = await mon.fetch_new_incoming(state)
    assert len(txs) == 1

    applied = await match_and_credit(txs[0], db_session)
    await db_session.commit()
    assert applied is True

    await db_session.refresh(intent)
    await db_session.refresh(user)
    assert intent.status == "paid"
    assert intent.tx_hash == "tron_tx_match"
    assert intent.paid_at is not None
    assert user.balance_micro_cents == 9_850_000_000
    assert user.total_topped_up_micro_cents == 9_850_000_000

    # BalanceTransaction row written
    btx = (await db_session.execute(select(BalanceTransaction))).scalar_one()
    assert btx.type == "topup"
    assert btx.amount_micro_cents == 9_850_000_000
    assert btx.balance_after_micro_cents == 9_850_000_000

    await mon.close()


@pytest.mark.asyncio
@respx.mock
async def test_tron_filters_other_contracts_and_recipients(db_session):
    """Transactions to other addresses or other tokens are ignored."""
    from app.payments.tron import TronMonitor

    state = ChainMonitorState(network="tron")
    db_session.add(state)
    await db_session.flush()

    body = {
        "success": True,
        "data": [
            # Wrong contract
            {
                "transaction_id": "wrong_token",
                "block_timestamp": 1,
                "from": "f", "to": "TT24g41HLptouzxGycZxQKmWaTENK4K4HG",
                "value": "1000000",
                "token_info": {"address": "TOTHERTOKEN0000000000000000", "decimals": 6},
            },
            # Wrong recipient
            {
                "transaction_id": "wrong_to",
                "block_timestamp": 2,
                "from": "f", "to": "TOtherWalletXXXXX",
                "value": "1000000",
                "token_info": {"address": "TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8", "decimals": 6},
            },
            # Good
            {
                "transaction_id": "good_one",
                "block_timestamp": 3,
                "from": "f", "to": "TT24g41HLptouzxGycZxQKmWaTENK4K4HG",
                "value": "1000000",
                "token_info": {"address": "TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8", "decimals": 6},
            },
        ],
    }
    respx.get(
        "https://api.trongrid.io/v1/accounts/TT24g41HLptouzxGycZxQKmWaTENK4K4HG/transactions/trc20"
    ).mock(return_value=Response(200, json=body))

    mon = TronMonitor()
    txs = await mon.fetch_new_incoming(state)
    assert len(txs) == 1
    assert txs[0].tx_hash == "good_one"
    await mon.close()


@pytest.mark.asyncio
@respx.mock
async def test_tron_advances_cursor_after_fetch(db_session):
    """After a successful fetch, last_block_height = highest seen block_timestamp."""
    from app.payments.tron import TronMonitor

    state = ChainMonitorState(network="tron", last_block_height=1_000)
    db_session.add(state)
    await db_session.flush()

    body = {
        "success": True,
        "data": [
            {
                "transaction_id": "x", "block_timestamp": 5_000,
                "from": "f", "to": "TT24g41HLptouzxGycZxQKmWaTENK4K4HG",
                "value": "1000000",
                "token_info": {"address": "TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8", "decimals": 6},
            },
            {
                "transaction_id": "y", "block_timestamp": 3_000,
                "from": "f", "to": "TT24g41HLptouzxGycZxQKmWaTENK4K4HG",
                "value": "2000000",
                "token_info": {"address": "TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8", "decimals": 6},
            },
        ],
    }
    respx.get(
        "https://api.trongrid.io/v1/accounts/TT24g41HLptouzxGycZxQKmWaTENK4K4HG/transactions/trc20"
    ).mock(return_value=Response(200, json=body))

    mon = TronMonitor()
    await mon.fetch_new_incoming(state)
    assert state.last_block_height == 5_000
    await mon.close()
