"""Top-up fee math: 万分之五 = 5 basis points = 0.05%."""

from __future__ import annotations


def calculate_topup_fee(amount_micro_cents: int, fee_bps: int = 5) -> int:
    """Integer math for fee. fee_bps = 5 means 5/10000 = 0.05%."""
    return amount_micro_cents * fee_bps // 10_000


def test_10000_topup_yields_5_fee():
    """充 10000 USD 收 5 USD 手续费 (万 5)."""
    amount = 10_000 * 100_000_000  # $10,000 in micro-cents
    fee = calculate_topup_fee(amount)
    assert fee == 5 * 100_000_000  # exactly $5


def test_1_topup_yields_5cent_fee():
    """充 100 USD → 5 cents fee = $0.05 = 5_000_000 µ¢."""
    amount = 100 * 100_000_000
    fee = calculate_topup_fee(amount)
    assert fee == 5_000_000


def test_5_topup_min():
    """充 $5 → fee 0.25 cent = 250_000 µ¢."""
    amount = 5 * 100_000_000
    fee = calculate_topup_fee(amount)
    assert fee == 250_000


def test_credited_after_fee():
    amount = 10_000 * 100_000_000
    fee = calculate_topup_fee(amount)
    credited = amount - fee
    assert credited == 9_995 * 100_000_000  # exactly $9,995
