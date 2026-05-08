"""Full auth flow: register → verify → login → logout."""

from __future__ import annotations

from contextlib import asynccontextmanager

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select


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


@pytest.mark.asyncio
async def test_register_creates_user_pending(db_engine):
    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post("/auth/register", json={
                "email": "new@example.com",
                "password": "long-pwd-12345",
            })
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "new@example.com"
    assert body["status"] == "pending_verification"


@pytest.mark.asyncio
async def test_register_email_already_taken(db_engine):
    from app.models.orm import User

    _, Session = db_engine
    async with Session() as db:
        db.add(User(email="taken@example.com", password_hash="dummy"))
        await db.commit()

    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post("/auth/register", json={
                "email": "taken@example.com",
                "password": "long-pwd-12345",
            })
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "email_taken"


@pytest.mark.asyncio
async def test_register_invalid_email(db_engine):
    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post("/auth/register", json={
                "email": "not-an-email",
                "password": "long-pwd-12345",
            })
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_register_weak_password(db_engine):
    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post("/auth/register", json={
                "email": "weak@example.com",
                "password": "short",
            })
    assert r.status_code == 400  # min length 10


@pytest.mark.asyncio
async def test_login_requires_verified_email(db_engine):
    """Register → try login before verifying → expect 403."""
    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post("/auth/register", json={
                "email": "unverified@example.com",
                "password": "long-pwd-12345",
            })
            assert r.status_code == 201
            r2 = await ac.post("/auth/login", json={
                "email": "unverified@example.com",
                "password": "long-pwd-12345",
            })
    assert r2.status_code == 403
    assert r2.json()["error"]["code"] == "email_not_verified"


@pytest.mark.asyncio
async def test_full_register_verify_login_flow(db_engine):
    """End-to-end: register → grab token from DB → verify → login → /account/me."""
    from app.models.orm import EmailVerification, User

    _, Session = db_engine

    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Register
            r = await ac.post("/auth/register", json={
                "email": "alice@example.com", "password": "long-pwd-12345",
            })
            assert r.status_code == 201

            # Pull verification token from DB (testing shortcut)
            async with Session() as db:
                row = await db.execute(select(EmailVerification))
                ev = row.scalar_one()
                # We hashed the token; test needs the plain. We can't recover it.
                # Instead, mark the user verified directly to simulate clicking the link.
                user = (await db.execute(select(User).where(User.email == "alice@example.com"))).scalar_one()
                user.email_verified = True
                ev.used_at = ev.created_at  # mark used
                await db.commit()

            # Now login should succeed
            r2 = await ac.post("/auth/login", json={
                "email": "alice@example.com", "password": "long-pwd-12345",
            })
            assert r2.status_code == 200
            data = r2.json()
            assert "token" in data
            assert data["user"]["email"] == "alice@example.com"
            token = data["token"]

            # /account/me with the token
            r3 = await ac.get("/account/me", headers={"Authorization": f"Bearer {token}"})
            assert r3.status_code == 200
            me = r3.json()
            assert me["email"] == "alice@example.com"
            assert me["balance_usd"] == 0
            assert me["default_rpm"] == 60  # < $50 → 60 RPM tier

            # Logout
            r4 = await ac.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
            assert r4.status_code == 200
            assert r4.json()["logged_out"] is True

            # /account/me with same token now fails (revoked)
            r5 = await ac.get("/account/me", headers={"Authorization": f"Bearer {token}"})
            assert r5.status_code == 401
            assert r5.json()["error"]["code"] == "revoked_token"


@pytest.mark.asyncio
async def test_account_api_keys_crud(db_engine):
    """Full self-service API key lifecycle through HTTP."""
    from app.models.orm import User

    _, Session = db_engine
    async with Session() as db:
        # Create a verified user with hashed pwd
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        user = User(
            email="bob@example.com",
            password_hash=ph.hash("long-pwd-12345"),
            email_verified=True,
            balance_micro_cents=10_000_000_00,
        )
        db.add(user)
        await db.commit()

    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post("/auth/login", json={
                "email": "bob@example.com", "password": "long-pwd-12345",
            })
            assert r.status_code == 200
            token = r.json()["token"]
            h = {"Authorization": f"Bearer {token}"}

            # List empty
            r_list = await ac.get("/account/api-keys", headers=h)
            assert r_list.status_code == 200
            assert r_list.json()["data"] == []

            # Create
            r_new = await ac.post(
                "/account/api-keys",
                headers=h,
                json={"name": "My laptop", "rate_limit_rpm": 120},
            )
            assert r_new.status_code == 201
            new_key = r_new.json()
            assert new_key["key"].startswith("sk-prism-")
            assert new_key["name"] == "My laptop"
            assert new_key["rate_limit_rpm"] == 120
            kid = new_key["id"]

            # List has one
            r_list2 = await ac.get("/account/api-keys", headers=h)
            assert len(r_list2.json()["data"]) == 1
            # Full key NOT returned in list
            assert "key" not in r_list2.json()["data"][0]

            # Update
            r_upd = await ac.patch(
                f"/account/api-keys/{kid}",
                headers=h,
                json={"name": "renamed", "rate_limit_rpm": 200},
            )
            assert r_upd.status_code == 200
            assert r_upd.json()["name"] == "renamed"
            assert r_upd.json()["rate_limit_rpm"] == 200

            # Delete (soft)
            r_del = await ac.delete(f"/account/api-keys/{kid}", headers=h)
            assert r_del.status_code == 200
            assert r_del.json()["revoked"] is True

            # Re-list shows it disabled
            r_list3 = await ac.get("/account/api-keys", headers=h)
            assert r_list3.json()["data"][0]["enabled"] is False


@pytest.mark.asyncio
async def test_account_balance_endpoint(db_engine):
    from argon2 import PasswordHasher

    from app.models.orm import User

    _, Session = db_engine
    ph = PasswordHasher()
    async with Session() as db:
        db.add(User(
            email="rich@example.com",
            password_hash=ph.hash("long-pwd-12345"),
            email_verified=True,
            balance_micro_cents=12_345_000_000,  # $123.45
            total_topped_up_micro_cents=20_000_000_000,  # $200 cumulative
        ))
        await db.commit()

    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post("/auth/login", json={
                "email": "rich@example.com", "password": "long-pwd-12345",
            })
            token = r.json()["token"]
            r_bal = await ac.get(
                "/account/balance",
                headers={"Authorization": f"Bearer {token}"},
            )
    assert r_bal.status_code == 200
    body = r_bal.json()
    assert body["balance_usd"] == 123.45
    assert body["total_topped_up_usd"] == 200.0


@pytest.mark.asyncio
async def test_no_auth_returns_401(db_engine):
    async with _build_app(db_engine) as app:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.get("/account/me")
    assert r.status_code == 401
