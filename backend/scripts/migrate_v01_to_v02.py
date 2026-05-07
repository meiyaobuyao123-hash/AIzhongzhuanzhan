"""Migrate an existing v0.1 SQLite database to v0.2 schema.

Idempotent: detects existing columns/tables and only adds what's missing.

Run::

    python -m scripts.migrate_v01_to_v02

For SQLite this uses raw ALTER TABLE statements (SQLAlchemy doesn't fully
abstract this on SQLite). For Postgres the same SQL works.

The migration:
  - users: + email_verified, display_name, avatar_url
           (password_hash already exists in v0.1 schema)
  - channels: + region, policy_no_training, policy_log_retention_days
  - usage_logs: + attempt_index, tried_channels
  - new tables: oauth_accounts, email_verifications, sessions
  - existing users without `email_verified` get marked verified
    (they were admin-created via CLI, trust them)
"""

from __future__ import annotations

import asyncio

from sqlalchemy import inspect, text

from app.db import SessionLocal, engine
from app.logging_config import configure_logging, logger
from app.models.orm import Base


COLUMN_ADDITIONS = [
    # (table, column, definition)
    ("users", "email_verified", "BOOLEAN NOT NULL DEFAULT 0"),
    ("users", "display_name", "VARCHAR(128)"),
    ("users", "avatar_url", "VARCHAR(512)"),
    ("channels", "region", "VARCHAR(64)"),
    ("channels", "policy_no_training", "BOOLEAN NOT NULL DEFAULT 1"),
    ("channels", "policy_log_retention_days", "INTEGER DEFAULT 30"),
    ("usage_logs", "attempt_index", "INTEGER NOT NULL DEFAULT 0"),
    ("usage_logs", "tried_channels", "TEXT"),
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


async def create_new_tables() -> None:
    """Use SQLAlchemy create_all for the new tables. It's idempotent — already-
    existing tables are skipped automatically."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("migrate_created_new_tables")


async def mark_existing_users_verified() -> None:
    """Users created in v0.1 via admin CLI are trusted (admin chose to add them).
    Backfill email_verified=1 for them."""
    async with SessionLocal() as db:
        result = await db.execute(
            text("UPDATE users SET email_verified = 1 WHERE email_verified = 0")
        )
        await db.commit()
        rowcount = result.rowcount or 0
        logger.info("migrate_backfill_email_verified", count=rowcount)


async def main() -> None:
    configure_logging()
    logger.info("migrate_v01_to_v02_start")

    tables = await existing_tables()
    logger.info("migrate_existing_tables", tables=sorted(tables))

    await add_missing_columns()
    await create_new_tables()
    await mark_existing_users_verified()

    logger.info("migrate_v01_to_v02_done")


if __name__ == "__main__":
    asyncio.run(main())
