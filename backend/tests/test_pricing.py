"""Cost calculation for v0.1: simple integer micro-cent arithmetic."""

from __future__ import annotations


def calculate_cost_micro_cents(
    *,
    prompt_tokens: int,
    completion_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
    reasoning_tokens: int = 0,
    price_input_per_million: int,
    price_output_per_million: int,
    price_cache_read_per_million: int | None = None,
    price_cache_write_per_million: int | None = None,
) -> int:
    """Inline-tested algorithm to verify the formula. Will move to app/billing/pricing.py
    in stage C, but this test pins the math today.
    """
    cost = 0
    cost += prompt_tokens * price_input_per_million // 1_000_000
    cost += completion_tokens * price_output_per_million // 1_000_000
    cost += cache_read_tokens * (price_cache_read_per_million or 0) // 1_000_000
    cost += cache_write_tokens * (price_cache_write_per_million or 0) // 1_000_000
    cost += reasoning_tokens * price_output_per_million // 1_000_000
    return cost


def test_simple_chat():
    # 1000 input @ $15/M, 500 output @ $75/M
    # 1000 * 1.5e9 / 1e6 = 1.5e6 micro-cents = $0.015
    # 500 * 7.5e9 / 1e6 = 3.75e6 micro-cents = $0.0375
    cost = calculate_cost_micro_cents(
        prompt_tokens=1000,
        completion_tokens=500,
        price_input_per_million=1_500_000_000,
        price_output_per_million=7_500_000_000,
    )
    assert cost == 1_500_000 + 3_750_000  # 5_250_000 µ¢ = $0.0525


def test_with_cache():
    cost = calculate_cost_micro_cents(
        prompt_tokens=1000,
        completion_tokens=500,
        cache_read_tokens=10000,
        cache_write_tokens=2000,
        price_input_per_million=1_500_000_000,
        price_output_per_million=7_500_000_000,
        price_cache_read_per_million=150_000_000,
        price_cache_write_per_million=1_875_000_000,
    )
    expected = (
        1000 * 1_500_000_000 // 1_000_000
        + 500 * 7_500_000_000 // 1_000_000
        + 10000 * 150_000_000 // 1_000_000
        + 2000 * 1_875_000_000 // 1_000_000
    )
    assert cost == expected


def test_reasoning_billed_at_output_rate():
    cost = calculate_cost_micro_cents(
        prompt_tokens=0,
        completion_tokens=0,
        reasoning_tokens=1000,
        price_input_per_million=800_000_000,
        price_output_per_million=3_200_000_000,
    )
    # 1000 reasoning at output rate: 1000 * 3.2e9 / 1e6 = 3.2e6 µ¢
    assert cost == 3_200_000


def test_no_floats_used():
    """Ensure the math never goes through float — large numbers must round-trip."""
    cost = calculate_cost_micro_cents(
        prompt_tokens=1_234_567,
        completion_tokens=5_678_901,
        price_input_per_million=1_500_000_000,
        price_output_per_million=7_500_000_000,
    )
    expected = (
        1_234_567 * 1_500_000_000 // 1_000_000
        + 5_678_901 * 7_500_000_000 // 1_000_000
    )
    assert cost == expected
    assert isinstance(cost, int)


def test_zero_tokens():
    cost = calculate_cost_micro_cents(
        prompt_tokens=0,
        completion_tokens=0,
        price_input_per_million=1_500_000_000,
        price_output_per_million=7_500_000_000,
    )
    assert cost == 0
