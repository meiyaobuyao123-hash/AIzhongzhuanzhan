"""MiniMax public pricing page scraper — skeleton.

Pricing at https://platform.minimaxi.com/document/Price (CN region).
Skeleton — raises PriceSourceError until implemented.
"""

from __future__ import annotations

from app.pricing.models import PriceSnapshot, PriceSourceError
from app.pricing.sources.base import PriceSource


class MinimaxWebSource(PriceSource):
    name = "minimax_web"
    description = "Scrapes platform.minimaxi.com/document/Price (skeleton)"
    URL = "https://platform.minimaxi.com/document/Price"

    async def fetch_all(self) -> list[PriceSnapshot]:
        raise PriceSourceError(
            "MiniMax scraper not yet implemented — manual review only"
        )


__all__ = ["MinimaxWebSource"]
