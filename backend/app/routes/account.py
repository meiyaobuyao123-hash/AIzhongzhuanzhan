"""Account self-service endpoints (require JWT)."""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import record_audit
from app.auth import generate_prism_key
from app.config import settings
from app.deps import client_ip, current_user, get_db
from app.errors import PrismException, error_response
from app.limits import default_rpm_for_user
from app.models.orm import (
    ApiKey,
    PaymentIntent,
    User,
)

router = APIRouter(tags=["account"], prefix="/account")


# ─── Schemas ────────────────────────────────────────────────────────────────


class UpdateMeRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=128)
    avatar_url: str | None = Field(default=None, max_length=512)


class CreateApiKeyRequest(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    model_whitelist: list[str] | None = None
    rate_limit_rpm: int | None = Field(default=None, ge=1, le=100_000)


class UpdateApiKeyRequest(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    model_whitelist: list[str] | None = None
    rate_limit_rpm: int | None = Field(default=None, ge=1, le=100_000)
    enabled: bool | None = None


# ─── /account/me ────────────────────────────────────────────────────────────


@router.get("/me")
async def get_me(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await current_user(authorization, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)
    return _user_view(user)


@router.patch("/me")
async def update_me(
    body: UpdateMeRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await current_user(authorization, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    changed: dict = {}
    if body.display_name is not None:
        user.display_name = body.display_name
        changed["display_name"] = body.display_name
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url
        changed["avatar_url"] = body.avatar_url

    if changed:
        await record_audit(
            db, actor=f"user:{user.id}", action="user.update_profile",
            target=str(user.id), payload=changed, ip=client_ip(request),
        )
        await db.commit()
    return _user_view(user)


def _user_view(u: User) -> dict:
    return {
        "id": u.id,
        "email": u.email,
        "tier": u.tier,
        "display_name": u.display_name,
        "avatar_url": u.avatar_url,
        "balance_micro_cents": u.balance_micro_cents,
        "balance_usd": round(u.balance_micro_cents / 100_000_000, 4),
        "total_topped_up_usd": round(u.total_topped_up_micro_cents / 100_000_000, 2),
        "default_rpm": default_rpm_for_user(u.total_topped_up_micro_cents, u.tier),
        "email_verified": u.email_verified,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


# ─── /account/api-keys ──────────────────────────────────────────────────────


@router.get("/api-keys")
async def list_api_keys(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await current_user(authorization, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    rows = (await db.execute(
        select(ApiKey).where(ApiKey.user_id == user.id).order_by(ApiKey.id.desc())
    )).scalars().all()
    return {
        "data": [_key_view(k) for k in rows],
    }


@router.post("/api-keys", status_code=201)
async def create_api_key(
    body: CreateApiKeyRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await current_user(authorization, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    full, hashed, prefix, last4 = generate_prism_key()
    ak = ApiKey(
        user_id=user.id,
        key_hash=hashed,
        key_prefix=prefix,
        key_last4=last4,
        name=body.name,
        rate_limit_rpm=body.rate_limit_rpm,
        model_whitelist=json.dumps(body.model_whitelist) if body.model_whitelist else None,
    )
    db.add(ak)
    await db.flush()
    await record_audit(
        db, actor=f"user:{user.id}", action="key.create_self",
        target=str(ak.id), ip=client_ip(request),
        payload={"name": body.name},
    )
    await db.commit()
    await db.refresh(ak)

    out = _key_view(ak)
    # Return the FULL key exactly once
    out["key"] = full
    return out


@router.get("/api-keys/{id}")
async def get_api_key(
    id: int,
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await current_user(authorization, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)
    ak = await db.get(ApiKey, id)
    if not ak or ak.user_id != user.id:
        return error_response(404, "API key not found", "invalid_request_error")
    return _key_view(ak)


@router.patch("/api-keys/{id}")
async def update_api_key(
    id: int,
    body: UpdateApiKeyRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await current_user(authorization, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)
    ak = await db.get(ApiKey, id)
    if not ak or ak.user_id != user.id:
        return error_response(404, "API key not found", "invalid_request_error")

    changed: dict = {}
    if body.name is not None:
        ak.name = body.name
        changed["name"] = body.name
    if body.model_whitelist is not None:
        ak.model_whitelist = json.dumps(body.model_whitelist)
        changed["model_whitelist"] = body.model_whitelist
    if body.rate_limit_rpm is not None:
        ak.rate_limit_rpm = body.rate_limit_rpm
        changed["rate_limit_rpm"] = body.rate_limit_rpm
    if body.enabled is not None:
        ak.enabled = body.enabled
        changed["enabled"] = body.enabled

    if changed:
        await record_audit(
            db, actor=f"user:{user.id}", action="key.update_self",
            target=str(ak.id), ip=client_ip(request), payload=changed,
        )
        await db.commit()
    return _key_view(ak)


@router.delete("/api-keys/{id}")
async def delete_api_key(
    id: int,
    request: Request,
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await current_user(authorization, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)
    ak = await db.get(ApiKey, id)
    if not ak or ak.user_id != user.id:
        return error_response(404, "API key not found", "invalid_request_error")

    ak.enabled = False
    await record_audit(
        db, actor=f"user:{user.id}", action="key.revoke_self",
        target=str(ak.id), ip=client_ip(request),
    )
    await db.commit()
    return {"revoked": True, "id": ak.id}


def _key_view(k: ApiKey) -> dict:
    return {
        "id": k.id,
        "name": k.name,
        "prefix": k.key_prefix,
        "last4": k.key_last4,
        "rate_limit_rpm": k.rate_limit_rpm,
        "model_whitelist": json.loads(k.model_whitelist) if k.model_whitelist else None,
        "enabled": k.enabled,
        "created_at": k.created_at.isoformat() if k.created_at else None,
        "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
    }


# ─── /account/balance + topups ─────────────────────────────────────────────


@router.get("/balance")
async def balance(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await current_user(authorization, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    return {
        "balance_micro_cents": user.balance_micro_cents,
        "balance_usd": round(user.balance_micro_cents / 100_000_000, 4),
        "total_topped_up_micro_cents": user.total_topped_up_micro_cents,
        "total_topped_up_usd": round(user.total_topped_up_micro_cents / 100_000_000, 2),
    }


@router.get("/topups")
async def topups(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    try:
        user = await current_user(authorization, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    rows = (await db.execute(
        select(PaymentIntent)
        .where(PaymentIntent.user_id == user.id)
        .order_by(PaymentIntent.id.desc())
        .limit(limit)
    )).scalars().all()
    return {
        "data": [
            {
                "id": p.id,
                "channel": p.channel,
                "amount_usd": round(p.amount_micro_cents / 100_000_000, 4),
                "fee_usd": round(p.fee_micro_cents / 100_000_000, 4),
                "credited_usd": round(p.credited_micro_cents / 100_000_000, 4),
                "status": p.status,
                "external_ref": p.external_ref,
                "network": p.network,
                "memo": p.memo,
                "expected_amount_usd": (
                    round(p.expected_amount_micro_cents / 100_000_000, 6)
                    if p.expected_amount_micro_cents else None
                ),
                "expires_at": p.expires_at.isoformat() if p.expires_at else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            }
            for p in rows
        ],
    }


# ─── /account/topup-intent ──────────────────────────────────────────────────


_USDT_CHANNELS = {"usdt-trc20", "usdt-sol", "usdt-evm"}


def _address_for_channel(channel: str) -> tuple[str, str]:
    """Return (receive_address, network_hint) for a USDT channel."""
    if channel == "usdt-trc20":
        return settings.chain_tron_address, "tron"
    if channel == "usdt-sol":
        return settings.chain_solana_address, "solana"
    if channel == "usdt-evm":
        return settings.chain_evm_address, settings.evm_default_chain
    raise ValueError(f"Unsupported channel: {channel}")


def _calc_fee_micro_cents(gross: int) -> int:
    """fee = gross * topup_fee_basis_points / 10000 (integer math)."""
    return gross * settings.topup_fee_basis_points // 10_000


def _generate_memo() -> str:
    """A 4-digit string used as the µ¢-suffix disambiguator. 0001..9999."""
    # secrets.randbelow gives 0..9998, +1 for 1..9999, zero-pad
    return f"{secrets.randbelow(9999) + 1:04d}"


class TopupIntentRequest(BaseModel):
    channel: str = Field(..., pattern="^usdt-(trc20|sol|evm)$")
    amount_usd: float = Field(..., gt=0, le=100_000)


@router.post("/topup-intent")
async def create_topup_intent(
    body: TopupIntentRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Create a pending USDT top-up intent.

    Returns the payment address + the EXACT amount the user must send
    (with a 4-digit µ¢-suffix that disambiguates them from other concurrent
    pending intents). The chain monitor matches on this exact amount.
    """
    try:
        user = await current_user(authorization, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    if body.channel not in _USDT_CHANNELS:
        return error_response(400, "Unsupported channel", "invalid_request_error")

    base_amount_micro_cents = int(round(body.amount_usd * 100_000_000))

    # Try up to 5 times to find a memo whose expected_amount doesn't collide
    # with another pending intent on the same channel.
    for _ in range(5):
        memo = _generate_memo()
        suffix = int(memo)  # 1..9999 µ¢ added on top of base
        expected = base_amount_micro_cents + suffix
        existing = (await db.execute(
            select(PaymentIntent)
            .where(PaymentIntent.channel == body.channel)
            .where(PaymentIntent.status == "pending")
            .where(PaymentIntent.expected_amount_micro_cents == expected)
        )).scalar_one_or_none()
        if existing is None:
            break
    else:
        return error_response(
            503, "Cannot allocate unique payment amount, retry later", "api_error"
        )

    fee = _calc_fee_micro_cents(base_amount_micro_cents)
    credited = base_amount_micro_cents - fee

    address, network_hint = _address_for_channel(body.channel)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.chain_topup_intent_ttl_min
    )

    intent = PaymentIntent(
        user_id=user.id,
        channel=body.channel,
        amount_micro_cents=base_amount_micro_cents,
        fee_micro_cents=fee,
        credited_micro_cents=credited,
        status="pending",
        receiver_address=address,
        network=network_hint,
        expected_amount_micro_cents=expected,
        memo=memo,
        expires_at=expires_at,
    )
    db.add(intent)
    await db.flush()

    await record_audit(
        db, actor=f"user:{user.id}", action="topup.intent_create",
        target=str(intent.id), ip=client_ip(request),
        payload={
            "channel": body.channel,
            "amount_usd": body.amount_usd,
            "memo": memo,
        },
    )
    await db.commit()
    await db.refresh(intent)

    return {
        "id": intent.id,
        "channel": intent.channel,
        "network": intent.network,
        "address": intent.receiver_address,
        "amount_usd": round(intent.amount_micro_cents / 100_000_000, 4),
        "fee_usd": round(intent.fee_micro_cents / 100_000_000, 4),
        "credited_usd": round(intent.credited_micro_cents / 100_000_000, 4),
        "expected_amount_usd": round(intent.expected_amount_micro_cents / 100_000_000, 6),
        "expected_amount_micro_cents": intent.expected_amount_micro_cents,
        "memo": intent.memo,
        "expires_at": intent.expires_at.isoformat() if intent.expires_at else None,
        "instructions": (
            f"Send EXACTLY ${intent.expected_amount_micro_cents / 100_000_000:.6f} "
            f"USDT on {intent.network} to the address above. The amount's last "
            f"4 µ¢ ({intent.memo}) identify your top-up — paying the wrong "
            f"amount will not credit your balance automatically."
        ),
    }
