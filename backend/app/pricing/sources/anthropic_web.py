"""Anthropic public pricing page scraper.

Fetches https://www.anthropic.com/pricing, regex-extracts the model rows,
returns PriceSnapshots for each model we map to a Prism model_id.

If the page HTML changes shape and parsing fails to find any of our mapped
models, we raise PriceSourceError — checker logs + skips, rather than
silently writing zeros.
"""

from __future__ import annotations

import re

import httpx

from app.pricing.models import PriceSnapshot, PriceSourceError
from app.pricing.sources.base import PriceSource

# Map "vendor's display name on pricing page" → our model_id
ANTHROPIC_NAME_MAP = {
    "claude opus 4.5":  "claude-opus-4-5",
    "claude opus 4.6":  "claude-opus-4-6",
    "claude opus 4.7":  "claude-opus-4-7",
    "claude sonnet 4.5": "claude-sonnet-4-5",
    "claude sonnet 4.6": "claude-sonnet-4-6",
    "claude haiku 4.5": "claude-haiku-4-5",
}


class AnthropicWebSource(PriceSource):
    name = "anthropic_web"
    description = "Scrapes anthropic.com/pricing"
    URL = "https://www.anthropic.com/pricing"

    async def fetch_all(self) -> list[PriceSnapshot]:
        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
                resp = await c.get(self.URL, headers={"User-Agent": "PrismPriceMonitor/0.5"})
            resp.raise_for_status()
            html = resp.text
        except httpx.HTTPError as exc:
            raise PriceSourceError(f"Anthropic page fetch failed: {exc}") from exc

        snapshots: list[PriceSnapshot] = []

        # Anthropic's pricing page typically renders rows as:
        #   <h_>Claude Opus 4.5</h_> ... $15 / MTok ... $75 / MTok
        # Strategy: lowercase the HTML, search for each name we care about,
        # then in a 3K window after the name try to find two $X.XX or $XX prices.
        lower = html.lower()
        for name, model_id in ANTHROPIC_NAME_MAP.items():
            idx = lower.find(name)
            if idx == -1:
                continue
            window = html[idx:idx + 3000]
            prices = re.findall(r"\$([0-9]+(?:\.[0-9]+)?)", window)
            if len(prices) < 2:
                continue
            # First two prices in row order are typically input then output per MTok
            try:
                p_in_usd = float(prices[0])
                p_out_usd = float(prices[1])
            except ValueError:
                continue

            snapshots.append(PriceSnapshot(
                model_id=model_id,
                price_input_per_million=int(p_in_usd * 100_000_000),
                price_output_per_million=int(p_out_usd * 100_000_000),
                currency="USD",
                source=self.name,
                source_url=self.URL,
            ))

        if not snapshots:
            raise PriceSourceError(
                "Anthropic page parsed but no known models found — "
                "page structure may have changed"
            )
        return snapshots


__all__ = ["AnthropicWebSource"]
