"""EVM USDT monitor (BSC default): parsing + matching with mocked Etherscan-style API."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import respx
from httpx import Response

from app.models.orm import ChainMonitorState, PaymentIntent, User


BSCSCAN_BASE = "https://api.bscscan.com/api/"
RECEIVE = "0xC862ff9Fd79D180950E546DBB8b108d5c9c38582"
USDT_BSC = "0x55d398326f99059fF775485246999027B3197955"


def _bsc_response(items: list[dict]) -> dict:
    return {"status": "1", "message": "OK", "result": items}


def _bsc_tx(tx_hash: str, value_18dec: str, block_number: str = "100",
            to: str = RECEIVE, contract: str = USDT_BSC) -> dict:
    return {
        "blockNumber": block_number,
        "timeStamp": "1700000000",
        "hash": tx_hash,
        "from": "0xSenderXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "to": to,
        "contractAddress": contract,
        "value": value_18dec,
        "tokenName": "Tether USD",
        "tokenSymbol": "USDT",
        "tokenDecimal": "18",
    }


@pytest.mark.asyncio
@respx.mock
async def test_evm_parse_and_advance_cursor(db_session):
    from app.payments.evm import EvmMonitor

    state = ChainMonitorState(network="bsc", last_block_height=99)
    db_session.add(state)
    await db_session.flush()

    # 100 USDT on BSC = 100 * 10^18 = "100000000000000000000"
    items = [
        _bsc_tx("0xtx1", "100000000000000000000", block_number="200"),
        _bsc_tx("0xtx2",  "50000000000000000000", block_number="500"),
    ]
    respx.get(BSCSCAN_BASE).mock(return_value=Response(200, json=_bsc_response(items)))

    mon = EvmMonitor("bsc")
    txs = await mon.fetch_new_incoming(state)
    assert len(txs) == 2
    assert txs[0].tx_hash == "0xtx1"
    # 100 USDT = 10_000_000_000 µ¢
    assert txs[0].amount_micro_cents == 10_000_000_000
    assert txs[1].amount_micro_cents ==  5_000_000_000
    # Cursor advanced to highest seen block
    assert state.last_block_height == 500
    await mon.close()


@pytest.mark.asyncio
@respx.mock
async def test_evm_match_and_credit(db_session):
    from app.payments.base import match_and_credit
    from app.payments.evm import EvmMonitor

    user = User(email="e@x.com", email_verified=True, balance_micro_cents=0)
    db_session.add(user)
    await db_session.flush()
    intent = PaymentIntent(
        user_id=user.id,
        channel="usdt-evm",
        amount_micro_cents=10_000_000_000,
        fee_micro_cents=5_000_000,
        credited_micro_cents=9_995_000_000,
        status="pending",
        receiver_address=RECEIVE,
        expected_amount_micro_cents=10_000_000_000,
        memo="0000",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db_session.add(intent)
    await db_session.flush()

    state = ChainMonitorState(network="bsc")
    db_session.add(state)
    await db_session.flush()

    items = [_bsc_tx("0xmatch", "100000000000000000000", block_number="1")]
    respx.get(BSCSCAN_BASE).mock(return_value=Response(200, json=_bsc_response(items)))

    mon = EvmMonitor("bsc")
    txs = await mon.fetch_new_incoming(state)
    assert len(txs) == 1
    applied = await match_and_credit(txs[0], db_session)
    await db_session.commit()
    assert applied is True

    await db_session.refresh(user)
    await db_session.refresh(intent)
    assert intent.status == "paid"
    assert user.balance_micro_cents == 9_995_000_000
    await mon.close()


@pytest.mark.asyncio
@respx.mock
async def test_evm_no_transactions_message(db_session):
    """Etherscan returns status='0' + 'No transactions found' on empty cursor."""
    from app.payments.evm import EvmMonitor

    state = ChainMonitorState(network="bsc", last_block_height=999_999)
    db_session.add(state)
    await db_session.flush()

    respx.get(BSCSCAN_BASE).mock(return_value=Response(200, json={
        "status": "0", "message": "No transactions found", "result": [],
    }))

    mon = EvmMonitor("bsc")
    txs = await mon.fetch_new_incoming(state)
    assert txs == []
    await mon.close()


@pytest.mark.asyncio
@respx.mock
async def test_evm_filters_other_recipients(db_session):
    from app.payments.evm import EvmMonitor

    state = ChainMonitorState(network="bsc")
    db_session.add(state)
    await db_session.flush()

    items = [
        _bsc_tx("0xother", "1000000000000000000", to="0xOtherWallet"),
        _bsc_tx("0xours",  "2000000000000000000"),
    ]
    respx.get(BSCSCAN_BASE).mock(return_value=Response(200, json=_bsc_response(items)))

    mon = EvmMonitor("bsc")
    txs = await mon.fetch_new_incoming(state)
    assert len(txs) == 1
    assert txs[0].tx_hash == "0xours"
    await mon.close()


def test_evm_invalid_chain_raises():
    from app.payments.evm import EvmMonitor
    with pytest.raises(ValueError, match="Unknown EVM chain"):
        EvmMonitor("dogecoin")
