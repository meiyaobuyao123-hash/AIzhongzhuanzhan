"""FastAPI dependency injectors."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import authenticate, parse_authorization
from app.db import SessionLocal
from app.jwt_auth import InvalidToken, decode_token, is_session_revoked
from app.models.orm import ApiKey, User


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def authenticate_request(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
    db: AsyncSession = None,  # set by route
) -> tuple[User, ApiKey]:
    """Resolve Prism Key → (user, api_key). Use as a route helper, not a Depends —
    we need the db Session passed in."""
    raw_key = parse_authorization(authorization, x_api_key)
    return await authenticate(raw_key, db)


def client_ip(request: Request) -> str | None:
    """Best-effort client IP from common reverse-proxy headers."""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    real = request.headers.get("x-real-ip")
    if real:
        return real.strip()
    return request.client.host if request.client else None


async def current_user(
    authorization: str | None,
    db: AsyncSession,
) -> User:
    """Resolve a JWT bearer token to a User. Raises if missing / invalid /
    revoked / disabled.

    Used by web-console endpoints (anything under /account, /usage)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise InvalidToken("Missing Authorization: Bearer ... header")
    token = authorization[7:].strip()
    payload = decode_token(token)
    jti = payload.get("jti")
    sub = payload.get("sub")
    if not jti or not sub:
        raise InvalidToken("Token payload incomplete")
    if await is_session_revoked(jti, db):
        from app.jwt_auth import RevokedToken
        raise RevokedToken("Session has been revoked")
    user = await db.get(User, int(sub))
    if user is None or not user.enabled:
        from app.errors import UserDisabled
        raise UserDisabled("User account no longer active")
    return user
