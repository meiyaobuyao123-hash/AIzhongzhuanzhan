"""Capacity alerts: rolling 5min window over usage_logs → email + audit.

`evaluate_window(db)` computes per-channel:
  - requests_in_window
  - rpm = requests_in_window / window_min
  - tpm (sum of prompt + completion + cache + reasoning tokens / window_min)
  - error_rate_pct = (http_status >= 500 OR status='error') / total * 100

Each (channel_id, signal) tuple that exceeds its threshold becomes an alert
candidate. We then debounce via Redis SETNX so the same (channel,signal)
fires at most once every `capacity_alert_debounce_min` minutes.

`start_capacity_loop()` spawns the background task. Lifespan in `app.main`
calls this; tests call `evaluate_window()` directly.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import record_audit
from app.config import settings
from app.db import SessionLocal
from app.email import send_email
from app.logging_config import logger
from app.models.orm import Channel, UsageLog
from app.redis_client import get_redis

# Module-level constants (avoid magic numbers in comparisons)
HTTP_5XX_THRESHOLD = 500
LOOP_DISABLED_INTERVAL_S = 60_000


@dataclass
class WindowStats:
    channel_id: int | None
    channel_name: str
    requests: int
    rpm: float
    tpm: float
    errors: int
    error_rate_pct: float
    rpm_quota: int


@dataclass
class Alert:
    channel_id: int | None
    channel_name: str
    signal: str  # 'rpm' / 'error_rate' / etc.
    value: float
    threshold: float
    extra: dict


def _parse_emails(raw: str) -> list[str]:
    return [e.strip() for e in raw.split(",") if e.strip()]


async def evaluate_window(
    db: AsyncSession, *, window_min: int | None = None
) -> list[WindowStats]:
    """Aggregate the last `window_min` of usage_logs per channel."""
    window_min = window_min or settings.capacity_window_min
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_min)

    # Build per-channel aggregates. We treat NULL channel_id as a real bucket
    # because router-failed requests still represent load (and we want to know
    # if the failure rate is high).
    rows = (await db.execute(
        select(
            UsageLog.channel_id,
            func.count(UsageLog.id).label("total"),
            func.coalesce(func.sum(
                UsageLog.prompt_tokens
                + UsageLog.completion_tokens
                + UsageLog.cache_read_tokens
                + UsageLog.cache_write_tokens
                + UsageLog.reasoning_tokens
            ), 0).label("tokens"),
            func.coalesce(func.sum(
                case(
                    (UsageLog.status == "error", 1),
                    (UsageLog.http_status >= HTTP_5XX_THRESHOLD, 1),
                    else_=0,
                )
            ), 0).label("errors"),
        )
        .where(UsageLog.created_at >= cutoff)
        .group_by(UsageLog.channel_id)
    )).all()

    # Map channel_id → channel name (for friendlier alert text)
    name_map: dict[int | None, str] = {}
    if rows:
        ids = [r.channel_id for r in rows if r.channel_id is not None]
        if ids:
            name_rows = (await db.execute(
                select(Channel.id, Channel.name).where(Channel.id.in_(ids))
            )).all()
            name_map = {nid: name for nid, name in name_rows}
    name_map[None] = "(unrouted)"

    out: list[WindowStats] = []
    for r in rows:
        total = int(r.total or 0)
        if total == 0:
            continue
        errors = int(r.errors or 0)
        tokens = int(r.tokens or 0)
        out.append(WindowStats(
            channel_id=r.channel_id,
            channel_name=name_map.get(r.channel_id, "?"),
            requests=total,
            rpm=total / window_min,
            tpm=tokens / window_min,
            errors=errors,
            error_rate_pct=(errors * 100.0 / total) if total else 0.0,
            rpm_quota=settings.capacity_default_rpm_quota,
        ))
    return out


def collect_alerts(stats: list[WindowStats]) -> list[Alert]:
    """Apply thresholds → list of alerts. Pure function for easy testing."""
    out: list[Alert] = []
    for s in stats:
        # RPM alert
        rpm_pct = (s.rpm * 100.0 / s.rpm_quota) if s.rpm_quota else 0.0
        if rpm_pct >= settings.capacity_rpm_warn_pct:
            out.append(Alert(
                channel_id=s.channel_id,
                channel_name=s.channel_name,
                signal="rpm",
                value=round(rpm_pct, 1),
                threshold=settings.capacity_rpm_warn_pct,
                extra={
                    "rpm": round(s.rpm, 1),
                    "rpm_quota": s.rpm_quota,
                    "requests": s.requests,
                },
            ))

        # 5xx-rate alert
        if s.error_rate_pct >= settings.capacity_5xx_warn_pct:
            out.append(Alert(
                channel_id=s.channel_id,
                channel_name=s.channel_name,
                signal="error_rate",
                value=round(s.error_rate_pct, 2),
                threshold=settings.capacity_5xx_warn_pct,
                extra={
                    "errors": s.errors,
                    "requests": s.requests,
                },
            ))
    return out


def _debounce_key(alert: Alert) -> str:
    return f"prism:cap_alert:{alert.channel_id or 'null'}:{alert.signal}"


async def _is_debounced(alert: Alert) -> bool:
    """SETNX on the debounce key. Returns True if the alert is suppressed."""
    redis = get_redis()
    ttl = max(60, settings.capacity_alert_debounce_min * 60)
    # SETNX (set if not exists) with TTL: 1 if we just wrote (allowed), 0 if existed (debounced)
    ok = await redis.set(
        _debounce_key(alert), "1", ex=ttl, nx=True
    )
    # ok is True (Redis OK reply) when the key was newly created.
    return not bool(ok)


async def _send_alert(alert: Alert, db: AsyncSession) -> None:
    """Email + audit_log. Email is best-effort (never raises)."""
    subject = (
        f"[Prism] Capacity {alert.signal} ≥ "
        f"{alert.threshold} on channel {alert.channel_name}"
    )
    body = (
        f"Capacity threshold breached.\n\n"
        f"  Channel: {alert.channel_name} (id={alert.channel_id})\n"
        f"  Signal:  {alert.signal}\n"
        f"  Value:   {alert.value}\n"
        f"  Limit:   {alert.threshold}\n"
        f"  Window:  last {settings.capacity_window_min} minutes\n"
        f"  Detail:  {json.dumps(alert.extra)}\n\n"
        f"— Prism Capacity Monitor"
    )

    recipients = _parse_emails(settings.admin_alert_emails)
    for to in recipients:
        try:
            await send_email(to, subject, body)
        except Exception as exc:
            logger.error("capacity_alert_email_failed", to=to, error=str(exc))

    await record_audit(
        db, actor="capacity-monitor", action="capacity.alert",
        target=str(alert.channel_id) if alert.channel_id else "unrouted",
        payload={
            "signal": alert.signal,
            "value": alert.value,
            "threshold": alert.threshold,
            "channel_name": alert.channel_name,
            **alert.extra,
        },
    )

    logger.warning(
        "capacity_alert_fired",
        signal=alert.signal,
        channel_id=alert.channel_id,
        channel_name=alert.channel_name,
        value=alert.value,
        threshold=alert.threshold,
    )


async def evaluate_and_alert(db: AsyncSession) -> list[Alert]:
    """One full pass. Returns the alerts that were actually fired (post-debounce)."""
    stats = await evaluate_window(db)
    candidates = collect_alerts(stats)
    fired: list[Alert] = []
    for a in candidates:
        if await _is_debounced(a):
            logger.debug(
                "capacity_alert_debounced",
                signal=a.signal, channel_id=a.channel_id,
            )
            continue
        await _send_alert(a, db)
        fired.append(a)
    if fired:
        await db.commit()
    return fired


# ── background loop ────────────────────────────────────────────────────────


async def _capacity_loop() -> None:
    interval = max(15, settings.capacity_check_interval_s)
    if interval > LOOP_DISABLED_INTERVAL_S:
        # Effectively disabled (e.g. tests set interval to 999999) — exit.
        logger.info("capacity_loop_disabled_via_interval", interval_s=interval)
        return

    logger.info("capacity_loop_starting", interval_s=interval)
    try:
        while True:
            try:
                async with SessionLocal() as db:
                    fired = await evaluate_and_alert(db)
                if fired:
                    logger.info(
                        "capacity_loop_alerts_fired",
                        count=len(fired),
                    )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("capacity_loop_iter_failed", error=str(exc))
            await asyncio.sleep(interval)
    finally:
        logger.info("capacity_loop_stopped")


async def start_capacity_loop() -> asyncio.Task | None:
    """Spawn the loop. Returns None if the loop is disabled."""
    interval = settings.capacity_check_interval_s
    if interval >= LOOP_DISABLED_INTERVAL_S:
        # Don't even spawn the task — saves cycles in tests.
        return None
    return asyncio.create_task(_capacity_loop(), name="capacity-monitor")


__all__ = [
    "Alert",
    "WindowStats",
    "collect_alerts",
    "evaluate_and_alert",
    "evaluate_window",
    "start_capacity_loop",
]
