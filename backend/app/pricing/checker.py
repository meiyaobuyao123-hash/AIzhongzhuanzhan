"""Price-tracking checker: orchestrate sources → diff DB → write anomalies.

Public surface used by CLI + lifespan:
  - run_check_cycle(db, threshold_pct=1.0) — one full pass
  - confirm_anomaly(db, anomaly_id, by) — apply observed value to DB +
    write history row
  - reject_anomaly(db, anomaly_id, by) — keep DB price, mark anomaly resolved
  - get_active_price_version_id(db, model_id) — billing.recorder uses this
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import logger
from app.models.orm import Model, ModelPriceHistory, PriceAnomaly
from app.pricing.models import PriceSnapshot, PriceSourceError
from app.pricing.sources import REGISTRY


def _diff_pct(observed: int, current: int) -> float:
    if current == 0:
        return 100.0 if observed != 0 else 0.0
    return abs(observed - current) / current * 100.0


@dataclass
class CheckResult:
    sources_run: int
    sources_failed: list[tuple[str, str]]   # [(source_name, error_msg), ...]
    snapshots_collected: int
    anomalies_created: int
    snapshots_unchanged: int
    unknown_models: int                       # observed models we don't host


async def run_check_cycle(
    db: AsyncSession,
    *,
    threshold_pct: float = 1.0,
    sources: Iterable[type] | None = None,
) -> CheckResult:
    """Pull from every source, diff against current DB price, insert
    PriceAnomaly rows for diffs > threshold_pct.

    Does NOT auto-update DB prices — that requires explicit
    confirm_anomaly() call (typically by a human via CLI).
    """
    source_classes = list(sources or REGISTRY)
    failed: list[tuple[str, str]] = []
    snaps: list[PriceSnapshot] = []
    sources_run = 0

    for cls in source_classes:
        sources_run += 1
        src = cls()
        try:
            got = await src.fetch_all()
        except PriceSourceError as exc:
            logger.warning("price_source_failed",
                            source=src.name, error=str(exc))
            failed.append((src.name, str(exc)))
            continue
        except Exception as exc:
            logger.error("price_source_unexpected",
                          source=src.name, error=str(exc))
            failed.append((src.name, f"unexpected: {exc}"))
            continue

        logger.info("price_source_fetched",
                     source=src.name, count=len(got))
        snaps.extend(got)

    anomalies_created = 0
    unchanged = 0
    unknown = 0

    for snap in snaps:
        m = (await db.execute(
            select(Model).where(Model.model_id == snap.model_id)
        )).scalar_one_or_none()
        if m is None:
            unknown += 1
            continue

        diff_in = _diff_pct(snap.price_input_per_million, m.price_input_per_million)
        diff_out = _diff_pct(snap.price_output_per_million, m.price_output_per_million)

        if max(diff_in, diff_out) <= threshold_pct:
            unchanged += 1
            continue

        # Suppress duplicates: if there's already a pending anomaly for this
        # (model, source) with the same observed numbers, don't insert again.
        dup = (await db.execute(
            select(PriceAnomaly)
            .where(PriceAnomaly.model_id == snap.model_id)
            .where(PriceAnomaly.source == snap.source)
            .where(PriceAnomaly.status == "pending")
            .where(PriceAnomaly.observed_input == snap.price_input_per_million)
            .where(PriceAnomaly.observed_output == snap.price_output_per_million)
        )).scalar_one_or_none()
        if dup is not None:
            unchanged += 1
            continue

        anomaly = PriceAnomaly(
            model_id=snap.model_id,
            source=snap.source,
            current_db_input=m.price_input_per_million,
            current_db_output=m.price_output_per_million,
            observed_input=snap.price_input_per_million,
            observed_output=snap.price_output_per_million,
            diff_pct_input=diff_in,
            diff_pct_output=diff_out,
            status="pending",
            notes=f"diff in={diff_in:.2f}% out={diff_out:.2f}% (threshold {threshold_pct}%)",
        )
        db.add(anomaly)
        anomalies_created += 1
        logger.warning(
            "price_anomaly_detected",
            model_id=snap.model_id,
            source=snap.source,
            diff_in_pct=round(diff_in, 2),
            diff_out_pct=round(diff_out, 2),
        )

    await db.commit()
    return CheckResult(
        sources_run=sources_run,
        sources_failed=failed,
        snapshots_collected=len(snaps),
        anomalies_created=anomalies_created,
        snapshots_unchanged=unchanged,
        unknown_models=unknown,
    )


async def confirm_anomaly(
    db: AsyncSession, *, anomaly_id: int, confirmed_by: str
) -> ModelPriceHistory:
    """Apply observed value to DB:
      1. Append model_price_history row (with effective_at=now)
      2. Update models row: price_*, price_set_at, price_set_by, price_source_url
      3. Mark anomaly status='confirmed'
    Returns the new ModelPriceHistory row.
    """
    anomaly = await db.get(PriceAnomaly, anomaly_id)
    if anomaly is None:
        raise ValueError(f"anomaly {anomaly_id} not found")
    if anomaly.status != "pending":
        raise ValueError(f"anomaly {anomaly_id} already {anomaly.status}")

    m = (await db.execute(
        select(Model).where(Model.model_id == anomaly.model_id)
    )).scalar_one_or_none()
    if m is None:
        raise ValueError(f"model {anomaly.model_id} not in catalog")

    now = datetime.now(timezone.utc)

    history = ModelPriceHistory(
        model_id=anomaly.model_id,
        effective_at=now,
        price_input_per_million=anomaly.observed_input,
        price_output_per_million=anomaly.observed_output,
        # Cache prices not part of anomaly (could be enhanced later)
        price_cache_read_per_million=m.price_cache_read_per_million,
        price_cache_write_per_million=m.price_cache_write_per_million,
        currency=m.price_currency or "USD",
        source=anomaly.source,
        source_url=m.price_source_url,
        confirmed_by=confirmed_by,
        notes=f"confirmed from anomaly {anomaly_id} (diff {anomaly.diff_pct_input:.1f}% / {anomaly.diff_pct_output:.1f}%)",
    )
    db.add(history)

    # Update live model row
    m.price_input_per_million = anomaly.observed_input
    m.price_output_per_million = anomaly.observed_output
    m.price_set_at = now
    m.price_set_by = confirmed_by

    anomaly.status = "confirmed"
    anomaly.resolved_at = now
    anomaly.resolved_by = confirmed_by

    await db.commit()
    await db.refresh(history)
    logger.info(
        "price_anomaly_confirmed",
        anomaly_id=anomaly_id, model_id=anomaly.model_id,
        new_history_id=history.id, by=confirmed_by,
    )
    return history


async def reject_anomaly(
    db: AsyncSession, *, anomaly_id: int, rejected_by: str, reason: str | None = None
) -> None:
    anomaly = await db.get(PriceAnomaly, anomaly_id)
    if anomaly is None:
        raise ValueError(f"anomaly {anomaly_id} not found")
    if anomaly.status != "pending":
        raise ValueError(f"anomaly {anomaly_id} already {anomaly.status}")
    anomaly.status = "rejected"
    anomaly.resolved_at = datetime.now(timezone.utc)
    anomaly.resolved_by = rejected_by
    if reason:
        anomaly.notes = (anomaly.notes or "") + f" | rejected: {reason}"
    await db.commit()
    logger.info("price_anomaly_rejected",
                 anomaly_id=anomaly_id, by=rejected_by, reason=reason)


async def get_active_price_version_id(
    db: AsyncSession, *, model_id: str
) -> int | None:
    """Return the most-recent ModelPriceHistory row id for `model_id`, or None
    if no history exists yet (legacy data).

    Used by billing.recorder when stamping usage_log.price_version_id so future
    refunds are computable per request.
    """
    row = (await db.execute(
        select(ModelPriceHistory.id)
        .where(ModelPriceHistory.model_id == model_id)
        .order_by(ModelPriceHistory.effective_at.desc())
        .limit(1)
    )).scalar_one_or_none()
    return row


__all__ = [
    "CheckResult",
    "run_check_cycle",
    "confirm_anomaly",
    "reject_anomaly",
    "get_active_price_version_id",
]
