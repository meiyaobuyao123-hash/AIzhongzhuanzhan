"""Email-based auth: register / verify-email / login / logout / change-password / forgot-password.

OAuth (GitHub/Google) lives in app/routes/oauth.py.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import record_audit
from app.deps import client_ip, get_db
from app.email import send_password_reset_email, send_verification_email
from app.errors import (
    InvalidAPIKey,
    PrismException,
    error_response,
)
from app.jwt_auth import (
    create_session_record,
    issue_token,
    revoke_session,
)
from app.logging_config import logger
from app.models.orm import EmailVerification, User

router = APIRouter(tags=["auth"], prefix="/auth")
_pwd_hasher = PasswordHasher()


# ─── Request / Response models ────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=10, max_length=200)


class LoginRequest(BaseModel):
    email: str
    password: str


class VerifyEmailRequest(BaseModel):
    token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=10, max_length=200)


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=10, max_length=200)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _validate_email_or_400(email: str) -> str:
    try:
        result = validate_email(email, check_deliverability=False)
        return result.normalized
    except EmailNotValidError as exc:
        raise PrismException(
            f"Invalid email address: {exc}",
        ) from exc


async def _create_email_verif(db: AsyncSession, user: User) -> str:
    """Create an email_verifications row, return the plaintext token."""
    plain = secrets.token_urlsafe(32)
    token_hash = _pwd_hasher.hash(plain)
    db.add(EmailVerification(
        user_id=user.id,
        token_hash=token_hash,
        email=user.email,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    ))
    return plain


# ─── Routes ───────────────────────────────────────────────────────────────────


@router.post("/register", status_code=201)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        email = _validate_email_or_400(body.email)
    except PrismException as exc:
        return error_response(400, exc.message, "invalid_request_error", param="email")

    pwd_hash = _pwd_hasher.hash(body.password)
    user = User(
        email=email,
        password_hash=pwd_hash,
        tier="self-serve",
        email_verified=False,
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        return error_response(
            409, "Email already registered", "invalid_request_error",
            code="email_taken", param="email",
        )

    plain_token = await _create_email_verif(db, user)
    await record_audit(
        db, actor=f"user:{user.id}", action="user.register",
        target=str(user.id), ip=client_ip(request),
        payload={"email": email},
    )
    await db.commit()

    # Send email (non-blocking on failure)
    sent = await send_verification_email(email, plain_token)

    return {
        "user_id": user.id,
        "email": email,
        "status": "pending_verification",
        "verification_email_sent": sent,
        # In dev (no SMTP configured), the token is in the journal — admin can
        # forward it. In prod, the email goes out automatically.
    }


@router.post("/verify-email")
async def verify_email(
    body: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    # Brute-force iterate (small table for v0.2)
    rows = await db.execute(
        select(EmailVerification).where(EmailVerification.used_at.is_(None))
    )
    matched: EmailVerification | None = None
    for ev in rows.scalars():
        try:
            _pwd_hasher.verify(ev.token_hash, body.token)
            matched = ev
            break
        except VerifyMismatchError:
            continue

    if matched is None:
        return error_response(
            400, "Invalid or already-used verification token",
            "invalid_request_error", code="invalid_verification_token",
        )

    now = datetime.now(timezone.utc)
    expires = matched.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if now > expires:
        return error_response(
            400, "Verification token expired", "invalid_request_error",
            code="expired_verification_token",
        )

    user = await db.get(User, matched.user_id)
    if user is None:
        return error_response(404, "User not found", "invalid_request_error")

    user.email_verified = True
    matched.used_at = now
    await record_audit(
        db, actor=f"user:{user.id}", action="user.email_verified",
        target=str(user.id),
    )
    await db.commit()

    return {"user_id": user.id, "email_verified": True}


@router.post("/login")
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_agent: str | None = Header(default=None, alias="user-agent"),
):
    try:
        email = _validate_email_or_400(body.email)
    except PrismException:
        return error_response(401, "Invalid credentials", "authentication_error")

    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None or not user.password_hash:
        return error_response(401, "Invalid credentials", "authentication_error")
    if not user.enabled:
        return error_response(403, "User account is disabled", "permission_error")
    try:
        _pwd_hasher.verify(user.password_hash, body.password)
    except VerifyMismatchError:
        return error_response(401, "Invalid credentials", "authentication_error")

    if not user.email_verified:
        return error_response(
            403, "Email not verified — check your inbox.",
            "permission_error", code="email_not_verified",
        )

    token, jti, expires_at = issue_token(user.id, tier=user.tier)
    await create_session_record(
        db, user_id=user.id, jti=jti, expires_at=expires_at,
        user_agent=user_agent, ip=client_ip(request),
    )
    await record_audit(
        db, actor=f"user:{user.id}", action="user.login",
        target=str(user.id), ip=client_ip(request),
    )
    await db.commit()

    return {
        "token": token,
        "expires_at": expires_at.isoformat(),
        "user": {
            "id": user.id,
            "email": user.email,
            "tier": user.tier,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
        },
    }


@router.post("/logout")
async def logout(
    request: Request,
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Revoke the current session. Idempotent."""
    from app.jwt_auth import decode_token

    if not authorization or not authorization.lower().startswith("bearer "):
        return error_response(401, "No active session", "authentication_error")
    token = authorization[7:].strip()
    try:
        payload = decode_token(token)
    except PrismException:
        # Already invalid → consider logged out
        return {"logged_out": True}

    jti = payload.get("jti")
    if jti:
        revoked = await revoke_session(jti, db)
        if revoked:
            await record_audit(
                db, actor=f"user:{payload.get('sub')}", action="user.logout",
                target=str(payload.get("sub")), ip=client_ip(request),
            )
            await db.commit()
    return {"logged_out": True}


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    from app.deps import current_user

    user = await current_user(authorization, db)
    if not user.password_hash:
        return error_response(
            400, "Account has no password set (OAuth-only).",
            "invalid_request_error",
        )
    try:
        _pwd_hasher.verify(user.password_hash, body.old_password)
    except VerifyMismatchError:
        return error_response(401, "Old password incorrect", "authentication_error")

    user.password_hash = _pwd_hasher.hash(body.new_password)
    await record_audit(
        db, actor=f"user:{user.id}", action="user.change_password",
        target=str(user.id), ip=client_ip(request),
    )
    await db.commit()
    return {"changed": True}


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a password-reset email. Always returns success (don't leak existence)."""
    try:
        email = _validate_email_or_400(body.email)
    except PrismException:
        return {"sent": True}

    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user and user.enabled:
        plain = await _create_email_verif(db, user)  # reuse mechanism
        await db.commit()
        await send_password_reset_email(email, plain)
    return {"sent": True}


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(
        select(EmailVerification).where(EmailVerification.used_at.is_(None))
    )
    matched: EmailVerification | None = None
    for ev in rows.scalars():
        try:
            _pwd_hasher.verify(ev.token_hash, body.token)
            matched = ev
            break
        except VerifyMismatchError:
            continue

    if matched is None:
        return error_response(400, "Invalid or already-used token", "invalid_request_error")

    now = datetime.now(timezone.utc)
    expires = matched.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if now > expires:
        return error_response(400, "Token expired", "invalid_request_error")

    user = await db.get(User, matched.user_id)
    if not user:
        return error_response(404, "User not found", "invalid_request_error")

    user.password_hash = _pwd_hasher.hash(body.new_password)
    matched.used_at = now
    await record_audit(
        db, actor=f"user:{user.id}", action="user.reset_password",
        target=str(user.id),
    )
    await db.commit()
    return {"reset": True}
