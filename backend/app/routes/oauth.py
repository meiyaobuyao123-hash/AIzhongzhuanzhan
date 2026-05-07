"""OAuth routes: authorize + callback for each provider.

Flow:
  GET /auth/oauth/{provider}/authorize
    → generate state (random 32-byte) → store in Redis 5min TTL
    → 302 to provider's authorize URL with our redirect_uri + state

  GET /auth/oauth/{provider}/callback?code=&state=
    → verify state in Redis → exchange code for profile
    → find/create OAuthAccount (provider, provider_uid)
    → find/create User (auto-verified, since the OAuth provider already verified)
    → issue JWT → 302 to /console#token=...
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from urllib.parse import quote, urlencode

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import record_audit
from app.config import settings
from app.crypto import encrypt
from app.deps import client_ip, get_db
from app.errors import error_response
from app.jwt_auth import create_session_record, issue_token
from app.logging_config import logger
from app.models.orm import OAuthAccount, User
from app.oauth import get_provider
from app.redis_client import get_redis

router = APIRouter(tags=["oauth"], prefix="/auth/oauth")


def _redirect_uri_for(provider_name: str) -> str:
    return f"{settings.oauth_redirect_base.rstrip('/')}/auth/oauth/{provider_name}/callback"


@router.get("/{provider_name}/authorize")
async def oauth_authorize(provider_name: str):
    p = get_provider(provider_name)
    if p is None:
        return error_response(
            503, f"OAuth provider '{provider_name}' not configured",
            "api_error", code="oauth_disabled",
        )

    state = secrets.token_urlsafe(32)
    redis = get_redis()
    await redis.set(f"prism:oauth_state:{state}", provider_name, ex=300)

    redirect_uri = _redirect_uri_for(provider_name)
    auth_url = p.authorize_redirect(state=state, redirect_uri=redirect_uri)
    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/{provider_name}/callback")
async def oauth_callback(
    provider_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_agent: str | None = Header(default=None, alias="user-agent"),
):
    p = get_provider(provider_name)
    if p is None:
        return error_response(
            503, f"OAuth provider '{provider_name}' not configured",
            "api_error", code="oauth_disabled",
        )

    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if not code or not state:
        return error_response(400, "Missing code or state", "invalid_request_error")

    redis = get_redis()
    redis_key = f"prism:oauth_state:{state}"
    expected_provider = await redis.get(redis_key)
    if expected_provider != provider_name:
        return error_response(400, "Invalid or expired OAuth state", "invalid_request_error")
    await redis.delete(redis_key)

    redirect_uri = _redirect_uri_for(provider_name)

    try:
        profile = await p.exchange_code(code=code, redirect_uri=redirect_uri)
    except Exception as exc:
        logger.warning("oauth_exchange_failed", provider=provider_name, error=str(exc))
        return error_response(
            502, f"OAuth exchange failed: {exc}",
            "api_error", code="oauth_exchange_failed",
        )

    # Find / create OAuthAccount + linked User
    oacc = (await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider_name,
            OAuthAccount.provider_uid == profile.provider_uid,
        )
    )).scalar_one_or_none()

    if oacc:
        user = await db.get(User, oacc.user_id)
        # Refresh stored access_token + email (user may have changed)
        oacc.access_token_encrypted = encrypt(profile.access_token, settings.master_key)
        if profile.email:
            oacc.provider_email = profile.email
    else:
        # New OAuth account. Try to link to existing user by email if present.
        user = None
        if profile.email:
            user = (await db.execute(
                select(User).where(User.email == profile.email)
            )).scalar_one_or_none()

        if user is None:
            # Brand-new user
            user = User(
                email=profile.email or f"oauth-{provider_name}-{profile.provider_uid}@noemail.local",
                tier="self-serve",
                email_verified=True,
                display_name=profile.display_name,
                avatar_url=profile.avatar_url,
            )
            db.add(user)
            try:
                await db.flush()
            except IntegrityError:
                await db.rollback()
                return error_response(
                    409, "Email already registered with a different login method",
                    "invalid_request_error", code="email_taken",
                )
            await record_audit(
                db, actor=f"oauth:{provider_name}", action="user.register_oauth",
                target=str(user.id), ip=client_ip(request),
                payload={"provider": provider_name, "email": profile.email},
            )

        oacc = OAuthAccount(
            user_id=user.id,
            provider=provider_name,
            provider_uid=profile.provider_uid,
            provider_email=profile.email,
            access_token_encrypted=encrypt(profile.access_token, settings.master_key),
        )
        db.add(oacc)

    # Backfill display_name / avatar_url if missing
    if not user.display_name and profile.display_name:
        user.display_name = profile.display_name
    if not user.avatar_url and profile.avatar_url:
        user.avatar_url = profile.avatar_url

    if not user.enabled:
        return error_response(403, "Account disabled", "permission_error")

    # Issue session
    token, jti, expires_at = issue_token(user.id, tier=user.tier)
    await create_session_record(
        db, user_id=user.id, jti=jti, expires_at=expires_at,
        user_agent=user_agent, ip=client_ip(request),
    )
    await record_audit(
        db, actor=f"user:{user.id}", action="user.login_oauth",
        target=str(user.id), ip=client_ip(request),
        payload={"provider": provider_name},
    )
    await db.commit()

    # Redirect frontend with the JWT in the URL fragment so JS can pick it up
    fragment = urlencode({
        "token": token,
        "expires_at": expires_at.isoformat(),
    })
    return RedirectResponse(
        url=f"{settings.frontend_base}/console#{fragment}",
        status_code=302,
    )


@router.get("/providers")
async def list_providers():
    """Used by the login page to know which buttons to show."""
    return {
        "data": [
            {"name": name, "configured": p.is_configured()}
            for name, p in __import__("app.oauth", fromlist=["PROVIDERS"]).PROVIDERS.items()
        ]
    }
