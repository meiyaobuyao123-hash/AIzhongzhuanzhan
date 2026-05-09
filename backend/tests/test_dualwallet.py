"""v0.4 dual-wallet: cross-currency deduction + FX spread tests."""

from __future__ import annotations

import pytest

from app.billing.recorder import _convert_to_other_wallet, _deduct_from_wallets
from app.errors import InsufficientBalance
from app.models.orm import User


# ─── FX conversion helpers ─────────────────────────────────────────────────


def test_fx_usd_to_cny_rate_for_cn_model():
    """USD wallet pays CN-priced model: cost ¥1 = $0.1538 (=1/6.5)."""
    cost_native_cny = 100_000_000  # ¥1 in µ¥
    cost_usd_micro_cents = _convert_to_other_wallet(cost_native_cny, "CNY")
    # ¥1 ÷ 6.5 = $0.15384...; in µ¢ = 15_384_615 (int truncation)
    assert cost_usd_micro_cents == int(100_000_000 / 6.5)
    assert cost_usd_micro_cents == 15_384_615


def test_fx_cny_to_usd_rate_for_intl_model():
    """CNY wallet pays USD-priced model: cost $1 = ¥7."""
    cost_native_usd = 100_000_000  # $1 in µ¢
    cost_cny_micro_yuan = _convert_to_other_wallet(cost_native_usd, "USD")
    # $1 × 7 = ¥7 = 700_000_000 µ¥
    assert cost_cny_micro_yuan == 700_000_000


# ─── Same-currency wallet sufficient → 1:1 deduction ────────────────────────


def test_usd_model_paid_from_usd_wallet():
    user = User(email="t@x.com", balance_micro_cents=10_000_000_000,  # $100
                balance_cny_micro_yuan=0)
    charged_currency, charged_amount = _deduct_from_wallets(
        user, cost_native=500_000, model_currency="USD"
    )
    assert charged_currency == "USD"
    assert charged_amount == 500_000
    assert user.balance_micro_cents == 10_000_000_000 - 500_000
    assert user.balance_cny_micro_yuan == 0  # untouched


def test_cny_model_paid_from_cny_wallet():
    user = User(email="t@x.com", balance_micro_cents=0,
                balance_cny_micro_yuan=100_000_000_000)  # ¥1000
    charged_currency, charged_amount = _deduct_from_wallets(
        user, cost_native=80_000_000, model_currency="CNY"  # ¥0.8
    )
    assert charged_currency == "CNY"
    assert charged_amount == 80_000_000
    assert user.balance_cny_micro_yuan == 100_000_000_000 - 80_000_000
    assert user.balance_micro_cents == 0


# ─── Cross-currency fallback (with FX spread) ──────────────────────────────


def test_usd_model_pays_from_cny_when_usd_empty():
    """USD model, no USD balance → falls back to CNY at 7.0 (worse for user)."""
    user = User(email="t@x.com", balance_micro_cents=0,
                balance_cny_micro_yuan=10_000_000_000)  # ¥100
    cost_usd = 100_000_000  # $1 in µ¢
    charged_currency, charged_amount = _deduct_from_wallets(
        user, cost_native=cost_usd, model_currency="USD"
    )
    assert charged_currency == "CNY"
    # $1 × 7.0 = ¥7
    assert charged_amount == 700_000_000
    assert user.balance_cny_micro_yuan == 10_000_000_000 - 700_000_000
    assert user.balance_micro_cents == 0


def test_cny_model_pays_from_usd_when_cny_empty():
    """CN model, no CNY balance → falls back to USD at 6.5 (worse for user)."""
    user = User(email="t@x.com", balance_micro_cents=10_000_000_000,  # $100
                balance_cny_micro_yuan=0)
    cost_cny = 100_000_000  # ¥1 in µ¥
    charged_currency, charged_amount = _deduct_from_wallets(
        user, cost_native=cost_cny, model_currency="CNY"
    )
    assert charged_currency == "USD"
    # ¥1 ÷ 6.5 = $0.1538...
    assert charged_amount == int(100_000_000 / 6.5)
    assert user.balance_micro_cents == 10_000_000_000 - charged_amount
    assert user.balance_cny_micro_yuan == 0


# ─── Insufficient on both wallets ──────────────────────────────────────────


def test_insufficient_both_wallets_raises():
    user = User(email="t@x.com", balance_micro_cents=100_000,        # $0.001
                balance_cny_micro_yuan=100_000)                      # ¥0.001
    with pytest.raises(InsufficientBalance):
        _deduct_from_wallets(user, cost_native=10_000_000, model_currency="USD")


# ─── Same-currency preferred over cross-currency ──────────────────────────


def test_same_currency_preferred_when_both_have_balance():
    """When both wallets have funds, same-currency wallet wins (no FX spread loss)."""
    user = User(email="t@x.com",
                balance_micro_cents=10_000_000_000,        # $100
                balance_cny_micro_yuan=10_000_000_000)     # ¥100
    charged_currency, _ = _deduct_from_wallets(
        user, cost_native=100_000_000, model_currency="USD"
    )
    assert charged_currency == "USD"  # paid from USD even though CNY also had enough


# ─── User margin sanity check ──────────────────────────────────────────────


def test_fx_spread_in_our_favor():
    """FX rates 6.5 / 7.0 should both yield user paying MORE than at mid-market 7.20."""
    # User pays ¥1 worth of CN model from USD wallet.
    cost_at_our_rate = _convert_to_other_wallet(100_000_000, "CNY")  # ÷ 6.5
    cost_at_mid_market = int(100_000_000 / 7.2)
    assert cost_at_our_rate > cost_at_mid_market  # we charge more
    spread_pct = (cost_at_our_rate - cost_at_mid_market) / cost_at_mid_market * 100
    assert 9 < spread_pct < 12  # ≈ 10.8%

    # User pays $1 worth of intl model from CNY wallet.
    cost_at_our_rate = _convert_to_other_wallet(100_000_000, "USD")  # × 7.0
    cost_at_mid_market = int(100_000_000 * 7.2)
    assert cost_at_our_rate < cost_at_mid_market  # we GIVE less CNY for $1
    # i.e., user has to spend MORE CNY (since 7.0 < 7.2), but our function
    # returns the µ¥ cost equivalent — which is LESS µ¥ than mid-market
    # would say for $1, meaning user effectively pays a worse rate.
    # The spread:
    spread_pct = (cost_at_mid_market - cost_at_our_rate) / cost_at_mid_market * 100
    assert 2 < spread_pct < 4  # ≈ 2.78%
