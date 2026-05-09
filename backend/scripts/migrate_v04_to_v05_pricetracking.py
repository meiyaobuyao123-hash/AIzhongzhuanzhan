"""v0.4 → v0.5: Price tracking schema migration.

Adds:
  - models columns: price_set_at, price_set_by, price_source_url
  - usage_logs column: price_version_id (FK)
  - new tables: model_price_history, price_anomalies
  - For each existing model, create a baseline history row (source='manual',
    notes='v0.5 baseline') so future scans have a "previous version" to diff against.

Idempotent. Run::

    python -m scripts.migrate_v04_to_v05_pricetracking
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import inspect, select, text

from app.db import SessionLocal, engine
from app.logging_config import configure_logging, logger
from app.models.orm import Base, Model, ModelPriceHistory

COLUMN_ADDITIONS = [
    ("models", "price_set_at", "DATETIME"),
    ("models", "price_set_by", "VARCHAR(128)"),
    ("models", "price_source_url", "VARCHAR(512)"),
    ("usage_logs", "price_version_id", "INTEGER"),
]


# Vendor pricing pages (used to seed price_source_url for first time)
VENDOR_PRICING_URL = {
    "anthropic": "https://www.anthropic.com/pricing",
    "openai":    "https://openai.com/api/pricing",
    "google":    "https://ai.google.dev/pricing",
}
# By-model overrides for non-USD-priced models we host
MODEL_PRICING_URL = {
    "deepseek-chat":              "https://api-docs.deepseek.com/quick_start/pricing",
    "deepseek-reasoner":          "https://api-docs.deepseek.com/quick_start/pricing",
    "minimax-text-01":            "https://platform.minimaxi.com/document/Price",
    "abab6.5s-chat":              "https://platform.minimaxi.com/document/Price",
    "abab6.5-chat":               "https://platform.minimaxi.com/document/Price",
    "doubao-1-5-pro-32k-250115":  "https://www.volcengine.com/product/doubao",
    "doubao-1-5-lite-32k-250115": "https://www.volcengine.com/product/doubao",
    "doubao-seed-1-6-250615":     "https://www.volcengine.com/product/doubao",
    "doubao-seed-1-6-flash-250828":   "https://www.volcengine.com/product/doubao",
    "doubao-1-5-thinking-pro-250415": "https://www.volcengine.com/product/doubao",
}


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


async def create_new_tables() -> None:
    """create_all is idempotent — only creates missing tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("migrate_created_new_tables")


async def seed_baseline_history() -> None:
    """For each existing model that has NO history row yet, create one.
    These rows represent "the price as of v0.5 launch", source='manual'."""
    now = datetime.now(timezone.utc)
    async with SessionLocal() as db:
        models = (await db.execute(select(Model))).scalars().all()
        for m in models:
            existing = (await db.execute(
                select(ModelPriceHistory.id).where(ModelPriceHistory.model_id == m.model_id)
            )).scalar_one_or_none()
            if existing is not None:
                logger.debug("migrate_skip_existing_history", model_id=m.model_id)
                continue

            url = MODEL_PRICING_URL.get(
                m.model_id, VENDOR_PRICING_URL.get(m.provider)
            )
            row = ModelPriceHistory(
                model_id=m.model_id,
                effective_at=now,
                price_input_per_million=m.price_input_per_million,
                price_output_per_million=m.price_output_per_million,
                price_cache_read_per_million=m.price_cache_read_per_million,
                price_cache_write_per_million=m.price_cache_write_per_million,
                currency=m.price_currency or "USD",
                source="manual",
                source_url=url,
                confirmed_by="migrate_v05_baseline",
                notes="v0.5 baseline — initial seed from existing models row",
            )
            db.add(row)

            # Also fill in the new metadata columns on models row
            m.price_set_at = now
            m.price_set_by = "migrate_v05_baseline"
            m.price_source_url = url

        await db.commit()
        logger.info("migrate_seeded_baseline_history", model_count=len(models))


async def main() -> None:
    configure_logging()
    logger.info("migrate_v04_to_v05_pricetracking_start")

    tables = await existing_tables()
    logger.info("migrate_existing_tables", tables=sorted(tables))

    await add_missing_columns()
    await create_new_tables()
    await seed_baseline_history()

    logger.info("migrate_v04_to_v05_pricetracking_done")


if __name__ == "__main__":
    asyncio.run(main())
