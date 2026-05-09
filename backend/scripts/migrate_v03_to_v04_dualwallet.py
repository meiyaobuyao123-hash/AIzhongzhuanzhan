"""v0.3 → v0.4: Dual-currency wallet schema migration.

Adds 4 columns and re-prices Chinese models in CNY-native units.

Idempotent — re-running is safe (uses inspect() checks).

Schema changes:
  - users:               + balance_cny_micro_yuan, total_topped_up_cny_micro_yuan
  - models:              + price_currency  (default 'USD')
  - payment_intents:     + currency        (default 'USD')
  - balance_transactions: + currency       (default 'USD')

Data migrations:
  - Chinese models (Doubao + MiniMax): convert price from USD-stored back to
    native CNY units; set price_currency='CNY'.
  - Existing user balance_micro_cents stays as USD wallet (semantic unchanged).
  - Existing payment_intents / balance_transactions get currency='USD'
    (back-compat default).

Run::

    python -m scripts.migrate_v03_to_v04_dualwallet
"""

from __future__ import annotations

import asyncio

from sqlalchemy import inspect, text

from app.db import engine
from app.logging_config import configure_logging, logger


COLUMN_ADDITIONS = [
    # (table, column, definition)
    ("users", "balance_cny_micro_yuan", "BIGINT NOT NULL DEFAULT 0"),
    ("users", "total_topped_up_cny_micro_yuan", "BIGINT NOT NULL DEFAULT 0"),
    ("models", "price_currency", "VARCHAR(3) NOT NULL DEFAULT 'USD'"),
    ("payment_intents", "currency", "VARCHAR(3) NOT NULL DEFAULT 'USD'"),
    ("balance_transactions", "currency", "VARCHAR(3) NOT NULL DEFAULT 'USD'"),
]


# Re-price Chinese models in CNY native units.
# Each tuple: (model_id, price_input_cny_micro_yuan, price_output_cny_micro_yuan,
#              cache_read_cny_micro_yuan or None, cache_write_cny_micro_yuan or None)
# 1 CNY = 100_000_000 µ¥.
CN_MODEL_PRICING = [
    # Doubao 1.5 Pro: ¥0.8 / ¥2 per M tokens
    ("doubao-1-5-pro-32k-250115",   80_000_000,   200_000_000, None, None),
    # Doubao 1.5 Lite: ¥0.3 / ¥0.6 per M tokens
    ("doubao-1-5-lite-32k-250115",  30_000_000,    60_000_000, None, None),
    # Doubao Seed 1.6: ¥0.8 / ¥8 per M tokens
    ("doubao-seed-1-6-250615",      80_000_000,   800_000_000, None, None),
    # Doubao Seed 1.6 Flash: ¥0.15 / ¥1.5 per M tokens
    ("doubao-seed-1-6-flash-250828", 15_000_000,   150_000_000, None, None),
    # Doubao 1.5 Thinking Pro: ¥2 / ¥8 per M tokens
    ("doubao-1-5-thinking-pro-250415", 200_000_000, 800_000_000, None, None),
    # MiniMax Text-01: ¥1 / ¥8 per M tokens
    ("minimax-text-01",            100_000_000,   800_000_000, None, None),
    # abab6.5s: ¥10 / ¥10 per M tokens
    ("abab6.5s-chat",            1_000_000_000, 1_000_000_000, None, None),
    # abab6.5: ¥30 / ¥30 per M tokens
    ("abab6.5-chat",             3_000_000_000, 3_000_000_000, None, None),
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


async def reprice_cn_models() -> None:
    """Re-store Chinese models with CNY-native prices and price_currency='CNY'."""
    async with engine.begin() as conn:
        for mid, p_in, p_out, p_cache_r, p_cache_w in CN_MODEL_PRICING:
            sets = [
                "price_currency = 'CNY'",
                f"price_input_per_million = {p_in}",
                f"price_output_per_million = {p_out}",
            ]
            if p_cache_r is not None:
                sets.append(f"price_cache_read_per_million = {p_cache_r}")
            if p_cache_w is not None:
                sets.append(f"price_cache_write_per_million = {p_cache_w}")
            sql = f"UPDATE models SET {', '.join(sets)} WHERE model_id = :mid"
            result = await conn.execute(text(sql), {"mid": mid})
            logger.info(
                "migrate_repriced_cn_model",
                model_id=mid, rowcount=result.rowcount or 0,
                price_input_cny=p_in / 100_000_000,
                price_output_cny=p_out / 100_000_000,
            )


async def main() -> None:
    configure_logging()
    logger.info("migrate_v03_to_v04_dualwallet_start")

    await add_missing_columns()
    await reprice_cn_models()

    logger.info("migrate_v03_to_v04_dualwallet_done")


if __name__ == "__main__":
    asyncio.run(main())
