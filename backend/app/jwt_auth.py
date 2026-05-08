"""JWT signing + verification + session bookkeeping.

JWT structure:
    header:  {alg: HS256, typ: JWT}
    payload: {sub: <user_id>, jti: <uuid>, exp, iat, tier}
    signed with PRISM_JWT_SECRET

We additionally maintain a `sessions` table (jti index) so users can revoke
specific sessions and admin can force-logout. Every authenticated request must
match a non-revoked session row.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.errors import PrismException
from app.models.orm import Session as SessionModel

JWT_ALGO = "HS256"


class InvalidToken(PrismException):
    status_code = 401
    error_type = "authentication_error"
    code = "invalid_token"


class ExpiredToken(InvalidToken):
    code = "expired_token"


class RevokedToken(InvalidToken):
    code = "revoked_token"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_jti() -> str:
    return secrets.token_urlsafe(16)


def issue_token(
    user_id: int, *, tier: str, ttl_days: int | None = None
) -> tuple[str, str, datetime]:
    """Returns (token_string, jti, expires_at).

    Caller is responsible for inserting a sessions row with the returned jti.
    """
    ttl = ttl_days or settings.jwt_ttl_days
    iat = _now()
    exp = iat + timedelta(days=ttl)
    jti = _make_jti()
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "iat": int(iat.timestamp()),
        "exp": int(exp.timestamp()),
        "tier": tier,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGO)
    return token, jti, exp


def decode_token(token: str) -> dict:
    """Verify signature + expiry. Returns payload dict or raises."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError as exc:
        raise ExpiredToken("Session expired, please login again") from exc
    except JWTError as exc:
        raise InvalidToken(f"Invalid session token: {exc}") from exc


async def is_session_revoked(jti: str, db: AsyncSession) -> bool:
    """True if jti has no row, or the row's revoked_at is not null."""
    row = await db.execute(select(SessionModel).where(SessionModel.jti == jti))
    sess = row.scalar_one_or_none()
    if sess is None:
        return True
    return sess.revoked_at is not None


async def create_session_record(
    db: AsyncSession,
    *,
    user_id: int,
    jti: str,
    expires_at: datetime,
    user_agent: str | None = None,
    ip: str | None = None,
) -> SessionModel:
    s = SessionModel(
        user_id=user_id,
        jti=jti,
        expires_at=expires_at,
        user_agent=user_agent,
        ip=ip,
    )
    db.add(s)
    return s


async def revoke_session(jti: str, db: AsyncSession) -> bool:
    """Mark a session revoked. Returns True iff a row was found and updated."""
    row = await db.execute(select(SessionModel).where(SessionModel.jti == jti))
    sess = row.scalar_one_or_none()
    if sess is None or sess.revoked_at is not None:
        return False
    sess.revoked_at = _now()
    return True
