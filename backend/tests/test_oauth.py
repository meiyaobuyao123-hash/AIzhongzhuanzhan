"""OAuth flow tests with mocked upstream."""

from __future__ import annotations

from contextlib import asynccontextmanager

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import select


@asynccontextmanager
async def _build_app(db_engine, monkeypatch=None):
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


def _configure_oauth(monkeypatch):
    """Stub OAuth config so providers report 'configured'."""
    from app.config import settings

    monkeypatch.setattr(settings, "oauth_github_client_id", "test-gh-id")
    monkeypatch.setattr(settings, "oauth_github_client_secret", "test-gh-secret")
    monkeypatch.setattr(settings, "oauth_google_client_id", "test-go-id")
    monkeypatch.setattr(settings, "oauth_google_client_secret", "test-go-secret")
    monkeypatch.setattr(settings, "oauth_redirect_base", "http://test")
    monkeypatch.setattr(settings, "frontend_base", "http://test/frontend")


@pytest.mark.asyncio
async def test_authorize_redirects_to_github(db_engine, monkeypatch):
    _configure_oauth(monkeypatch)
    async with _build_app(db_engine) as app:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as ac:
            r = await ac.get("/auth/oauth/github/authorize")
    assert r.status_code == 302
    loc = r.headers["location"]
    assert loc.startswith("https://github.com/login/oauth/authorize")
    assert "client_id=test-gh-id" in loc
    assert "state=" in loc


@pytest.mark.asyncio
async def test_authorize_unconfigured_returns_503(db_engine, monkeypatch):
    """When client_id/secret not set, /authorize returns 503."""
    from app.config import settings

    monkeypatch.setattr(settings, "oauth_github_client_id", "")
    monkeypatch.setattr(settings, "oauth_github_client_secret", "")

    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.get("/auth/oauth/github/authorize")
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "oauth_disabled"


@pytest.mark.asyncio
async def test_callback_invalid_state_rejected(db_engine, monkeypatch):
    _configure_oauth(monkeypatch)
    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.get("/auth/oauth/github/callback?code=abc&state=fake-state")
    assert r.status_code == 400
    assert "Invalid or expired OAuth state" in r.json()["error"]["message"]


@pytest.mark.asyncio
@respx.mock
async def test_full_github_oauth_first_time_user(db_engine, monkeypatch):
    """End-to-end: authorize → fake provider response → user created → redirected with JWT."""
    _configure_oauth(monkeypatch)

    # Step 1: get authorize → grab state from URL
    async with _build_app(db_engine) as app:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as ac:
            r1 = await ac.get("/auth/oauth/github/authorize")
            assert r1.status_code == 302
            from urllib.parse import parse_qs, urlparse
            qs = parse_qs(urlparse(r1.headers["location"]).query)
            state = qs["state"][0]

            # Step 2: mock GitHub upstream
            respx.post("https://github.com/login/oauth/access_token").mock(
                return_value=Response(200, json={"access_token": "gh-tok-xyz", "scope": "read:user"})
            )
            respx.get("https://api.github.com/user").mock(
                return_value=Response(200, json={
                    "id": 12345,
                    "login": "alice",
                    "name": "Alice GitHub",
                    "email": "alice@gh.example",
                    "avatar_url": "https://gh.example/avatar.png",
                })
            )

            # Step 3: hit our callback
            r2 = await ac.get(f"/auth/oauth/github/callback?code=auth-code-1&state={state}")

    assert r2.status_code == 302
    redirect_loc = r2.headers["location"]
    assert redirect_loc.startswith("http://test/frontend/console#")
    assert "token=" in redirect_loc

    # Verify user + oauth_account were created
    from app.models.orm import OAuthAccount, User
    _, Session = db_engine
    async with Session() as db:
        u = (await db.execute(select(User).where(User.email == "alice@gh.example"))).scalar_one()
        assert u.email_verified is True
        assert u.display_name == "Alice GitHub"
        assert u.avatar_url == "https://gh.example/avatar.png"

        oacc = (await db.execute(
            select(OAuthAccount).where(OAuthAccount.user_id == u.id)
        )).scalar_one()
        assert oacc.provider == "github"
        assert oacc.provider_uid == "12345"
        # Encrypted (not plaintext)
        assert oacc.access_token_encrypted is not None
        assert "gh-tok-xyz" not in oacc.access_token_encrypted


@pytest.mark.asyncio
@respx.mock
async def test_oauth_returning_user_links_correctly(db_engine, monkeypatch):
    """A user who has already used GitHub OAuth → log them back in (don't double-create)."""
    _configure_oauth(monkeypatch)

    from app.models.orm import OAuthAccount, User
    _, Session = db_engine

    # Pre-seed an existing user + oauth_account
    async with Session() as db:
        u = User(
            email="returning@gh.example",
            display_name="Returning User",
            email_verified=True,
        )
        db.add(u)
        await db.flush()
        db.add(OAuthAccount(
            user_id=u.id,
            provider="github",
            provider_uid="99999",
            provider_email="returning@gh.example",
            access_token_encrypted="dummy",
        ))
        await db.commit()
        existing_user_id = u.id

    async with _build_app(db_engine) as app:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False
        ) as ac:
            r1 = await ac.get("/auth/oauth/github/authorize")
            from urllib.parse import parse_qs, urlparse
            state = parse_qs(urlparse(r1.headers["location"]).query)["state"][0]

            respx.post("https://github.com/login/oauth/access_token").mock(
                return_value=Response(200, json={"access_token": "new-gh-tok"})
            )
            respx.get("https://api.github.com/user").mock(
                return_value=Response(200, json={
                    "id": 99999,
                    "login": "returning",
                    "name": "Returning Updated",  # name changed
                    "email": "returning@gh.example",
                })
            )

            r2 = await ac.get(f"/auth/oauth/github/callback?code=c&state={state}")

    assert r2.status_code == 302

    # No duplicate users created
    async with Session() as db:
        users = (await db.execute(select(User))).scalars().all()
        assert len(users) == 1
        assert users[0].id == existing_user_id


@pytest.mark.asyncio
async def test_providers_endpoint(db_engine, monkeypatch):
    _configure_oauth(monkeypatch)
    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.get("/auth/oauth/providers")
    assert r.status_code == 200
    data = r.json()["data"]
    by_name = {p["name"]: p["configured"] for p in data}
    assert by_name["github"] is True
    assert by_name["google"] is True
