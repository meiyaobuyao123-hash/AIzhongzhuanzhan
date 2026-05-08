"""Usage analytics routes: pagination, filters, distinct models, channel→models breakdown."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.models.orm import ApiKey, Channel, UsageLog, User


@asynccontextmanager
async def _build_app(db_engine):
    from app.deps import get_db
    from app.main import app

    _, Session = db_engine

    async def override_get_db():
        async with Session() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield app
    finally:
        app.dependency_overrides.clear()


async def _seed(Session) -> tuple[int, str]:
    """Create user + key + channels + a fixed mix of usage_logs.

    Returns (user_id, jwt_token).
    """
    from argon2 import PasswordHasher

    from app.jwt_auth import create_session_record, issue_token

    ph = PasswordHasher()
    async with Session() as db:
        user = User(email="usage@x.com", password_hash=ph.hash("long-pwd-12345"),
                    email_verified=True)
        db.add(user)
        await db.flush()

        ak = ApiKey(user_id=user.id, key_hash="dummy", key_prefix="sk-prism-aaa",
                    key_last4="zzzz", name="t")
        db.add(ak)

        ch1 = Channel(provider="openai", name="OpenAI primary",
                      base_url="https://api.openai.com",
                      upstream_key_encrypted="enc", models='[]')
        ch2 = Channel(provider="anthropic", name="Anthropic primary",
                      base_url="https://api.anthropic.com",
                      upstream_key_encrypted="enc", models='[]')
        db.add_all([ch1, ch2])
        await db.flush()

        now = datetime.now(timezone.utc)

        def _log(request_id: str, model: str, channel_id: int,
                 status: str = "ok", age_min: int = 1,
                 prompt: int = 100, completion: int = 50,
                 cost: int = 1000):
            return UsageLog(
                request_id=request_id, user_id=user.id, api_key_id=ak.id,
                channel_id=channel_id, model_id=model,
                prompt_tokens=prompt, completion_tokens=completion,
                cost_micro_cents=cost, status=status,
                http_status=200 if status == "ok" else 500,
                latency_ms=300,
                created_at=now - timedelta(minutes=age_min),
            )

        # 6 OpenAI logs (4 gpt-4o + 2 gpt-4o-mini), 3 Anthropic, 1 error
        logs = [
            _log("r1", "gpt-4o",      ch1.id, age_min=1,  cost=5000),
            _log("r2", "gpt-4o",      ch1.id, age_min=2,  cost=5500),
            _log("r3", "gpt-4o",      ch1.id, age_min=5,  cost=6000),
            _log("r4", "gpt-4o",      ch1.id, age_min=8,  cost=4500),
            _log("r5", "gpt-4o-mini", ch1.id, age_min=10, cost=300),
            _log("r6", "gpt-4o-mini", ch1.id, age_min=12, cost=350),
            _log("r7", "claude-haiku-4-5", ch2.id, age_min=15, cost=2000),
            _log("r8", "claude-haiku-4-5", ch2.id, age_min=20, cost=2100),
            _log("r9", "claude-opus-4-5",  ch2.id, age_min=22, cost=12000),
            _log("r10", "gpt-4o",     ch1.id, age_min=25, status="error", cost=0),
            # Old log (outside default 7-day window for /requests but inside stats 30d)
            _log("r-old", "gpt-4o",   ch1.id, age_min=8 * 24 * 60, cost=8000),
        ]
        for log in logs:
            db.add(log)

        token, jti, expires_at = issue_token(user.id, tier=user.tier)
        await create_session_record(
            db, user_id=user.id, jti=jti, expires_at=expires_at,
            user_agent=None, ip=None,
        )
        await db.commit()
        return user.id, token


@pytest.mark.asyncio
async def test_requests_returns_total_and_pages(db_engine):
    _, Session = db_engine
    _, token = await _seed(Session)

    async with _build_app(db_engine) as app, AsyncClient(
        transport=ASGITransport(app=app), base_url="http://t",
    ) as client:
        r = await client.get(
            "/usage/requests?page=1&size=4",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    body = r.json()
    # 10 logs are within the default 7-day window (one is older)
    assert body["total"] == 10
    assert body["pages"] == 3       # ceil(10/4)
    assert body["page"] == 1
    assert body["size"] == 4
    assert len(body["data"]) == 4
    # Newest first: r1 should be at top
    assert body["data"][0]["request_id"] == "r1"


@pytest.mark.asyncio
async def test_requests_filter_by_status(db_engine):
    _, Session = db_engine
    _, token = await _seed(Session)

    async with _build_app(db_engine) as app, AsyncClient(
        transport=ASGITransport(app=app), base_url="http://t",
    ) as client:
        r = await client.get(
            "/usage/requests?status=error",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["data"][0]["request_id"] == "r10"
    assert body["data"][0]["status"] == "error"


@pytest.mark.asyncio
async def test_requests_until_filter_excludes_recent(db_engine):
    """Setting until=20min-ago should drop the 5 newest logs."""
    _, Session = db_engine
    _, token = await _seed(Session)

    # Cutoff at 13 min ago: drops r1..r6 (1-12 min), keeps r7..r10 (15-25 min).
    # r-old (8 days) is also dropped because default since = now-7d.
    until = (datetime.now(timezone.utc) - timedelta(minutes=13)).isoformat()
    async with _build_app(db_engine) as app, AsyncClient(
        transport=ASGITransport(app=app), base_url="http://t",
    ) as client:
        r = await client.get(
            "/usage/requests", params={"until": until},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 4
    assert {row["request_id"] for row in body["data"]} == {"r7", "r8", "r9", "r10"}


@pytest.mark.asyncio
async def test_requests_filter_by_model(db_engine):
    _, Session = db_engine
    _, token = await _seed(Session)

    async with _build_app(db_engine) as app, AsyncClient(
        transport=ASGITransport(app=app), base_url="http://t",
    ) as client:
        r = await client.get(
            "/usage/requests?model=claude-haiku-4-5",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert {row["request_id"] for row in body["data"]} == {"r7", "r8"}


@pytest.mark.asyncio
async def test_models_endpoint_lists_distinct_used_models(db_engine):
    _, Session = db_engine
    _, token = await _seed(Session)

    async with _build_app(db_engine) as app, AsyncClient(
        transport=ASGITransport(app=app), base_url="http://t",
    ) as client:
        r = await client.get(
            "/usage/models",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    body = r.json()
    by_id = {row["model_id"]: row for row in body["data"]}
    assert set(by_id.keys()) == {"gpt-4o", "gpt-4o-mini",
                                  "claude-haiku-4-5", "claude-opus-4-5"}
    # gpt-4o has 6 (5 fresh + 1 old) total log entries
    assert by_id["gpt-4o"]["requests"] == 6
    assert by_id["claude-haiku-4-5"]["requests"] == 2
    # Most-recently-used first: r1 (gpt-4o) is newest
    assert body["data"][0]["model_id"] == "gpt-4o"


@pytest.mark.asyncio
async def test_stats_channel_groupby_includes_models(db_engine):
    """group_by=channel response items must carry a `models` array of sub-rows."""
    _, Session = db_engine
    _, token = await _seed(Session)

    async with _build_app(db_engine) as app, AsyncClient(
        transport=ASGITransport(app=app), base_url="http://t",
    ) as client:
        r = await client.get(
            "/usage/stats?group_by=channel",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    body = r.json()
    # 2 channels expected
    assert len(body["data"]) == 2
    # Sorted by cost descending — ch1 (OpenAI) had bigger volume
    by_name = {row["channel_name"]: row for row in body["data"]}
    assert "OpenAI primary" in by_name
    assert "Anthropic primary" in by_name

    oai = by_name["OpenAI primary"]
    assert "models" in oai
    oai_model_ids = {m["model_id"] for m in oai["models"]}
    assert oai_model_ids == {"gpt-4o", "gpt-4o-mini"}

    ant = by_name["Anthropic primary"]
    ant_model_ids = {m["model_id"] for m in ant["models"]}
    assert ant_model_ids == {"claude-opus-4-5", "claude-haiku-4-5"}


@pytest.mark.asyncio
async def test_stats_summary_has_token_totals(db_engine):
    _, Session = db_engine
    _, token = await _seed(Session)

    async with _build_app(db_engine) as app, AsyncClient(
        transport=ASGITransport(app=app), base_url="http://t",
    ) as client:
        r = await client.get(
            "/usage/stats?group_by=model",
            headers={"Authorization": f"Bearer {token}"},
        )
    body = r.json()
    s = body["summary"]
    # 11 logs × 100 prompt = 1100; 11 × 50 completion = 550
    assert s["total_requests"] == 11
    assert s["total_input_tokens"] == 1100
    assert s["total_output_tokens"] == 550


@pytest.mark.asyncio
async def test_requests_pagination_page_2(db_engine):
    _, Session = db_engine
    _, token = await _seed(Session)

    async with _build_app(db_engine) as app, AsyncClient(
        transport=ASGITransport(app=app), base_url="http://t",
    ) as client:
        r = await client.get(
            "/usage/requests?page=2&size=4",
            headers={"Authorization": f"Bearer {token}"},
        )
    body = r.json()
    assert body["page"] == 2
    assert len(body["data"]) == 4
    # Page 2 with size 4: rows 5..8 (newest first → r5, r6, r7, r8)
    assert {row["request_id"] for row in body["data"]} == {"r5", "r6", "r7", "r8"}
