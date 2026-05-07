"""v0.1 router: model_id → first-priority channel (single-channel-per-provider).

For v0.3+ this becomes 4-layer (tier filter → model filter → health filter →
weighted pick). See docs/routing-strategy.md.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ModelNotFound, NoChannelAvailable
from app.models.orm import Channel, Model


async def find_model(model_id: str, db: AsyncSession) -> Model:
    row = await db.execute(
        select(Model).where(Model.model_id == model_id, Model.enabled.is_(True))
    )
    model = row.scalar_one_or_none()
    if not model:
        raise ModelNotFound(f"Model not found: {model_id}", param="model")
    return model


async def route(model: Model, db: AsyncSession) -> Channel:
    """Pick the highest-priority enabled channel for this model's provider that
    lists this model in its `models` JSON array.

    v0.1: no cooldown, no weighted random. Just deterministic priority desc.
    """
    rows = await db.execute(
        select(Channel)
        .where(Channel.provider == model.provider)
        .where(Channel.enabled.is_(True))
        .order_by(Channel.priority.desc(), Channel.id.asc())
    )
    now = datetime.now(timezone.utc)
    for ch in rows.scalars():
        # check model in this channel's whitelist
        try:
            ch_models = json.loads(ch.models)
        except (json.JSONDecodeError, TypeError):
            continue
        if model.model_id not in ch_models:
            continue
        # honour cooldown_until even though v0.1 doesn't set it
        if ch.cooldown_until and ch.cooldown_until.replace(tzinfo=timezone.utc) > now:
            continue
        return ch

    raise NoChannelAvailable(
        f"No upstream channel available for model {model.model_id}"
    )
