"""Price source registry.

Each source returns PriceSnapshots from a specific vendor.
Order in REGISTRY = order they run in checker (Tier 1 first).
"""

from app.pricing.sources.anthropic_web import AnthropicWebSource
from app.pricing.sources.base import PriceSource
from app.pricing.sources.deepseek_web import DeepseekWebSource
from app.pricing.sources.doubao_web import DoubaoWebSource
from app.pricing.sources.minimax_web import MinimaxWebSource

# OpenAI billing source — Tier 1 (golden) — placeholder until we wire admin key
# from app.pricing.sources.openai_billing import OpenAIBillingSource

REGISTRY: list[type[PriceSource]] = [
    AnthropicWebSource,
    DeepseekWebSource,
    DoubaoWebSource,
    MinimaxWebSource,
    # OpenAIBillingSource,  # enable when admin key wired
]

__all__ = ["REGISTRY", "PriceSource"]
