"""v0.5 price tracking: checker logic + anomaly lifecycle."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from app.models.orm import (
    Model,
    ModelPriceHistory,
    PriceAnomaly,
)
from app.pricing.checker import (
    confirm_anomaly,
    get_active_price_version_id,
    reject_anomaly,
    run_check_cycle,
)
from app.pricing.models import PriceSnapshot, PriceSourceError
from app.pricing.sources.anthropic_web import AnthropicWebSource
from app.pricing.sources.base import PriceSource

# ─── A trivial fake source ────────────────────────────────────────────────


class FakeSource(PriceSource):
    name = "fake"

    def __init__(self, snapshots=None, raise_error=None):
        self._snaps = snapshots or []
        self._err = raise_error

    async def fetch_all(self):
        if self._err:
            raise PriceSourceError(self._err)
        return self._snaps


# ─── checker.run_check_cycle ──────────────────────────────────────────────


async def _seed_model(db, model_id="claude-opus-4-5", input_price=1_500_000_000,
                      output_price=7_500_000_000, currency="USD"):
    db.add(Model(
        model_id=model_id, display_name=model_id, provider="anthropic",
        price_input_per_million=input_price,
        price_output_per_million=output_price,
        price_currency=currency,
    ))
    await db.flush()


@pytest.mark.asyncio
async def test_check_no_diff_no_anomaly(db_session):
    await _seed_model(db_session)
    # Same as DB → no anomaly
    src_cls = type("S", (FakeSource,), {})
    fake_snap = PriceSnapshot(
        model_id="claude-opus-4-5",
        price_input_per_million=1_500_000_000,
        price_output_per_million=7_500_000_000,
        currency="USD", source="fake", source_url="x",
    )
    src_cls.__init__ = lambda self: FakeSource.__init__(self, [fake_snap])

    result = await run_check_cycle(db_session, sources=[src_cls])
    assert result.anomalies_created == 0
    assert result.snapshots_unchanged == 1


@pytest.mark.asyncio
async def test_check_diff_creates_anomaly(db_session):
    from sqlalchemy import select
    await _seed_model(db_session)
    src_cls = type("S", (FakeSource,), {})
    # Observed input dropped 5% → > 1% threshold → anomaly
    fake_snap = PriceSnapshot(
        model_id="claude-opus-4-5",
        price_input_per_million=1_425_000_000,  # 5% lower
        price_output_per_million=7_500_000_000,
        currency="USD", source="fake_test", source_url="x",
    )
    src_cls.__init__ = lambda self: FakeSource.__init__(self, [fake_snap])

    result = await run_check_cycle(db_session, sources=[src_cls])
    assert result.anomalies_created == 1
    rows = (await db_session.execute(
        select(PriceAnomaly).where(PriceAnomaly.status == "pending")
    )).scalars().all()
    assert len(rows) == 1
    assert rows[0].model_id == "claude-opus-4-5"
    assert rows[0].source == "fake_test"
    assert abs(rows[0].diff_pct_input - 5.0) < 0.01


@pytest.mark.asyncio
async def test_check_skips_unknown_models(db_session):
    src_cls = type("S", (FakeSource,), {})
    fake_snap = PriceSnapshot(
        model_id="not-in-catalog", price_input_per_million=1, price_output_per_million=1,
        currency="USD", source="fake", source_url="x",
    )
    src_cls.__init__ = lambda self: FakeSource.__init__(self, [fake_snap])

    result = await run_check_cycle(db_session, sources=[src_cls])
    assert result.unknown_models == 1
    assert result.anomalies_created == 0


@pytest.mark.asyncio
async def test_check_one_source_fails_others_continue(db_session):
    await _seed_model(db_session)
    fail_cls = type("F", (FakeSource,), {})
    fail_cls.__init__ = lambda self: FakeSource.__init__(self, raise_error="boom")

    ok_cls = type("OK", (FakeSource,), {})
    fake_snap = PriceSnapshot(
        model_id="claude-opus-4-5",
        price_input_per_million=2_000_000_000,  # big diff
        price_output_per_million=7_500_000_000,
        currency="USD", source="ok_test", source_url="x",
    )
    ok_cls.__init__ = lambda self: FakeSource.__init__(self, [fake_snap])

    result = await run_check_cycle(db_session, sources=[fail_cls, ok_cls])
    assert len(result.sources_failed) == 1
    assert result.anomalies_created == 1


@pytest.mark.asyncio
async def test_check_dedups_pending_anomaly(db_session):
    """Running check twice with same observed value shouldn't create 2 anomalies."""
    await _seed_model(db_session)
    src_cls = type("S", (FakeSource,), {})
    fake_snap = PriceSnapshot(
        model_id="claude-opus-4-5",
        price_input_per_million=1_400_000_000, price_output_per_million=7_500_000_000,
        currency="USD", source="dedup_test", source_url="x",
    )
    src_cls.__init__ = lambda self: FakeSource.__init__(self, [fake_snap])

    r1 = await run_check_cycle(db_session, sources=[src_cls])
    r2 = await run_check_cycle(db_session, sources=[src_cls])
    assert r1.anomalies_created == 1
    assert r2.anomalies_created == 0  # same diff, dedup


