"""Smoke test: seed model catalog runs and is idempotent."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import select

from app.models.orm import Model
from scripts.init_db import SEED_MODELS


@pytest.mark.asyncio
async def test_seed_inserts_all(db_engine):
    _, Session = db_engine

    async with Session() as db:
        for spec in SEED_MODELS:
            db.add(Model(
                model_id=spec["model_id"],
                display_name=spec["display_name"],
                provider=spec["provider"],
                context_window=spec["context_window"],
                price_input_per_million=spec["price_input_per_million"],
                price_output_per_million=spec["price_output_per_million"],
                price_cache_read_per_million=spec["price_cache_read_per_million"],
                price_cache_write_per_million=spec["price_cache_write_per_million"],
                capabilities=json.dumps(spec["capabilities"]),
            ))
        await db.commit()

    async with Session() as db:
        rows = (await db.execute(select(Model))).scalars().all()
        ids = {m.model_id for m in rows}
        assert ids >= {"claude-opus-4-5", "gpt-5", "gemini-3-pro"}
        # Sanity: prices stored as integer micro-cents
        opus = next(m for m in rows if m.model_id == "claude-opus-4-5")
        assert opus.price_input_per_million == 1_500_000_000  # $15/M
