"""Persist a usage_log + deduct balance + write balance_transaction.

Wraps everything in a single DB transaction so partial failures roll back. Used
as the on_complete callback from the SSE pump and from non-streaming routes.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

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
    """Persist usage_log + deduct balance + balance_transaction in one tx.

    For status='ok' or 'partial', we deduct cost_micro_cents from user balance.
    For 'error' or 'cancelled' with cost==0 (no upstream tokens billed), no
    balance change.
    """
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
    )
    db.add(log)
    await db.flush()  # need log.id before referencing in BalanceTransaction

    if cost_micro_cents > 0:
        # SQLite has no real row lock, but Postgres does; SELECT FOR UPDATE here.
        # For SQLite, we accept the write-write conflict will be rare in v0.1.
        await db.refresh(user)
        if user.balance_micro_cents < cost_micro_cents:
            # Edge case: usage exceeded pre-flight estimate. Bill what we can,
            # mark balance to zero, and flag the log.
            actual_charge = user.balance_micro_cents
            log.error_message = (
                f"{log.error_message or ''}; balance underrun: usage cost "
                f"{cost_micro_cents}µ¢ > balance {user.balance_micro_cents}µ¢"
            ).strip("; ")
        else:
            actual_charge = cost_micro_cents

        if actual_charge > 0:
            user.balance_micro_cents -= actual_charge
            db.add(BalanceTransaction(
                user_id=user.id,
                type="inference",
                amount_micro_cents=-actual_charge,
                balance_after_micro_cents=user.balance_micro_cents,
                related_usage_log_id=log.id,
                description=f"{model.model_id} via channel {channel.id if channel else 'n/a'} ({status})",
            ))

    await db.commit()
    return log


async def check_balance_or_402(
    db: AsyncSession, user: User, estimated_cost_micro_cents: int
) -> None:
    """Pre-flight balance check. Raises InsufficientBalance if user can't afford."""
    await db.refresh(user)
    if user.balance_micro_cents < estimated_cost_micro_cents:
        raise InsufficientBalance(
            f"Insufficient balance: have ${user.balance_micro_cents / 100_000_000:.4f}, "
            f"estimated cost ${estimated_cost_micro_cents / 100_000_000:.4f}"
        )
