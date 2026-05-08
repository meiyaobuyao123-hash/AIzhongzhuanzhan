"""Top-up fee math: 1.5% = 150 basis points (covers 链上 gas / 商户费 / Stripe 等)."""

from __future__ import annotations


def calculate_topup_fee(amount_micro_cents: int, fee_bps: int = 150) -> int:
    """Integer math for fee. fee_bps = 150 means 150/10000 = 1.5%."""
    return amount_micro_cents * fee_bps // 10_000


def test_10000_topup_yields_150_fee():
    """充 $10,000 收 $150 手续费 (1.5%)."""
    amount = 10_000 * 100_000_000  # $10,000 in micro-cents
    fee = calculate_topup_fee(amount)
    assert fee == 150 * 100_000_000  # exactly $150


def test_100_topup_yields_1_50_fee():
    """充 $100 → $1.50 fee = 150_000_000 µ¢."""
    amount = 100 * 100_000_000
    fee = calculate_topup_fee(amount)
    assert fee == 150_000_000


def test_5_topup_min():
    """充 $5 → fee $0.075 = 7_500_000 µ¢."""
    amount = 5 * 100_000_000
    fee = calculate_topup_fee(amount)
    assert fee == 7_500_000


def test_credited_after_fee():
    """充 $10,000 → 实到账 $9,850."""
    amount = 10_000 * 100_000_000
    fee = calculate_topup_fee(amount)
    credited = amount - fee
    assert credited == 9_850 * 100_000_000  # exactly $9,850


def test_old_万5_no_longer_applies():
    """Sanity: confirm we are NOT charging the old 0.05% rate."""
    amount = 10_000 * 100_000_000
    old_fee = calculate_topup_fee(amount, fee_bps=5)
    new_fee = calculate_topup_fee(amount, fee_bps=150)
    assert new_fee == old_fee * 30  # 1.5% / 0.05% = 30×
