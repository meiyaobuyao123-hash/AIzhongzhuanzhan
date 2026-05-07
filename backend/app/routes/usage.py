"""Usage analytics endpoints for the user console."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import current_user, get_db
from app.errors import PrismException, error_response
from app.models.orm import Channel, UsageLog

router = APIRouter(tags=["usage"], prefix="/usage")


@router.get("/stats")
async def usage_stats(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
    since: str | None = Query(default=None, description="ISO timestamp"),
    until: str | None = Query(default=None, description="ISO timestamp"),
    group_by: str = Query(default="model", pattern="^(model|channel|key|day)$"),
):
    try:
        user = await current_user(authorization, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    since_dt = _parse_iso(since) or (datetime.now(timezone.utc) - timedelta(days=30))
    until_dt = _parse_iso(until)

    grouping_col = {
        "model": UsageLog.model_id,
        "channel": UsageLog.channel_id,
        "key": UsageLog.api_key_id,
        "day": func.date(UsageLog.created_at),
    }[group_by]

    stmt = (
        select(
            grouping_col.label("bucket"),
            func.count().label("requests"),
            func.sum(UsageLog.prompt_tokens).label("in_tok"),
            func.sum(UsageLog.completion_tokens).label("out_tok"),
            func.sum(UsageLog.cost_micro_cents).label("cost_mc"),
            func.avg(UsageLog.latency_ms).label("avg_latency"),
        )
        .where(UsageLog.user_id == user.id)
        .where(UsageLog.created_at >= since_dt)
        .group_by("bucket")
    )
    if until_dt:
        stmt = stmt.where(UsageLog.created_at <= until_dt)

    rows = (await db.execute(stmt)).all()

    # Compute summary
    total_cost = sum((r.cost_mc or 0) for r in rows)
    total_requests = sum((r.requests or 0) for r in rows)

    return {
        "group_by": group_by,
        "since": since_dt.isoformat(),
        "until": (until_dt or datetime.now(timezone.utc)).isoformat(),
        "summary": {
            "total_requests": total_requests,
            "total_cost_micro_cents": total_cost,
            "total_cost_usd": round(total_cost / 100_000_000, 4),
        },
        "data": [
            {
                "bucket": str(r.bucket) if r.bucket is not None else None,
                "requests": int(r.requests or 0),
                "input_tokens": int(r.in_tok or 0),
                "output_tokens": int(r.out_tok or 0),
                "cost_usd": round((r.cost_mc or 0) / 100_000_000, 4),
                "avg_latency_ms": round(r.avg_latency, 1) if r.avg_latency else None,
            }
            for r in rows
        ],
    }


@router.get("/requests")
async def usage_requests(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
    since: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    model: str | None = None,
):
    try:
        user = await current_user(authorization, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    since_dt = _parse_iso(since) or (datetime.now(timezone.utc) - timedelta(days=7))

    stmt = (
        select(UsageLog)
        .where(UsageLog.user_id == user.id)
        .where(UsageLog.created_at >= since_dt)
        .order_by(UsageLog.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    if model:
        stmt = stmt.where(UsageLog.model_id == model)

    rows = (await db.execute(stmt)).scalars().all()
    return {
        "page": page,
        "size": size,
        "data": [_request_summary(r) for r in rows],
    }


@router.get("/requests/{request_id}")
async def request_detail(
    request_id: str,
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """**The "渠道明牌" panel** — shows the user EXACTLY which upstream channel
    served this request, including region + data policy.

    This is the core differentiator from competitors that hide channel info.
    """
    try:
        user = await current_user(authorization, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    log = (await db.execute(
        select(UsageLog).where(UsageLog.request_id == request_id)
    )).scalar_one_or_none()
    if not log or log.user_id != user.id:
        return error_response(404, "Request not found", "invalid_request_error")

    channel: Channel | None = None
    if log.channel_id:
        channel = await db.get(Channel, log.channel_id)

    tried = json.loads(log.tried_channels) if log.tried_channels else []

    return {
        "request_id": log.request_id,
        "model_id": log.model_id,
        "status": log.status,
        "http_status": log.http_status,
        "is_streaming": log.is_streaming,
        "created_at": log.created_at.isoformat() if log.created_at else None,
        "tokens": {
            "prompt": log.prompt_tokens,
            "completion": log.completion_tokens,
            "cache_read": log.cache_read_tokens,
            "cache_write": log.cache_write_tokens,
            "reasoning": log.reasoning_tokens,
        },
        "cost_micro_cents": log.cost_micro_cents,
        "cost_usd": round(log.cost_micro_cents / 100_000_000, 6),
        "performance": {
            "latency_ms": log.latency_ms,
            "ttft_ms": log.ttft_ms,
        },
        "routing": {
            "attempt_index": log.attempt_index,
            "tried_channels": tried,
            "served_by_channel": _channel_view(channel) if channel else None,
        },
        "error_message": log.error_message,
    }


def _request_summary(r: UsageLog) -> dict:
    return {
        "request_id": r.request_id,
        "model_id": r.model_id,
        "status": r.status,
        "channel_id": r.channel_id,
        "tokens": {
            "prompt": r.prompt_tokens,
            "completion": r.completion_tokens,
        },
        "cost_usd": round(r.cost_micro_cents / 100_000_000, 6),
        "latency_ms": r.latency_ms,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _channel_view(c: Channel) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "provider": c.provider,
        "region": c.region,
        "policy": {
            "no_training": c.policy_no_training,
            "log_retention_days": c.policy_log_retention_days,
        },
    }


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None
