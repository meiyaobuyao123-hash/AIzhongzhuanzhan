"""Billing module tests using the actual app/billing/pricing.py."""

from __future__ import annotations

from app.billing import calculate_cost_micro_cents, estimate_max_cost_micro_cents
from app.models.orm import Model
from app.schemas.common import Usage


def make_model(**overrides) -> Model:
    base = dict(
        id=1,
        model_id="claude-opus-4-5",
        display_name="Claude Opus 4.5",
        provider="anthropic",
        context_window=200_000,
        price_input_per_million=1_500_000_000,        # $15
        price_output_per_million=7_500_000_000,       # $75
        price_cache_read_per_million=150_000_000,     # $1.5
        price_cache_write_per_million=1_875_000_000,  # $18.75
    )
    base.update(overrides)
    return Model(**base)


def test_simple_cost():
    model = make_model()
    usage = Usage(prompt_tokens=1000, completion_tokens=500)
    cost = calculate_cost_micro_cents(usage, model)
    # 1000 * 1.5e9 // 1e6 = 1_500_000
    # 500 * 7.5e9 // 1e6 = 3_750_000
    assert cost == 5_250_000


def test_with_cache_costs():
    model = make_model()
    usage = Usage(
        prompt_tokens=1000,
        completion_tokens=500,
        cache_read_tokens=10_000,
        cache_write_tokens=2_000,
    )
    cost = calculate_cost_micro_cents(usage, model)
    expected = (
        1000 * 1_500_000_000 // 1_000_000
        + 500 * 7_500_000_000 // 1_000_000
        + 10_000 * 150_000_000 // 1_000_000
        + 2_000 * 1_875_000_000 // 1_000_000
    )
    assert cost == expected


def test_cache_falls_back_to_zero_when_price_not_set():
    model = make_model(price_cache_read_per_million=None, price_cache_write_per_million=None)
    usage = Usage(prompt_tokens=100, completion_tokens=50, cache_read_tokens=999, cache_write_tokens=999)
    cost = calculate_cost_micro_cents(usage, model)
    # cache should contribute 0 when price is None
    assert cost == 100 * 1_500_000_000 // 1_000_000 + 50 * 7_500_000_000 // 1_000_000


def test_reasoning_at_output_rate():
    model = make_model()
    usage = Usage(reasoning_tokens=1000)
    cost = calculate_cost_micro_cents(usage, model)
    # 1000 reasoning at output rate $75/M → 7_500_000 µ¢
    assert cost == 7_500_000


def test_estimate_max_cost():
    model = make_model()
    cost = estimate_max_cost_micro_cents(1000, 4096, model)
    assert cost == 1000 * 1_500_000_000 // 1_000_000 + 4096 * 7_500_000_000 // 1_000_000


def test_zero_usage():
    assert calculate_cost_micro_cents(Usage(), make_model()) == 0