# ─── Confirm / reject anomaly ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_confirm_anomaly_writes_history_and_updates_model(db_session):
    from sqlalchemy import select
    await _seed_model(db_session)
    src_cls = type("S", (FakeSource,), {})
    fake_snap = PriceSnapshot(
        model_id="claude-opus-4-5",
        price_input_per_million=1_400_000_000, price_output_per_million=7_000_000_000,
        currency="USD", source="confirm_test", source_url="https://anthropic.com/pricing",
    )
    src_cls.__init__ = lambda self: FakeSource.__init__(self, [fake_snap])
    await run_check_cycle(db_session, sources=[src_cls])

    anomaly = (await db_session.execute(
        select(PriceAnomaly).where(PriceAnomaly.status == "pending")
    )).scalar_one()

    history = await confirm_anomaly(
        db_session, anomaly_id=anomaly.id, confirmed_by="ops@test.com"
    )
    assert history.price_input_per_million == 1_400_000_000
    assert history.confirmed_by == "ops@test.com"

    # Live model row updated
    m = (await db_session.execute(
        select(Model).where(Model.model_id == "claude-opus-4-5")
    )).scalar_one()
    assert m.price_input_per_million == 1_400_000_000
    assert m.price_set_by == "ops@test.com"
    assert m.price_set_at is not None

    # Anomaly resolved
    a2 = await db_session.get(PriceAnomaly, anomaly.id)
    assert a2.status == "confirmed"
    assert a2.resolved_by == "ops@test.com"


@pytest.mark.asyncio
async def test_reject_anomaly_keeps_db_price(db_session):
    from sqlalchemy import select
    await _seed_model(db_session)
    src_cls = type("S", (FakeSource,), {})
    fake_snap = PriceSnapshot(
        model_id="claude-opus-4-5",
        price_input_per_million=99_999_999_999, price_output_per_million=7_500_000_000,
        currency="USD", source="reject_test", source_url="x",
    )
    src_cls.__init__ = lambda self: FakeSource.__init__(self, [fake_snap])
    await run_check_cycle(db_session, sources=[src_cls])
    anomaly = (await db_session.execute(
        select(PriceAnomaly).where(PriceAnomaly.status == "pending")
    )).scalar_one()

    await reject_anomaly(
        db_session, anomaly_id=anomaly.id, rejected_by="ops@test.com",
        reason="page parse error",
    )
    a2 = await db_session.get(PriceAnomaly, anomaly.id)
    assert a2.status == "rejected"
    # DB price unchanged
    m = (await db_session.execute(
        select(Model).where(Model.model_id == "claude-opus-4-5")
    )).scalar_one()
    assert m.price_input_per_million == 1_500_000_000


@pytest.mark.asyncio
async def test_get_active_price_version_id_returns_latest(db_session):
    from datetime import datetime, timedelta, timezone
    await _seed_model(db_session)
    now = datetime.now(timezone.utc)
    db_session.add(ModelPriceHistory(
        model_id="claude-opus-4-5", effective_at=now - timedelta(days=10),
        price_input_per_million=1_500_000_000, price_output_per_million=7_500_000_000,
        currency="USD", source="manual",
    ))
    await db_session.flush()
    db_session.add(ModelPriceHistory(
        model_id="claude-opus-4-5", effective_at=now,
        price_input_per_million=1_400_000_000, price_output_per_million=7_500_000_000,
        currency="USD", source="manual",
    ))
    await db_session.flush()

    pid = await get_active_price_version_id(db_session, model_id="claude-opus-4-5")
    assert pid is not None
    row = await db_session.get(ModelPriceHistory, pid)
    # Should pick the newest (1_400_000_000)
    assert row.price_input_per_million == 1_400_000_000


# ─── Anthropic scraper smoke test (mocked HTML) ───────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_anthropic_web_parses_real_shape():
    fake_html = """
    <html><body>
    <div>Claude Opus 4.5 ... Input $15 / MTok ... Output $75 / MTok ...</div>
    <div>Claude Sonnet 4.5 ... Input $3 / MTok ... Output $15 / MTok ...</div>
    </body></html>
    """
    respx.get("https://www.anthropic.com/pricing").mock(
        return_value=Response(200, text=fake_html)
    )
    src = AnthropicWebSource()
    snaps = await src.fetch_all()
    by_id = {s.model_id: s for s in snaps}
    assert "claude-opus-4-5" in by_id
    assert by_id["claude-opus-4-5"].price_input_per_million == 1_500_000_000
    assert by_id["claude-opus-4-5"].price_output_per_million == 7_500_000_000
    assert by_id["claude-sonnet-4-5"].price_input_per_million == 300_000_000


@pytest.mark.asyncio
@respx.mock
async def test_anthropic_web_raises_on_unparseable():
    respx.get("https://www.anthropic.com/pricing").mock(
        return_value=Response(200, text="<html>nothing recognizable</html>")
    )
    with pytest.raises(PriceSourceError):
        await AnthropicWebSource().fetch_all()


@pytest.mark.asyncio
@respx.mock
async def test_anthropic_web_raises_on_http_error():
    respx.get("https://www.anthropic.com/pricing").mock(
        return_value=Response(503, text="overloaded")
    )
    with pytest.raises(PriceSourceError):
        await AnthropicWebSource().fetch_all()
