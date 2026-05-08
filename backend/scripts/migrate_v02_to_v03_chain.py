"""Migrate v0.2 → v0.3 schema (chain monitor + topup intent fields).

Idempotent. Detects existing columns/tables and only adds what's missing.

Changes:
  - payment_intents: + expected_amount_micro_cents, memo, expires_at, tx_hash UNIQUE
  - payment_intents.status CHECK accepts 'expired' (no rebuild — SQLite enforces
    only on row-level CHECK; new inserts naturally use the runtime CHECK from
    the live ORM. For strict enforcement we'd rebuild; v0.3 leaves as-is.)
  - new table: chain_monitor_state

Run::

    python -m scripts.migrate_v02_to_v03_chain
"""

from __future__ import annotations

import asyncio

from sqlalchemy import inspect, text

from app.db import engine
from app.logging_config import configure_logging, logger
from app.models.orm import Base

COLUMN_ADDITIONS = [
    # (table, column, definition)
    ("payment_intents", "expected_amount_micro_cents", "BIGINT"),
    ("payment_intents", "memo", "VARCHAR(16)"),
    ("payment_intents", "expires_at", "DATETIME"),
    ("payment_intents", "tx_hash", "VARCHAR(128)"),
]


async def existing_columns(table: str) -> set[str]:
    def _get(sync_conn):
        insp = inspect(sync_conn)
        try:
            return {c["name"] for c in insp.get_columns(table)}
        except Exception:
            return set()

    async with engine.begin() as conn:
        return await conn.run_sync(_get)


async def existing_tables() -> set[str]:
    def _get(sync_conn):
        insp = inspect(sync_conn)
        return set(insp.get_table_names())

    async with engine.begin() as conn:
        return await conn.run_sync(_get)


async def add_missing_columns() -> None:
    for table, col, defn in COLUMN_ADDITIONS:
        cols = await existing_columns(table)
        if col in cols:
            logger.debug("migrate_skip_existing_column", table=table, column=col)
            continue
        sql = f"ALTER TABLE {table} ADD COLUMN {col} {defn}"
        async with engine.begin() as conn:
            await conn.execute(text(sql))
        logger.info("migrate_added_column", table=table, column=col)


async def create_indexes_if_missing() -> None:
    """Add the new indexes idempotently (CREATE INDEX IF NOT EXISTS)."""
    async with engine.begin() as conn:
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_payment_pending_expected "
            "ON payment_intents(status, expected_amount_micro_cents)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_payment_intents_expires_at "
            "ON payment_intents(expires_at)"
        ))
        # Unique index on tx_hash — partial: only when set
        await conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_intents_tx_hash "
            "ON payment_intents(tx_hash) WHERE tx_hash IS NOT NULL"
        ))


async def create_new_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("migrate_created_new_tables")


async def main() -> None:
    configure_logging()
    logger.info("migrate_v02_to_v03_chain_start")

    tables = await existing_tables()
    logger.info("migrate_existing_tables", tables=sorted(tables))

    await add_missing_columns()
    await create_new_tables()
    await create_indexes_if_missing()

    logger.info("migrate_v02_to_v03_chain_done")


if __name__ == "__main__":
    asyncio.run(main())
