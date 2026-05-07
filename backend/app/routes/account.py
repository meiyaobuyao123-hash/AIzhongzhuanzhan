"""Account self-service endpoints (require JWT)."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import record_audit
from app.auth import generate_prism_key
from app.deps import client_ip, current_user, get_db
from app.errors import PrismException, error_response
from app.limits import default_rpm_for_user
from app.models.orm import (
    ApiKey,
    BalanceTransaction,
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
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            }
            for p in rows
        ],
    }
