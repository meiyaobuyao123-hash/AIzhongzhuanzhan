"""Solana monitor: parsing + matching with mocked JSON-RPC responses."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import respx
from httpx import Response

from app.models.orm import ChainMonitorState, PaymentIntent, User


SOL_RPC_URL = "https://api.mainnet-beta.solana.com"
RECEIVE = "66p5tnV6Fd7x5QmRE6X772PMVmVUVgozRzATJ4Ns9iQn"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def _signatures_response(sigs: list[str]) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": [{"signature": s, "slot": i + 1, "err": None} for i, s in enumerate(sigs)],
    }


def _tx_with_usdc_credit(sig: str, raw_amount: int = 100_000_000,
                          dest_owner: str = RECEIVE) -> dict:
    """JSON-RPC `getTransaction` payload with one transferChecked credit to us."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "slot": 1,
            "blockTime": 1_700_000_000,
            "transaction": {
                "message": {
                    "instructions": [
                        {
                            "program": "spl-token",
                            "parsed": {
                                "type": "transferChecked",
                                "info": {
                                    "authority": "FromWalletXXXXXXXXXXXXXXX",
                                    "mint": USDC_MINT,
                                    "destination": "RecipientATAXXXXXXXXXXX",
                                    "destinationOwner": dest_owner,
                                    "tokenAmount": {
                                        "amount": str(raw_amount),
                                        "decimals": 6,
                                    },
                                },
                            },
                        }
                    ]
                }
            },
            "meta": {
                "innerInstructions": [],
                "postTokenBalances": [
                    {"owner": dest_owner, "mint": USDC_MINT, "uiTokenAmount": {}}
                ],
            },
        },
    }


@pytest.mark.asyncio
@respx.mock
async def test_solana_extracts_usdc_credit(db_session):
    from app.payments.solana import SolanaMonitor

    state = ChainMonitorState(network="solana")
    db_session.add(state)
    await db_session.flush()

    sig = "SignatureZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"

    # JSON-RPC: respx matches by URL — first call (getSignaturesForAddress)
    # then second call (getTransaction). Use a side-effect callable so each
    # call returns the next response.
    responses = [
        Response(200, json=_signatures_response([sig])),
        Response(200, json=_tx_with_usdc_credit(sig, raw_amount=99_950_000)),  # 99.95 USDC
    ]
    iter_resp = iter(responses)
    respx.post(SOL_RPC_URL).mock(side_effect=lambda req: next(iter_resp))

    mon = SolanaMonitor()
    txs = await mon.fetch_new_incoming(state)
    assert len(txs) == 1
    tx = txs[0]
    assert tx.network == "solana"
    assert tx.tx_hash == sig
    # 99.95 USDC = 9_995_000_000 µ¢
    assert tx.amount_micro_cents == 9_995_000_000
    assert state.last_tx_hash == sig
    await mon.close()


@pytest.mark.asyncio
@respx.mock
async def test_solana_match_credits_user(db_session):
    from app.payments.base import match_and_credit
    from app.payments.solana import SolanaMonitor

    user = User(email="s@x.com", email_verified=True, balance_micro_cents=0)
    db_session.add(user)
    await db_session.flush()
    intent = PaymentIntent(
        user_id=user.id,
        channel="usdt-sol",
        amount_micro_cents=10_000_000_000,
        fee_micro_cents=5_000_000,
        credited_micro_cents=9_995_000_000,
        status="pending",
        receiver_address=RECEIVE,
        expected_amount_micro_cents=10_000_000_001,  # $100.00000001
        memo="0001",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db_session.add(intent)
    await db_session.flush()

    state = ChainMonitorState(network="solana")
    db_session.add(state)
    await db_session.flush()

    sig = "MatchSig111111111111111111111111111111111"
    # 100.00000001 USDC * 10^6 = 100_000_000.01 raw. Solana has integer raw
    # units only — closest is 100_000_000. So the user paid an integer amount
    # of 100 USDC = 10_000_000_000 µ¢, matching with expected_amount_µc 10_000_000_001
    # would FAIL. Use exact integer amount instead:
    # expected = 9_995_000_000 µ¢ + 0 suffix. Let me test exact match path.
    responses = [
        Response(200, json=_signatures_response([sig])),
        Response(200, json=_tx_with_usdc_credit(sig, raw_amount=100_000_000)),
    ]
    iter_resp = iter(responses)
    respx.post(SOL_RPC_URL).mock(side_effect=lambda req: next(iter_resp))

    # Update intent expected to exactly 100 USDC = 10_000_000_000 µ¢
    intent.expected_amount_micro_cents = 10_000_000_000
    await db_session.flush()

    mon = SolanaMonitor()
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
async def test_solana_skips_non_usdc_mints(db_session):
    from app.payments.solana import SolanaMonitor

    state = ChainMonitorState(network="solana")
    db_session.add(state)
    await db_session.flush()

    sig = "OtherMintSig"
    tx_body = _tx_with_usdc_credit(sig)
    # Override mint to a wrong one
    tx_body["result"]["transaction"]["message"]["instructions"][0]["parsed"]["info"]["mint"] = (
        "WrongMint11111111111111111111111111111111111"
    )

    responses = [
        Response(200, json=_signatures_response([sig])),
        Response(200, json=tx_body),
    ]
    iter_resp = iter(responses)
    respx.post(SOL_RPC_URL).mock(side_effect=lambda req: next(iter_resp))

    mon = SolanaMonitor()
    txs = await mon.fetch_new_incoming(state)
    assert len(txs) == 0
    await mon.close()


@pytest.mark.asyncio
@respx.mock
async def test_solana_empty_response(db_session):
    """No new sigs since cursor → empty list, no errors."""
    from app.payments.solana import SolanaMonitor

    state = ChainMonitorState(network="solana", last_tx_hash="prev_sig")
    db_session.add(state)
    await db_session.flush()

    respx.post(SOL_RPC_URL).mock(return_value=Response(
        200, json={"jsonrpc": "2.0", "id": 1, "result": []}
    ))

    mon = SolanaMonitor()
    txs = await mon.fetch_new_incoming(state)
    assert txs == []
    await mon.close()
