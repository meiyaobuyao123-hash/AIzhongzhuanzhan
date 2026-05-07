"""GET /v1/models — OpenAI-style model listing."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.models.orm import Model as ModelOrm

router = APIRouter(tags=["models"])


@router.get("/v1/models")
async def list_models(db: AsyncSession = Depends(get_db)) -> dict:
    rows = (
        await db.execute(
            select(ModelOrm).where(ModelOrm.enabled.is_(True)).order_by(ModelOrm.id)
        )
    ).scalars().all()

    now = int(time.time())
    return {
        "object": "list",
        "data": [
            {
                "id": m.model_id,
                "object": "model",
                "created": int(m.created_at.timestamp()) if m.created_at else now,
                "owned_by": m.provider,
                "context_window": m.context_window,
                "input_price_per_million_micro_cents": m.price_input_per_million,
                "output_price_per_million_micro_cents": m.price_output_per_million,
            }
            for m in rows
        ],
    }
