"""JWT issue + decode + session revoke tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.jwt_auth import (
    ExpiredToken,
    InvalidToken,
    create_session_record,
    decode_token,
    is_session_revoked,
    issue_token,
    revoke_session,
)
from app.models.orm import User


@pytest.mark.asyncio
async def test_issue_and_decode_roundtrip(db_session):
    user = User(email="x@example.com", email_verified=True)
    db_session.add(user)
    await db_session.flush()

    token, jti, expires_at = issue_token(user.id, tier=user.tier)
    payload = decode_token(token)
    assert payload["sub"] == str(user.id)
    assert payload["jti"] == jti
    assert payload["tier"] == user.tier
    assert expires_at > datetime.now(timezone.utc)


def test_decode_garbage_raises():
    with pytest.raises(InvalidToken):
        decode_token("not-a-jwt")


def test_decode_with_wrong_secret_raises(monkeypatch):
    from jose import jwt as jose_jwt

    bogus = jose_jwt.encode({"sub": "1"}, "wrong-secret", algorithm="HS256")
    with pytest.raises(InvalidToken):
        decode_token(bogus)


def test_decode_expired_raises():
    """Issue a token with negative TTL by hand and verify ExpiredToken."""
    from jose import jwt as jose_jwt

    from app.config import settings

    payload = {
        "sub": "42",
        "jti": "test-expired",
        "iat": int((datetime.now(timezone.utc) - timedelta(days=10)).timestamp()),
        "exp": int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp()),
        "tier": "self-serve",
    }
    expired = jose_jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    with pytest.raises(ExpiredToken):
        decode_token(expired)


@pytest.mark.asyncio
async def test_session_revocation_flow(db_session):
    user = User(email="alice@example.com", email_verified=True)
    db_session.add(user)
    await db_session.flush()

    _, jti, expires_at = issue_token(user.id, tier=user.tier)
    await create_session_record(
        db_session, user_id=user.id, jti=jti, expires_at=expires_at,
    )
    await db_session.commit()

    # Initially not revoked
    assert not await is_session_revoked(jti, db_session)

    # Revoke
    revoked = await revoke_session(jti, db_session)
    assert revoked is True
    await db_session.commit()

    # Now appears revoked
    assert await is_session_revoked(jti, db_session)

    # Revoking again is a no-op
    revoked2 = await revoke_session(jti, db_session)
    assert revoked2 is False


@pytest.mark.asyncio
async def test_unknown_jti_treated_as_revoked(db_session):
    """A jti with no row in sessions table = revoked (defense in depth)."""
    assert await is_session_revoked("nonexistent-jti", db_session)
