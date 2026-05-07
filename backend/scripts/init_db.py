"""Initialise the database schema and seed an initial model catalog.

Idempotent: safe to run multiple times. Only creates missing tables and only
inserts catalog rows that don't already exist.

Usage::

    python -m scripts.init_db
"""

from __future__ import annotations

import asyncio
import json

from sqlalchemy import select

from app.db import SessionLocal, engine
from app.logging_config import configure_logging, logger
from app.models.orm import Base, Model

# Seed model catalog. Prices are micro-cents per 1M tokens.
# 1 USD = 100_000_000 micro-cents → $15/M = 1_500_000_000.
# These are *placeholder defaults*; user should update via `prism-admin model add`.
SEED_MODELS: list[dict] = [
    # Anthropic
    {
        "model_id": "claude-opus-4-5",
        "display_name": "Claude Opus 4.5",
        "provider": "anthropic",
        "context_window": 200_000,
        "price_input_per_million": 1_500_000_000,         # $15
        "price_output_per_million": 7_500_000_000,        # $75
        "price_cache_read_per_million": 150_000_000,      # $1.5
        "price_cache_write_per_million": 1_875_000_000,   # $18.75
        "capabilities": ["streaming", "tool-use", "vision", "cache"],
    },
    {
        "model_id": "claude-sonnet-4-5",
        "display_name": "Claude Sonnet 4.5",
        "provider": "anthropic",
        "context_window": 200_000,
        "price_input_per_million": 300_000_000,           # $3
        "price_output_per_million": 1_500_000_000,        # $15
        "price_cache_read_per_million": 30_000_000,       # $0.3
        "price_cache_write_per_million": 375_000_000,     # $3.75
        "capabilities": ["streaming", "tool-use", "vision", "cache"],
    },
    {
        "model_id": "claude-haiku-4-5",
        "display_name": "Claude Haiku 4.5",
        "provider": "anthropic",
        "context_window": 200_000,
        "price_input_per_million": 80_000_000,            # $0.8
        "price_output_per_million": 400_000_000,          # $4
        "price_cache_read_per_million": 8_000_000,        # $0.08
        "price_cache_write_per_million": 100_000_000,     # $1
        "capabilities": ["streaming", "tool-use", "cache"],
    },
    # OpenAI (placeholder pricing — update when user provides real catalog)
    {
        "model_id": "gpt-5",
        "display_name": "GPT-5",
        "provider": "openai",
        "context_window": 400_000,
        "price_input_per_million": 800_000_000,           # $8
        "price_output_per_million": 3_200_000_000,        # $32
        "price_cache_read_per_million": 80_000_000,       # $0.8
        "price_cache_write_per_million": None,
        "capabilities": ["streaming", "tool-use", "vision", "reasoning"],
    },
    {
        "model_id": "gpt-5-mini",
        "display_name": "GPT-5 mini",
        "provider": "openai",
        "context_window": 400_000,
        "price_input_per_million": 120_000_000,           # $1.2
        "price_output_per_million": 480_000_000,          # $4.8
        "price_cache_read_per_million": 12_000_000,
        "price_cache_write_per_million": None,
        "capabilities": ["streaming", "tool-use"],
    },
    # Google
    {
        "model_id": "gemini-3-pro",
        "display_name": "Gemini 3 Pro",
        "provider": "google",
        "context_window": 2_000_000,
        "price_input_per_million": 250_000_000,           # $2.5
        "price_output_per_million": 1_000_000_000,        # $10
        "price_cache_read_per_million": 25_000_000,
        "price_cache_write_per_million": None,
        "capabilities": ["streaming", "tool-use", "vision", "long-context"],
    },
    {
        "model_id": "gemini-3-flash",
        "display_name": "Gemini 3 Flash",
        "provider": "google",
        "context_window": 1_000_000,
        "price_input_per_million": 30_000_000,            # $0.3
        "price_output_per_million": 120_000_000,          # $1.2
        "price_cache_read_per_million": 3_000_000,
        "price_cache_write_per_million": None,
        "capabilities": ["streaming", "tool-use"],
    },
]


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("schema_created")


async def seed_models() -> None:
    async with SessionLocal() as db:
        for spec in SEED_MODELS:
            existing = await db.execute(
                select(Model).where(Model.model_id == spec["model_id"])
            )
            if existing.scalar_one_or_none():
                logger.debug("model_seed_skip", model_id=spec["model_id"])
                continue
            model = Model(
                model_id=spec["model_id"],
                display_name=spec["display_name"],
                provider=spec["provider"],
                context_window=spec["context_window"],
                price_input_per_million=spec["price_input_per_million"],
                price_output_per_million=spec["price_output_per_million"],
                price_cache_read_per_million=spec["price_cache_read_per_million"],
                price_cache_write_per_million=spec["price_cache_write_per_million"],
                capabilities=json.dumps(spec["capabilities"]),
            )
            db.add(model)
            logger.info("model_seed_add", model_id=spec["model_id"])
        await db.commit()


async def main() -> None:
    configure_logging()
    await create_tables()
    await seed_models()
    logger.info("init_db_done")


if __name__ == "__main__":
    asyncio.run(main())
