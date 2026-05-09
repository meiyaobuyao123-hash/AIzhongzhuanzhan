"""Doubao (Volcengine) public pricing page scraper — skeleton.

Pricing at https://www.volcengine.com/product/doubao
Tiered by input length (≤32K / 32-128K / 128-256K) so single-snapshot doesn't
fully model it. Until we can pull real billing via Volcengine RAM key, this
just raises PriceSourceError so manual review is the only path.
"""

from __future__ import annotations

from app.pricing.models import PriceSnapshot, PriceSourceError
from app.pricing.sources.base import PriceSource


class DoubaoWebSource(PriceSource):
    name = "doubao_web"
    description = "Scrapes Volcengine Doubao pricing (skeleton — tiered pricing)"
    URL = "https://www.volcengine.com/product/doubao"

    async def fetch_all(self) -> list[PriceSnapshot]:
        raise PriceSourceError(
            "Doubao scraper not yet implemented — input-tiered pricing requires "
            "Volcengine billing API (provide RAM key to upgrade to Tier 1)"
        )


__all__ = ["DoubaoWebSource"]
