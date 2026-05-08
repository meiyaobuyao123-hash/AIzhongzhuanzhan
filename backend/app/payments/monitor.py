"""Async polling loop + monitor factory.

`monitor_loop(monitor)` runs forever:
  - load (or create) the `chain_monitor_state` row for the network
  - call `monitor.fetch_new_incoming(state)`
  - for each incoming tx, call `match_and_credit`
  - commit the session
  - sleep `settings.chain_poll_interval_s` seconds, with exponential backoff
    on consecutive failures (capped at 5 minutes)
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import record_audit
from app.config import settings
from app.db import SessionLocal
from app.logging_config import logger
from app.models.orm import ChainMonitorState
from app.payments.base import ChainMonitor, match_and_credit


def build_monitor(name: str) -> ChainMonitor:
    """name ∈ {'tron', 'solana', 'evm', 'bsc', 'polygon', 'arbitrum', 'ethereum'}."""
    if name == "tron":
        from app.payments.tron import TronMonitor
        return TronMonitor()
    if name == "solana":
        from app.payments.solana import SolanaMonitor
        return SolanaMonitor()
    if name == "evm":
        from app.payments.evm import EvmMonitor
        return EvmMonitor()  # default sub-chain from settings
    if name in ("bsc", "polygon", "arbitrum", "ethereum"):
        from app.payments.evm import EvmMonitor
        return EvmMonitor(chain=name)
    raise ValueError(f"Unknown chain monitor: {name}")


async def _load_state(db: AsyncSession, network: str) -> ChainMonitorState:
    state = await db.get(ChainMonitorState, network)
    if state is None:
        state = ChainMonitorState(network=network)
        db.add(state)
        await db.flush()
    return state


async def _tick(monitor: ChainMonitor) -> int:
    """One iteration. Returns the number of credits applied (for testing)."""
    credits = 0
    async with SessionLocal() as db:
        state = await _load_state(db, monitor.network)
        try:
            txs = await monitor.fetch_new_incoming(state)
        except Exception as exc:
            state.consecutive_failures = (state.consecutive_failures or 0) + 1
            state.last_error = str(exc)[:512]
            await db.commit()
            logger.error(
                "chain_fetch_failed",
                network=monitor.network,
                error=str(exc),
                consecutive_failures=state.consecutive_failures,
            )
            raise

        # Reset failure counter on success
        state.consecutive_failures = 0
        state.last_error = None
        state.last_scanned_at = datetime.now(timezone.utc)

        for tx in txs:
            try:
                applied = await match_and_credit(tx, db)
                if applied:
                    credits += 1
            except Exception as exc:
                logger.warning(
                    "chain_credit_failed",
                    network=monitor.network,
                    tx_hash=tx.tx_hash,
                    error=str(exc),
                )
                await record_audit(
                    db, actor="chain-monitor", action="topup.credit_failed",
                    target=tx.tx_hash,
                    payload={
                        "network": monitor.network,
                        "amount_micro_cents": tx.amount_micro_cents,
                        "error": str(exc),
                    },
                )

        await db.commit()
    return credits


async def monitor_loop(monitor: ChainMonitor) -> None:
    """Run forever. Cooperatively cancellable."""
    base = max(5, settings.chain_poll_interval_s)
    backoff_max = 300
    fail_streak = 0

    logger.info("chain_monitor_starting", network=monitor.network)
    try:
        while True:
            try:
                credits = await _tick(monitor)
                fail_streak = 0
                if credits:
                    logger.info(
                        "chain_monitor_credits_applied",
                        network=monitor.network,
                        credits=credits,
                    )
                await asyncio.sleep(base)
            except asyncio.CancelledError:
                raise
            except Exception:
                fail_streak += 1
                # Exponential backoff capped at 5min
                wait = min(base * (2 ** fail_streak), backoff_max)
                logger.warning(
                    "chain_monitor_backoff",
                    network=monitor.network,
                    fail_streak=fail_streak,
                    sleep_s=wait,
                )
                await asyncio.sleep(wait)
    finally:
        try:
            await monitor.close()
        except Exception as exc:
            logger.warning("chain_monitor_close_failed", error=str(exc))
        logger.info("chain_monitor_stopped", network=monitor.network)


def parse_chain_list(raw: str) -> list[str]:
    """Parse 'tron,solana,evm' env-style into a clean list, stripping blanks."""
    if not raw:
        return []
    return [c.strip() for c in raw.split(",") if c.strip()]


async def start_all_monitors() -> list[asyncio.Task]:
    """Spawn one task per configured chain. Returns list for cancel-on-shutdown."""
    chains = parse_chain_list(settings.chain_monitors)
    tasks: list[asyncio.Task] = []
    for name in chains:
        try:
            mon = build_monitor(name)
        except Exception as exc:
            logger.error("chain_monitor_build_failed", name=name, error=str(exc))
            continue
        task = asyncio.create_task(monitor_loop(mon), name=f"monitor-{name}")
        tasks.append(task)
    logger.info(
        "chain_monitors_started",
        count=len(tasks),
        chains=[t.get_name() for t in tasks],
    )
    return tasks


async def cancel_tasks(tasks: list[asyncio.Task]) -> None:
    for t in tasks:
        t.cancel()
    for t in tasks:
        try:
            await t
        except (asyncio.CancelledError, Exception):
            pass


# Re-exports for callers who only need the top-level helpers
__all__ = [
    "build_monitor",
    "monitor_loop",
    "start_all_monitors",
    "cancel_tasks",
    "parse_chain_list",
    "_tick",
]


# Pretty-print state row, used by CLI inspect command
def state_to_dict(s: ChainMonitorState) -> dict:
    return {
        "network": s.network,
        "last_block_height": s.last_block_height,
        "last_tx_hash": s.last_tx_hash,
        "last_scanned_at": s.last_scanned_at.isoformat() if s.last_scanned_at else None,
        "consecutive_failures": s.consecutive_failures,
        "last_error": s.last_error,
    }


def dump_state_pretty(s: ChainMonitorState) -> str:
    return json.dumps(state_to_dict(s), indent=2)
