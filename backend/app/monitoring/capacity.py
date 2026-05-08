"""Capacity alert loop — placeholder. Filled in during C4 stage.

Exports `start_capacity_loop()` so the lifespan in `app.main` can import it
even before the real implementation lands.
"""

from __future__ import annotations

import asyncio


async def start_capacity_loop() -> asyncio.Task | None:
    """C4 placeholder. Returns None — lifespan handles None gracefully."""
    return None
