"""Cost calculation: tokens × model unit price → (cost, currency).

v0.4 dual-wallet: cost is computed in the model's NATIVE currency. Whether
the user pays from USD wallet, CNY wallet, or both (with FX) is decided
later in `billing.recorder`.

Money math is integer micro-cents (USD) or micro-yuan (CNY); same scale,
1 base unit = 100_000_000 µ.
"""

from __future__ import annotations

from app.models.orm import Model
from app.schemas.common import Usage


def calculate_cost_micro_cents(usage: Usage, model: Model) -> int:
    """Backwards-compatible shim. Returns native-currency cost as int.

    For 'USD' models this is micro-cents. For 'CNY' models this is micro-yuan.
    Callers that care about currency should use :func:`calculate_cost_native`.
    """
    cost, _ = calculate_cost_native(usage, model)
    return cost


def calculate_cost_native(usage: Usage, model: Model) -> tuple[int, str]:
    """Compute total cost in the model's native currency.

    Returns (cost_micro, currency) where currency is 'USD' or 'CNY' and
    cost_micro is in micro-cents (USD) or micro-yuan (CNY) respectively.

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
        cost += (
            usage.reasoning_tokens * model.price_output_per_million // 1_000_000
        )

    currency = (model.price_currency or "USD").upper()
    return cost, currency


def estimate_max_cost_micro_cents(
    prompt_tokens_estimate: int,
    max_output_tokens: int,
    model: Model,
) -> int:
    """Pre-flight balance estimate: most-pessimistic cost in NATIVE currency."""
    cost = 0
    cost += prompt_tokens_estimate * model.price_input_per_million // 1_000_000
    cost += max_output_tokens * model.price_output_per_million // 1_000_000
    return cost
