"""PriceSnapshot dataclass + PriceSourceError."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class PriceSnapshot:
    """One observation of a model's price from a single source."""

    model_id: str
    price_input_per_million: int   # native unit (µ¢ for USD, µ¥ for CNY)
    price_output_per_million: int
    currency: str                   # 'USD' or 'CNY'
    source: str                     # 'openai_billing' / 'anthropic_web' / etc
    source_url: str
    price_cache_read_per_million: int | None = None
    price_cache_write_per_million: int | None = None
    fetched_at: datetime = field(default_factory=_utcnow)


class PriceSourceError(Exception):
    """Raised when a source can't fetch / parse. Caught by checker; we log
    and continue with other sources without writing anything."""


__all__ = ["PriceSnapshot", "PriceSourceError"]
