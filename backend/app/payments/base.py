"""Chain-monitor abstract base + incoming-tx record + credit logic.

The flow:
  1. `ChainMonitor.fetch_new_incoming(state)` — chain-specific HTTP call,
     returns a list of `IncomingTx` since `state.last_block_height` (or
     last-tx-hash; depends on chain).
  2. `match_and_credit(tx, db)` — find a pending `payment_intent` whose
     `expected_amount_micro_cents == tx.amount_micro_cents` for the right
     network, mark paid, write a `BalanceTransaction(type='topup')`, bump the
     user's balance.
  3. Update `chain_monitor_state` so we don't re-scan the same range.

Dedupe is enforced by the unique index on `payment_intents.tx_hash`. Even if a
chain RPC double-delivers a transaction, the second `match_and_credit` will
fail-fast on the unique constraint and we log it as a benign event.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import logger
from app.models.orm import (
    BalanceTransaction,
    ChainMonitorState,
    PaymentIntent,
    User,
)


@dataclass(frozen=True)
class IncomingTx:
    """One on-chain USDT transfer we want to evaluate for matching."""

    network: str  # 'tron' / 'solana' / 'bsc' / 'polygon' / 'arbitrum' / 'ethereum'
    tx_hash: str
    from_address: str
    to_address: str
    amount_micro_cents: int  # USDT amount converted to our µ¢ (1 USDT = 100_000_000 µ¢)
    block_height: int | None = None
    block_time: datetime | None = None
    memo: str | None = None  # only TRC20/SOL might carry one; EVM does not
    raw: dict | None = None  # original RPC payload (useful for debugging/audit)


class ChainMonitor(ABC):
    """One concrete subclass per chain we watch."""

    network: str  # 'tron' / 'solana' / 'bsc' / 'polygon' / 'arbitrum' / 'ethereum'
    receive_address: str
    payment_channel: str  # PaymentIntent.channel ('usdt-trc20' / 'usdt-sol' / 'usdt-evm')

    @abstractmethod
    async def fetch_new_incoming(
        self, state: ChainMonitorState
    ) -> list[IncomingTx]:
        """Return new incoming USDT transfers since `state` cursor.

        Implementations should advance the state cursor _in this method_ when
        appropriate (e.g. set `state.last_block_height` to the highest block
        observed). The caller will commit afterward.
        """

    async def close(self) -> None:  # noqa: B027 — default no-op, subclasses override
        """Override to release HTTP clients etc. Default no-op."""
        return None


# Map evm sub-chain → PaymentIntent.network value we expect on intents
# (we use the granular network name, but match against payment_channel='usdt-evm')
EVM_NETWORKS = {"bsc", "polygon", "arbitrum", "ethereum"}


async def match_and_credit(tx: IncomingTx, db: AsyncSession) -> bool:
    """Try to match `tx` against a pending intent and credit the user.

    Returns True if a match was found and credit was applied. False otherwise
    (no matching intent / amount mismatch / already credited).

    The caller is responsible for committing the session.
    """
    # First short-circuit on tx_hash dedup: if any intent already has this hash,
    # skip re-processing.
    existing = (await db.execute(
        select(PaymentIntent).where(PaymentIntent.tx_hash == tx.tx_hash)
    )).scalar_one_or_none()
    if existing is not None:
        logger.debug(
            "chain_tx_already_credited",
            network=tx.network,
            tx_hash=tx.tx_hash,
            payment_intent_id=existing.id,
        )
        return False

    # Channel selector: TRC20/SOL go to their own channel; EVM-family share one.
    if tx.network == "tron":
        channel = "usdt-trc20"
    elif tx.network == "solana":
        channel = "usdt-sol"
    elif tx.network in EVM_NETWORKS:
        channel = "usdt-evm"
    else:
        logger.warning("chain_unknown_network", network=tx.network)
        return False

    # Find the pending intent: same channel + exact expected amount.
    # We do NOT match on receiver address here — the monitor already filters
    # for our receive_address, so any tx that gets here is destined for us.
    candidates = (await db.execute(
        select(PaymentIntent)
        .where(PaymentIntent.channel == channel)
        .where(PaymentIntent.status == "pending")
        .where(PaymentIntent.expected_amount_micro_cents == tx.amount_micro_cents)
        .order_by(PaymentIntent.created_at.asc())
    )).scalars().all()

    if not candidates:
        logger.info(
            "chain_no_matching_intent",
            network=tx.network,
            tx_hash=tx.tx_hash,
            amount_micro_cents=tx.amount_micro_cents,
        )
        return False

    # If multiple match same amount (extremely unlikely with 4-digit µ¢ memo
    # randomization), prefer the oldest pending — first come, first credit.
    intent = candidates[0]

    # Pull the user (we need to bump balance + maybe other tier counters)
    user = await db.get(User, intent.user_id)
    if user is None:
        logger.error(
            "chain_intent_orphan_user",
            tx_hash=tx.tx_hash,
            user_id=intent.user_id,
        )
        return False

    # Apply credit
    user.balance_micro_cents += intent.credited_micro_cents
    user.total_topped_up_micro_cents += intent.credited_micro_cents

    intent.status = "paid"
    intent.tx_hash = tx.tx_hash
    intent.network = tx.network
    intent.paid_at = datetime.now(timezone.utc)
    intent.external_ref = tx.tx_hash

    db.add(BalanceTransaction(
        user_id=user.id,
        type="topup",
        amount_micro_cents=intent.credited_micro_cents,
        balance_after_micro_cents=user.balance_micro_cents,
        related_payment_id=intent.id,
        description=f"USDT top-up via {tx.network} (tx {tx.tx_hash[:10]}…)",
    ))

    try:
        await db.flush()
    except IntegrityError:
        # Race: someone else just credited the same tx_hash in parallel.
        # SQLite + the unique partial index on tx_hash will raise.
        await db.rollback()
        logger.info(
            "chain_tx_double_credit_blocked",
            network=tx.network,
            tx_hash=tx.tx_hash,
        )
        return False

    logger.info(
        "chain_credit_applied",
        network=tx.network,
        tx_hash=tx.tx_hash,
        intent_id=intent.id,
        user_id=user.id,
        credited_micro_cents=intent.credited_micro_cents,
    )
    return True


__all__ = [
    "ChainMonitor",
    "IncomingTx",
    "EVM_NETWORKS",
    "match_and_credit",
]
