"""DeepSeek public pricing page scraper — skeleton.

Their pricing is at https://api-docs.deepseek.com/quick_start/pricing
Page structure uses a Markdown-ish table; full parsing not yet implemented.
Raises PriceSourceError until done — checker will skip it gracefully.
"""

from __future__ import annotations

from app.pricing.models import PriceSnapshot, PriceSourceError
from app.pricing.sources.base import PriceSource


class DeepseekWebSource(PriceSource):
    name = "deepseek_web"
    description = "Scrapes api-docs.deepseek.com/quick_start/pricing (skeleton)"
    URL = "https://api-docs.deepseek.com/quick_start/pricing"

    async def fetch_all(self) -> list[PriceSnapshot]:
        # TODO: implement HTML parser. Fall through to "skip with warning"
        # until then — checker logs and continues.
        raise PriceSourceError(
            "DeepSeek scraper not yet implemented — manual review only"
        )


__all__ = ["DeepseekWebSource"]
