"""Cost calculation: tokens × model unit price → micro-cents (integer math).

All money math is integer micro-cents. 1 USD = 100_000_000 micro-cents.
Model.price_*_per_million is already micro-cents per 1M tokens.

cost = sum(tokens_X × price_X_per_million // 1_000_000)
"""

from __future__ import annotations

from app.models.orm import Model
from app.schemas.common import Usage


def calculate_cost_micro_cents(usage: Usage, model: Model) -> int:
    """Compute total cost in micro-cents from a Usage and a Model.

    Reasoning tokens (OpenAI o-series) bill at the output rate.
    Cache_read / cache_write fall back to 0 if their per-million price isn't set.
    """
    cost = 0
    cost += usage.prompt_tokens * model.price_input_per_million // 1_000_000
    cost += usage.completion_tokens * model.price_output_per_million // 1_000_000

    if usage.cache_read_tokens and model.price_cache_read_per_million:
        cost += (
            usage.cache_read_tokens
            * model.price_cache_read_per_million
            // 1_000_000
        )

    if usage.cache_write_tokens and model.price_cache_write_per_million:
        cost += (
            usage.cache_write_tokens
            * model.price_cache_write_per_million
            // 1_000_000
        )

    if usage.reasoning_tokens:
        # Reasoning tokens bill at output rate (OpenAI's spec).
        cost += (
            usage.reasoning_tokens * model.price_output_per_million // 1_000_000
        )

    return cost


def estimate_max_cost_micro_cents(
    prompt_tokens_estimate: int,
    max_output_tokens: int,
    model: Model,
) -> int:
    """Pre-flight balance estimate: most-pessimistic cost if all output tokens
    are output (no cache)."""
    cost = 0
    cost += prompt_tokens_estimate * model.price_input_per_million // 1_000_000
    cost += max_output_tokens * model.price_output_per_million // 1_000_000
    return cost
