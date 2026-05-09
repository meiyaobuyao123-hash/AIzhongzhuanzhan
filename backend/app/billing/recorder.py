"""Persist a usage_log + dual-wallet deduct + write balance_transaction.

v0.4: cost is in the model's NATIVE currency. Deduction strategy:
  1. Same-currency wallet has enough → 1:1 deduction
  2. Same-currency wallet empty + opposite has enough → cross-FX deduction
     (asymmetric rate from settings, with spread in our favor)
  3. Both insufficient → InsufficientBalance / partial billing

Wraps everything in a single DB transaction so partial failures roll back.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.errors import InsufficientBalance
from app.models.orm import (
    ApiKey,
    BalanceTransaction,
    Channel,
    Model,
    UsageLog,
    User,
)
from app.schemas.common import ResponseStats, Usage


def _convert_to_other_wallet(cost_native: int, model_currency: str) -> int:
    """Cross-currency conversion using asymmetric FX rates.

    Returns the cost in the OTHER wallet's currency unit (still in µ).
    """
    if model_currency == "USD":
        # Pay USD-priced model from CNY wallet: 7 CNY = 1 USD (worse for user)
        # cost_µ¢ × 7  = cost_µ¥  (since 1 µ¢ = 1 µ¥ scale-wise, just × FX)
        rate = settings.fx_cny_to_usd_for_intl_model  # = 7.0
        return int(cost_native * rate)
    elif model_currency == "CNY":
        # Pay CNY-priced model from USD wallet: 1 USD = 6.5 CNY (worse for user)
        # cost_µ¥ ÷ 6.5 = cost_µ¢
        rate = settings.fx_usd_to_cny_for_cn_model  # = 6.5
        return int(cost_native / rate)
    else:
        raise ValueError(f"Unknown model_currency: {model_currency}")


def _deduct_from_wallets(
    user: User, cost_native: int, model_currency: str
) -> tuple[str, int]:
    """Apply dual-wallet deduction strategy.

    Returns (charged_currency, charged_amount). May raise InsufficientBalance.

    Mutates `user` in-place (balance_micro_cents or balance_cny_micro_yuan).
    """
    if model_currency == "USD":
        # Try USD wallet first (1:1)
        if user.balance_micro_cents >= cost_native:
            user.balance_micro_cents -= cost_native
            return ("USD", cost_native)
        # Fall back to CNY wallet via FX
        cost_cny = _convert_to_other_wallet(cost_native, "USD")
        if user.balance_cny_micro_yuan >= cost_cny:
            user.balance_cny_micro_yuan -= cost_cny
            return ("CNY", cost_cny)
        raise InsufficientBalance(
            f"Insufficient balance: USD ${user.balance_micro_cents / 100_000_000:.4f}, "
            f"CNY ¥{user.balance_cny_micro_yuan / 100_000_000:.4f}, "
            f"need ${cost_native / 100_000_000:.4f} USD or "
            f"¥{cost_cny / 100_000_000:.4f} CNY"
        )
    elif model_currency == "CNY":
        if user.balance_cny_micro_yuan >= cost_native:
            user.balance_cny_micro_yuan -= cost_native
            return ("CNY", cost_native)
        cost_usd = _convert_to_other_wallet(cost_native, "CNY")
        if user.balance_micro_cents >= cost_usd:
            user.balance_micro_cents -= cost_usd
            return ("USD", cost_usd)
        raise InsufficientBalance(
            f"Insufficient balance: CNY ¥{user.balance_cny_micro_yuan / 100_000_000:.4f}, "
            f"USD ${user.balance_micro_cents / 100_000_000:.4f}, "
            f"need ¥{cost_native / 100_000_000:.4f} CNY or "
            f"${cost_usd / 100_000_000:.4f} USD"
        )
    else:
        raise ValueError(f"Unknown model_currency: {model_currency}")


async def record_request_outcome(
    db: AsyncSession,
    *,
    request_id: str,
    user: User,
    api_key: ApiKey,
    channel: Channel | None,
    model: Model,
    usage: Usage,
    cost_micro_cents: int,
    status: str,
    http_status: int | None = None,
    error_message: str | None = None,
    stats: ResponseStats | None = None,
    is_streaming: bool = False,
    client_ip: str | None = None,
) -> UsageLog:
    """Persist usage_log + dual-wallet deduction + balance_transaction in one tx.

    `cost_micro_cents` is the NATIVE currency cost (USD µ¢ or CNY µ¥) per the
    model's `price_currency`.

    For status='ok' or 'partial', we deduct from the appropriate wallet(s).
    For 'error' or 'cancelled' with cost==0, no balance change.
    """
    model_currency = (model.price_currency or "USD").upper()

    # v0.5: stamp the active price_version_id so refunds are computable
    from app.pricing.checker import get_active_price_version_id
    price_version_id = await get_active_price_version_id(db, model_id=model.model_id)

    log = UsageLog(
        request_id=request_id,
        user_id=user.id,
        api_key_id=api_key.id,
        channel_id=channel.id if channel else None,
        model_id=model.model_id,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        cache_read_tokens=usage.cache_read_tokens,
        cache_write_tokens=usage.cache_write_tokens,
        reasoning_tokens=usage.reasoning_tokens,
        cost_micro_cents=cost_micro_cents,
        status=status,
        http_status=http_status,
        error_message=error_message,
        latency_ms=None,
        ttft_ms=stats.ttft_ms if stats else None,
        is_streaming=is_streaming,
        client_ip=client_ip,
        price_version_id=price_version_id,
    )
    db.add(log)
    await db.flush()

    if cost_micro_cents > 0:
        await db.refresh(user)
        try:
            charged_currency, actual_charge = _deduct_from_wallets(
                user, cost_micro_cents, model_currency
            )
            balance_after = (
                user.balance_micro_cents if charged_currency == "USD"
                else user.balance_cny_micro_yuan
            )
            db.add(BalanceTransaction(
                user_id=user.id,
                type="inference",
                amount_micro_cents=-actual_charge,
                balance_after_micro_cents=balance_after,
                currency=charged_currency,
                related_usage_log_id=log.id,
                description=(
                    f"{model.model_id} via channel "
                    f"{channel.id if channel else 'n/a'} ({status}) — "
                    f"charged {charged_currency}"
                ),
            ))
        except InsufficientBalance as exc:
            # Edge case: usage exceeded pre-flight estimate. Bill what we can
            # from the model-native wallet, mark log with the underrun.
            if model_currency == "USD":
                actual_charge = max(0, user.balance_micro_cents)
                user.balance_micro_cents = 0
                charged_currency = "USD"
                balance_after = 0
            else:
                actual_charge = max(0, user.balance_cny_micro_yuan)
                user.balance_cny_micro_yuan = 0
                charged_currency = "CNY"
                balance_after = 0
            log.error_message = (
                f"{log.error_message or ''}; balance underrun: {exc}"
            ).strip("; ")
            if actual_charge > 0:
                db.add(BalanceTransaction(
                    user_id=user.id,
                    type="inference",
                    amount_micro_cents=-actual_charge,
                    balance_after_micro_cents=balance_after,
                    currency=charged_currency,
                    related_usage_log_id=log.id,
                    description=f"{model.model_id} (underrun, partial bill)",
                ))

    await db.commit()
    return log


async def check_balance_or_402(
    db: AsyncSession, user: User, estimated_cost_micro_cents: int,
    model_currency: str = "USD",
) -> None:
    """Pre-flight balance check. Raises InsufficientBalance if user can't afford
    the estimated cost from EITHER wallet (native first, then via FX)."""
    await db.refresh(user)
    if model_currency == "USD":
        if user.balance_micro_cents >= estimated_cost_micro_cents:
            return
        # Check CNY wallet via FX
        needed_cny = _convert_to_other_wallet(estimated_cost_micro_cents, "USD")
        if user.balance_cny_micro_yuan >= needed_cny:
            return
        raise InsufficientBalance(
            f"Insufficient balance: USD ${user.balance_micro_cents / 100_000_000:.4f}, "
            f"CNY ¥{user.balance_cny_micro_yuan / 100_000_000:.4f}, "
            f"need ${estimated_cost_micro_cents / 100_000_000:.4f} or "
            f"¥{needed_cny / 100_000_000:.4f}"
        )
    else:  # 'CNY'
        if user.balance_cny_micro_yuan >= estimated_cost_micro_cents:
            return
        needed_usd = _convert_to_other_wallet(estimated_cost_micro_cents, "CNY")
        if user.balance_micro_cents >= needed_usd:
            return
        raise InsufficientBalance(
            f"Insufficient balance: CNY ¥{user.balance_cny_micro_yuan / 100_000_000:.4f}, "
            f"USD ${user.balance_micro_cents / 100_000_000:.4f}, "
            f"need ¥{estimated_cost_micro_cents / 100_000_000:.4f} or "
            f"${needed_usd / 100_000_000:.4f}"
        )
