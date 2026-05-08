"""Capacity alert evaluation: thresholds, debouncing, edge cases."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

from app.models.orm import Channel, UsageLog


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _seed_channel(db, *, name="anthropic primary", chan_id=None) -> Channel:
    ch = Channel(
        provider="anthropic",
        name=name,
        base_url="https://api.anthropic.com",
        upstream_key_encrypted="enc",
        models='["claude-haiku-4-5"]',
    )
    if chan_id is not None:
        ch.id = chan_id
    db.add(ch)
    await db.flush()
    return ch


async def _seed_usage(db, *, channel_id, count=10, errors=0,
                      tokens_per_req=100, age_minutes=1) -> None:
    base_ts = _now() - timedelta(minutes=age_minutes)
    for i in range(count):
        is_error = i < errors
        db.add(UsageLog(
            request_id=f"req-{channel_id}-{age_minutes}-{i}-{os.getpid()}",
            user_id=1,
            api_key_id=1,
            channel_id=channel_id,
            model_id="claude-haiku-4-5",
            prompt_tokens=tokens_per_req,
            completion_tokens=tokens_per_req,
            cost_micro_cents=100,
            status="error" if is_error else "ok",
            http_status=500 if is_error else 200,
            created_at=base_ts,
        ))
    await db.flush()


# ─── Tests ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_evaluate_window_returns_empty_when_no_usage(db_session):
    from app.monitoring.capacity import evaluate_window
    stats = await evaluate_window(db_session)
    assert stats == []


@pytest.mark.asyncio
async def test_evaluate_window_aggregates_rpm_tpm_errors(db_session):
    from app.monitoring.capacity import evaluate_window

    ch = await _seed_channel(db_session)
    # 100 requests in last minute, 5 errors, 200 tokens each
    await _seed_usage(db_session, channel_id=ch.id, count=100, errors=5, tokens_per_req=100)
    await db_session.flush()

    stats = await evaluate_window(db_session)
    assert len(stats) == 1
    s = stats[0]
    assert s.channel_id == ch.id
    assert s.requests == 100
    assert s.rpm == 20.0  # 100 reqs / 5 min window
    # tokens = 100 reqs × (100 in + 100 out) = 20_000; tpm = 20_000 / 5 = 4000
    assert s.tpm == 4000.0
    assert s.errors == 5
    assert s.error_rate_pct == 5.0


@pytest.mark.asyncio
async def test_evaluate_window_excludes_old_logs(db_session):
    from app.monitoring.capacity import evaluate_window

    ch = await _seed_channel(db_session)
    # 50 fresh, 50 OLD (10 min ago = outside default 5-min window)
    await _seed_usage(db_session, channel_id=ch.id, count=50, age_minutes=1)
    await _seed_usage(db_session, channel_id=ch.id, count=50, age_minutes=10)

    stats = await evaluate_window(db_session)
    assert len(stats) == 1
    assert stats[0].requests == 50  # only the fresh ones


@pytest.mark.asyncio
async def test_collect_alerts_fires_on_high_5xx(db_session, monkeypatch):
    from app.monitoring.capacity import collect_alerts, evaluate_window

    # Lower the 5xx threshold so 5% is triggering
    from app.config import settings
    monkeypatch.setattr(settings, "capacity_5xx_warn_pct", 4.0)

    ch = await _seed_channel(db_session)
    await _seed_usage(db_session, channel_id=ch.id, count=100, errors=10)

    stats = await evaluate_window(db_session)
    alerts = collect_alerts(stats)
    err_alerts = [a for a in alerts if a.signal == "error_rate"]
    assert len(err_alerts) == 1
    assert err_alerts[0].channel_id == ch.id
    assert err_alerts[0].value == 10.0  # 10/100 = 10%
    assert err_alerts[0].threshold == 4.0


@pytest.mark.asyncio
async def test_collect_alerts_fires_on_high_rpm(db_session, monkeypatch):
    from app.config import settings
    from app.monitoring.capacity import collect_alerts, evaluate_window

    # Set quota = 50 and warn at 50% so anything > 25 RPM fires
    monkeypatch.setattr(settings, "capacity_default_rpm_quota", 50)
    monkeypatch.setattr(settings, "capacity_rpm_warn_pct", 50.0)

    ch = await _seed_channel(db_session)
    # 200 reqs / 5min = 40 RPM → 80% of 50 quota → fires
    await _seed_usage(db_session, channel_id=ch.id, count=200, errors=0)

    stats = await evaluate_window(db_session)
    alerts = collect_alerts(stats)
    rpm_alerts = [a for a in alerts if a.signal == "rpm"]
    assert len(rpm_alerts) == 1
    assert rpm_alerts[0].value == 80.0  # 40/50 = 80%


@pytest.mark.asyncio
async def test_collect_alerts_quiet_when_under_threshold(db_session, monkeypatch):
    from app.config import settings
    from app.monitoring.capacity import collect_alerts, evaluate_window

    monkeypatch.setattr(settings, "capacity_5xx_warn_pct", 50.0)
    monkeypatch.setattr(settings, "capacity_rpm_warn_pct", 99.0)
    monkeypatch.setattr(settings, "capacity_default_rpm_quota", 1000)

    ch = await _seed_channel(db_session)
    await _seed_usage(db_session, channel_id=ch.id, count=10, errors=0)

    stats = await evaluate_window(db_session)
    assert collect_alerts(stats) == []


@pytest.mark.asyncio
async def test_evaluate_and_alert_debounces_repeated_calls(db_session, monkeypatch):
    from app.config import settings
    from app.monitoring.capacity import evaluate_and_alert

    # Force alerts to fire
    monkeypatch.setattr(settings, "capacity_5xx_warn_pct", 1.0)
    monkeypatch.setattr(settings, "capacity_alert_debounce_min", 30)

    ch = await _seed_channel(db_session)
    await _seed_usage(db_session, channel_id=ch.id, count=100, errors=10)
    await db_session.flush()

    fired_first = await evaluate_and_alert(db_session)
    assert any(a.signal == "error_rate" and a.channel_id == ch.id for a in fired_first)

    # Same conditions, called again → debounced (no new fires)
    fired_second = await evaluate_and_alert(db_session)
    assert all(
        not (a.signal == "error_rate" and a.channel_id == ch.id)
        for a in fired_second
    )


@pytest.mark.asyncio
async def test_evaluate_groups_by_channel(db_session, monkeypatch):
    from app.config import settings
    from app.monitoring.capacity import evaluate_window

    monkeypatch.setattr(settings, "capacity_default_rpm_quota", 1000)
    ch1 = await _seed_channel(db_session, name="anthropic-1")
    ch2 = await _seed_channel(db_session, name="anthropic-2")

    await _seed_usage(db_session, channel_id=ch1.id, count=20, errors=0)
    await _seed_usage(db_session, channel_id=ch2.id, count=80, errors=8)

    stats = await evaluate_window(db_session)
    by_id = {s.channel_id: s for s in stats}
    assert by_id[ch1.id].requests == 20
    assert by_id[ch2.id].requests == 80
    assert by_id[ch2.id].error_rate_pct == 10.0
    assert by_id[ch1.id].channel_name == "anthropic-1"
    assert by_id[ch2.id].channel_name == "anthropic-2"


@pytest.mark.asyncio
async def test_unrouted_failures_show_up(db_session):
    """Requests that never picked a channel (channel_id=NULL) should still be aggregated."""
    from app.monitoring.capacity import evaluate_window

    await _seed_usage(db_session, channel_id=None, count=5, errors=5)

    stats = await evaluate_window(db_session)
    assert len(stats) == 1
    assert stats[0].channel_id is None
    assert stats[0].channel_name == "(unrouted)"
    assert stats[0].error_rate_pct == 100.0


def test_start_capacity_loop_disabled_when_interval_huge():
    """Tests force interval to 999999 (in conftest); start should return None."""
    import asyncio

    from app.monitoring.capacity import start_capacity_loop

    task = asyncio.run(start_capacity_loop())
    assert task is None
