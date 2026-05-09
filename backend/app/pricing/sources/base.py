"""PriceSource abstract base."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.pricing.models import PriceSnapshot


class PriceSource(ABC):
    """One vendor's price source.

    Concrete implementations override `fetch_all`. If parsing fails or the
    network call fails, raise PriceSourceError — the checker logs it and
    moves on without writing anything (safe default).
    """

    name: str = "base"
    description: str = ""

    @abstractmethod
    async def fetch_all(self) -> list[PriceSnapshot]:
        """Return current prices for all models this source covers."""


__all__ = ["PriceSource"]
