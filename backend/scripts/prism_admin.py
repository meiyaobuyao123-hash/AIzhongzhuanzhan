"""Prism admin CLI (v0.1, no Web UI).

Usage::

    prism-admin user create --email dev@example.com
    prism-admin user topup --id 1 --amount 100
    prism-admin key create --user-id 1 --name "My laptop"
    prism-admin channel add --provider anthropic ...
    prism-admin model list
    prism-admin payment create --user 1 --channel usdt-trc20 ...
    prism-admin usage stats --user-id 1 --since 2026-05-01
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.audit import record_audit
from app.auth import generate_prism_key
from app.config import settings
from app.crypto import encrypt
from app.db import SessionLocal
from app.logging_config import configure_logging
from app.models.orm import (
    ApiKey,
    AuditLog,
    BalanceTransaction,
    Channel,
    Model,
    PaymentIntent,
    UsageLog,
    User,
)

console = Console()

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Prism admin CLI")
user_app = typer.Typer(no_args_is_help=True, help="Manage users")
key_app = typer.Typer(no_args_is_help=True, help="Manage Prism API keys")
channel_app = typer.Typer(no_args_is_help=True, help="Manage upstream channels")
model_app = typer.Typer(no_args_is_help=True, help="Manage model catalog")
payment_app = typer.Typer(no_args_is_help=True, help="Manage top-up payments")
usage_app = typer.Typer(no_args_is_help=True, help="Usage stats / reporting")
audit_app = typer.Typer(no_args_is_help=True, help="View admin audit log")
oauth_app = typer.Typer(no_args_is_help=True, help="Configure OAuth providers")
capacity_app = typer.Typer(no_args_is_help=True, help="Capacity monitor (RPM/TPM/5xx)")
email_app = typer.Typer(no_args_is_help=True, help="Email provider diagnostics")
price_app = typer.Typer(no_args_is_help=True, help="Price tracking (v0.5)")
app.add_typer(user_app, name="user")
app.add_typer(key_app, name="key")
app.add_typer(channel_app, name="channel")
app.add_typer(model_app, name="model")
app.add_typer(payment_app, name="payment")
app.add_typer(usage_app, name="usage")
app.add_typer(audit_app, name="audit")
app.add_typer(oauth_app, name="oauth")
app.add_typer(capacity_app, name="capacity")
app.add_typer(email_app, name="email")
app.add_typer(price_app, name="price")


def _run(coro):
    """Adapt async helper to Typer's sync model."""
    return asyncio.run(coro)


def _amount_usd_to_micro_cents(amount: float) -> int:
    """$1.00 → 100_000_000 micro-cents."""
    return int(round(amount * 100_000_000))


def _micro_cents_to_usd_str(mc: int) -> str:
    return f"${mc / 100_000_000:.4f}"


# =============================================================================
# user subcommands
# =============================================================================


@user_app.command("create")
def user_create(
    email: Annotated[str, typer.Option(help="Email address")],
    tier: Annotated[str, typer.Option(help="self-serve | team")] = "self-serve",
    admin: Annotated[bool, typer.Option(help="Mark as admin")] = False,
) -> None:
    """Create a new user (no password — v0.2 will add registration)."""

    async def _go():
        async with SessionLocal() as db:
            try:
                u = User(email=email, tier=tier, is_admin=admin, email_verified=True)
                db.add(u)
                await db.flush()
                await record_audit(
                    db, actor="admin-cli", action="user.create",
                    target=str(u.id),
                    payload={"email": email, "tier": tier, "is_admin": admin},
                )
                await db.commit()
                await db.refresh(u)
                console.print(f"[green]✓[/] Created user [bold]{u.id}[/] ({email}, tier={tier})")
            except IntegrityError:
                console.print(f"[red]✗[/] Email already exists: {email}")
                raise typer.Exit(code=1)

    _run(_go())


@user_app.command("list")
def user_list(
    enabled_only: Annotated[bool, typer.Option("--enabled/--all")] = False,
) -> None:
    async def _go():
        async with SessionLocal() as db:
            stmt = select(User).order_by(User.id)
            if enabled_only:
                stmt = stmt.where(User.enabled.is_(True))
            rows = (await db.execute(stmt)).scalars().all()

            tbl = Table("ID", "Email", "Tier", "Balance", "Total topped", "Admin", "Enabled")
            for u in rows:
                tbl.add_row(
                    str(u.id),
                    u.email,
                    u.tier,
                    _micro_cents_to_usd_str(u.balance_micro_cents),
                    _micro_cents_to_usd_str(u.total_topped_up_micro_cents),
                    "✓" if u.is_admin else "",
                    "✓" if u.enabled else "✗",
                )
            console.print(tbl)

    _run(_go())


@user_app.command("disable")
def user_disable(id_: Annotated[int, typer.Option("--id", help="User ID")]) -> None:
    async def _go():
        async with SessionLocal() as db:
            u = await db.get(User, id_)
            if not u:
                console.print(f"[red]✗[/] User {id_} not found")
                raise typer.Exit(1)
            u.enabled = False
            await record_audit(
                db, actor="admin-cli", action="user.disable", target=str(id_)
            )
            await db.commit()
            console.print(f"[yellow]✓[/] User {id_} disabled")

    _run(_go())


@user_app.command("topup")
def user_topup(
    id_: Annotated[int, typer.Option("--id", help="User ID")],
    amount: Annotated[float, typer.Option(help="Amount (USD or CNY per --currency)")],
    currency: Annotated[str, typer.Option(help="Currency: USD or CNY")] = "USD",
    channel: Annotated[str, typer.Option(help="Payment channel")] = "manual",
    note: Annotated[str | None, typer.Option(help="Operator note")] = None,
) -> None:
    """Top-up user balance. Auto-applies 1.5% fee. Credits the matching wallet.

    --currency USD → 进 USD 钱包 (USDC / 对公电汇 / Stripe 等)
    --currency CNY → 进 CNY 钱包 (支付宝 / 微信)
    """
    cur = currency.upper()
    if cur not in ("USD", "CNY"):
        console.print(f"[red]✗[/] currency must be USD or CNY, got {currency}")
        raise typer.Exit(2)

    async def _go():
        async with SessionLocal() as db:
            u = await db.get(User, id_)
            if not u:
                console.print(f"[red]✗[/] User {id_} not found")
                raise typer.Exit(1)

            amount_mc = int(round(amount * 100_000_000))
            fee_mc = amount_mc * settings.topup_fee_basis_points // 10_000
            credited_mc = amount_mc - fee_mc

            sym = "$" if cur == "USD" else "¥"
            if cur == "USD":
                u.balance_micro_cents += credited_mc
                u.total_topped_up_micro_cents += credited_mc
                balance_after = u.balance_micro_cents
            else:
                u.balance_cny_micro_yuan += credited_mc
                u.total_topped_up_cny_micro_yuan += credited_mc
                balance_after = u.balance_cny_micro_yuan

            db.add(BalanceTransaction(
                user_id=u.id,
                type="topup",
                amount_micro_cents=credited_mc,
                balance_after_micro_cents=balance_after,
                currency=cur,
                description=(
                    f"Top-up via {channel} ({cur}); gross {sym}{amount:.2f}, "
                    f"fee {sym}{fee_mc/100_000_000:.4f}"
                    f"{f'; note: {note}' if note else ''}"
                ),
            ))
            await record_audit(
                db, actor="admin-cli", action="user.topup", target=str(u.id),
                payload={"channel": channel, "currency": cur, "amount": amount,
                          "fee": fee_mc / 100_000_000},
            )
            await db.commit()

            console.print(
                f"[green]✓[/] Topped up user {id_}: "
                f"gross={sym}{amount:.2f}, fee={sym}{fee_mc/100_000_000:.4f} (1.5%), "
                f"credited={sym}{credited_mc/100_000_000:.4f}, "
                f"new {cur} balance={sym}{balance_after/100_000_000:.4f}"
            )

    _run(_go())


@user_app.command("balance")
def user_balance(id_: Annotated[int, typer.Option("--id", help="User ID")]) -> None:
    async def _go():
        async with SessionLocal() as db:
            u = await db.get(User, id_)
            if not u:
                console.print(f"[red]✗[/] User {id_} not found")
                raise typer.Exit(1)
            console.print(
                f"User {u.id} ({u.email}) "
                f"balance={_micro_cents_to_usd_str(u.balance_micro_cents)} "
                f"total_topped={_micro_cents_to_usd_str(u.total_topped_up_micro_cents)}"
            )

    _run(_go())


# =============================================================================
# key subcommands
# =============================================================================


@key_app.command("create")
def key_create(
    user_id: Annotated[int, typer.Option(help="User ID")],
    name: Annotated[str | None, typer.Option(help="Friendly name")] = None,
    rate_limit_rpm: Annotated[int | None, typer.Option("--rpm")] = None,
) -> None:
    """Create a new Prism Key. The full key is printed ONCE."""

    async def _go():
        async with SessionLocal() as db:
            u = await db.get(User, user_id)
            if not u:
                console.print(f"[red]✗[/] User {user_id} not found")
                raise typer.Exit(1)

            full, hashed, prefix, last4 = generate_prism_key()
            ak = ApiKey(
                user_id=user_id,
                key_hash=hashed,
                key_prefix=prefix,
                key_last4=last4,
                name=name,
                rate_limit_rpm=rate_limit_rpm,
            )
            db.add(ak)
            await db.flush()
            await record_audit(
                db, actor="admin-cli", action="key.create", target=str(ak.id),
                payload={"user_id": user_id, "name": name, "rate_limit_rpm": rate_limit_rpm},
            )
            await db.commit()
            await db.refresh(ak)

            console.print(f"[green]✓[/] Created Prism Key (id={ak.id}) for user {user_id}")
            console.print("\n[bold yellow]This is the only time the full key is shown:[/]\n")
            console.print(f"  [bold cyan]{full}[/]\n")
            console.print(f"Prefix: {prefix} … {last4}")

    _run(_go())


@key_app.command("list")
def key_list(
    user_id: Annotated[int | None, typer.Option(help="Filter by user ID")] = None,
) -> None:
    async def _go():
        async with SessionLocal() as db:
            stmt = select(ApiKey).order_by(ApiKey.id.desc())
            if user_id is not None:
                stmt = stmt.where(ApiKey.user_id == user_id)
            rows = (await db.execute(stmt)).scalars().all()

            tbl = Table("ID", "User", "Name", "Prefix…last4", "RPM", "Enabled", "LastUsed")
            for ak in rows:
                tbl.add_row(
                    str(ak.id),
                    str(ak.user_id),
                    ak.name or "-",
                    f"{ak.key_prefix}…{ak.key_last4}",
                    str(ak.rate_limit_rpm or "-"),
                    "✓" if ak.enabled else "✗",
                    ak.last_used_at.isoformat() if ak.last_used_at else "-",
                )
            console.print(tbl)

    _run(_go())


@key_app.command("revoke")
def key_revoke(id_: Annotated[int, typer.Option("--id", help="ApiKey ID")]) -> None:
    async def _go():
        async with SessionLocal() as db:
            ak = await db.get(ApiKey, id_)
            if not ak:
                console.print(f"[red]✗[/] Key {id_} not found")
                raise typer.Exit(1)
            ak.enabled = False
            await record_audit(
                db, actor="admin-cli", action="key.revoke", target=str(id_)
            )
            await db.commit()
            console.print(f"[yellow]✓[/] Key {id_} revoked")

    _run(_go())


# =============================================================================
# channel subcommands
# =============================================================================


@channel_app.command("add")
def channel_add(
    provider: Annotated[str, typer.Option(help="anthropic | openai | google")],
    name: Annotated[str, typer.Option(help="Display name")],
    base_url: Annotated[str, typer.Option("--base-url")],
    upstream_key: Annotated[str, typer.Option("--upstream-key", help="The actual sk-... key")],
    models: Annotated[
        str, typer.Option(help="Comma-separated model_ids supported by this channel")
    ],
    group: Annotated[str, typer.Option("--group")] = "default",
    priority: Annotated[int, typer.Option()] = 100,
    weight: Annotated[int, typer.Option()] = 100,
) -> None:
    """Add an upstream channel. Encrypts upstream_key at rest."""

    async def _go():
        async with SessionLocal() as db:
            encrypted = encrypt(upstream_key, settings.master_key)
            model_list = [m.strip() for m in models.split(",") if m.strip()]
            ch = Channel(
                name=name,
                provider=provider,
                base_url=base_url,
                upstream_key_encrypted=encrypted,
                models=json.dumps(model_list),
                channel_group=group,
                priority=priority,
                weight=weight,
            )
            db.add(ch)
            await db.flush()
            await record_audit(
                db, actor="admin-cli", action="channel.create", target=str(ch.id),
                payload={
                    "provider": provider, "name": name, "base_url": base_url,
                    "models": model_list, "priority": priority, "weight": weight,
                    # Note: upstream_key NOT included in audit payload
                },
            )
            await db.commit()
            await db.refresh(ch)
            console.print(
                f"[green]✓[/] Added channel {ch.id}: {provider}/{name} "
                f"(models={model_list}, priority={priority}, weight={weight})"
            )

    _run(_go())


@channel_app.command("test")
def channel_test(id_: Annotated[int, typer.Option("--id", help="Channel ID")]) -> None:
    """Send a minimal request through the channel to verify upstream Key works."""
    import httpx

    from app.crypto import decrypt

    async def _go():
        async with SessionLocal() as db:
            ch = await db.get(Channel, id_)
            if not ch:
                console.print(f"[red]✗[/] Channel {id_} not found")
                raise typer.Exit(1)
            try:
                upstream_key = decrypt(ch.upstream_key_encrypted, settings.master_key)
            except Exception as exc:
                console.print(f"[red]✗[/] Failed to decrypt upstream_key: {exc}")
                raise typer.Exit(2)

        # Build a minimal probe per provider. Single-token request.
        models = json.loads(ch.models) if ch.models else []
        if not models:
            console.print("[red]✗[/] Channel has no models attached")
            raise typer.Exit(3)
        model_id = models[0]

        async with httpx.AsyncClient(timeout=30, base_url=ch.base_url) as client:
            try:
                if ch.provider == "anthropic":
                    resp = await client.post(
                        "/v1/messages",
                        headers={
                            "x-api-key": upstream_key,
                            "anthropic-version": "2023-06-01",
                        },
                        json={
                            "model": model_id,
                            "max_tokens": 1,
                            "messages": [{"role": "user", "content": "hi"}],
                        },
                    )
                elif ch.provider == "openai":
                    from app.providers.openai import chat_completions_path
                    resp = await client.post(
                        chat_completions_path(ch.base_url),
                        headers={"Authorization": f"Bearer {upstream_key}"},
                        json={
                            "model": model_id,
                            "max_tokens": 1,
                            "messages": [{"role": "user", "content": "hi"}],
                        },
                    )
                elif ch.provider == "google":
                    base = str(client.base_url).rstrip("/")
                    path = "/chat/completions" if base.endswith("/openai") else "/v1beta/openai/chat/completions"
                    resp = await client.post(
                        path,
                        headers={"Authorization": f"Bearer {upstream_key}"},
                        json={
                            "model": model_id,
                            "max_tokens": 1,
                            "messages": [{"role": "user", "content": "hi"}],
                        },
                    )
                else:
                    console.print(f"[red]✗[/] Unknown provider: {ch.provider}")
                    raise typer.Exit(4)
            except httpx.HTTPError as exc:
                console.print(f"[red]✗[/] Network error: {exc}")
                async with SessionLocal() as db:
                    await record_audit(
                        db, actor="admin-cli", action="channel.test",
                        target=str(id_),
                        payload={"result": "network_error", "error": str(exc)},
                    )
                    await db.commit()
                raise typer.Exit(5)

        result_summary = {
            "status": resp.status_code,
            "ok": 200 <= resp.status_code < 300,
        }
        async with SessionLocal() as db:
            await record_audit(
                db, actor="admin-cli", action="channel.test", target=str(id_),
                payload=result_summary,
            )
            await db.commit()

        if resp.status_code < 300:
            console.print(
                f"[green]✓[/] Channel {id_} ({ch.provider}/{ch.name}) is healthy. "
                f"HTTP {resp.status_code}, model {model_id}."
            )
        else:
            try:
                body = resp.json()
            except Exception:
                body = resp.text[:500]
            console.print(
                f"[red]✗[/] Channel {id_} returned HTTP {resp.status_code}\n"
                f"  Body: {body}"
            )
            raise typer.Exit(6)

    _run(_go())


@channel_app.command("list")
def channel_list() -> None:
    async def _go():
        async with SessionLocal() as db:
            rows = (await db.execute(select(Channel).order_by(Channel.id))).scalars().all()
            tbl = Table("ID", "Provider", "Name", "Group", "Models", "Pri", "Wgt", "Cooldown", "On")
            for ch in rows:
                tbl.add_row(
                    str(ch.id),
                    ch.provider,
                    ch.name,
                    ch.channel_group,
                    ",".join(ch.models_list),
                    str(ch.priority),
                    str(ch.weight),
                    ch.cooldown_until.isoformat() if ch.cooldown_until else "-",
                    "✓" if ch.enabled else "✗",
                )
            console.print(tbl)

    _run(_go())


@channel_app.command("disable")
def channel_disable(id_: Annotated[int, typer.Option("--id")]) -> None:
    async def _go():
        async with SessionLocal() as db:
            ch = await db.get(Channel, id_)
            if not ch:
                console.print(f"[red]✗[/] Channel {id_} not found")
                raise typer.Exit(1)
            ch.enabled = False
            await record_audit(
                db, actor="admin-cli", action="channel.disable", target=str(id_)
            )
            await db.commit()
            console.print(f"[yellow]✓[/] Channel {id_} disabled")

    _run(_go())


# =============================================================================
# model subcommands
# =============================================================================


@model_app.command("list")
def model_list_cmd() -> None:
    async def _go():
        async with SessionLocal() as db:
            rows = (await db.execute(select(Model).order_by(Model.id))).scalars().all()
            tbl = Table("ID", "model_id", "Provider", "Ctx", "$ in/M", "$ out/M", "Enabled")
            for m in rows:
                tbl.add_row(
                    str(m.id),
                    m.model_id,
                    m.provider,
                    str(m.context_window or "-"),
                    f"${m.price_input_per_million / 100_000_000:.2f}",
                    f"${m.price_output_per_million / 100_000_000:.2f}",
                    "✓" if m.enabled else "✗",
                )
            console.print(tbl)

    _run(_go())


@model_app.command("add")
def model_add(
    id_: Annotated[str, typer.Option("--id", help="model_id, e.g. claude-opus-4-5")],
    provider: Annotated[str, typer.Option()],
    display_name: Annotated[str, typer.Option("--display-name")],
    price_input: Annotated[int, typer.Option("--price-input", help="micro-cents per 1M")],
    price_output: Annotated[int, typer.Option("--price-output")],
    price_cache_read: Annotated[int | None, typer.Option("--price-cache-read")] = None,
    price_cache_write: Annotated[int | None, typer.Option("--price-cache-write")] = None,
    context_window: Annotated[int | None, typer.Option("--ctx")] = None,
    capabilities: Annotated[
        str, typer.Option(help='Comma list: streaming,tool-use,vision,cache,reasoning')
    ] = "streaming",
) -> None:
    async def _go():
        async with SessionLocal() as db:
            caps = [c.strip() for c in capabilities.split(",") if c.strip()]
            m = Model(
                model_id=id_,
                display_name=display_name,
                provider=provider,
                context_window=context_window,
                price_input_per_million=price_input,
                price_output_per_million=price_output,
                price_cache_read_per_million=price_cache_read,
                price_cache_write_per_million=price_cache_write,
                capabilities=json.dumps(caps),
            )
            db.add(m)
            await db.commit()
            await db.refresh(m)
            console.print(f"[green]✓[/] Model {id_} added (id={m.id})")

    _run(_go())


# =============================================================================
# payment subcommands (v0.1: admin-managed)
# =============================================================================


@payment_app.command("create")
def payment_create(
    user: Annotated[int, typer.Option()],
    channel: Annotated[str, typer.Option(help="alipay/wechat/usdt-trc20/usdt-sol/usdt-evm/bank-wire/stripe")],
    amount_usd: Annotated[float, typer.Option("--amount-usd")],
    tx_hash: Annotated[str | None, typer.Option("--tx-hash")] = None,
    network: Annotated[str | None, typer.Option()] = None,
    receiver: Annotated[str | None, typer.Option()] = None,
    note: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Record a top-up intent (status=pending). Use 'mark-paid' to credit balance."""

    async def _go():
        async with SessionLocal() as db:
            amount_mc = _amount_usd_to_micro_cents(amount_usd)
            fee_mc = amount_mc * settings.topup_fee_basis_points // 10_000
            credited_mc = amount_mc - fee_mc
            p = PaymentIntent(
                user_id=user,
                channel=channel,
                amount_micro_cents=amount_mc,
                fee_micro_cents=fee_mc,
                credited_micro_cents=credited_mc,
                external_ref=tx_hash,
                network=network,
                receiver_address=receiver,
                notes=note,
            )
            db.add(p)
            await db.commit()
            await db.refresh(p)
            console.print(
                f"[green]✓[/] PaymentIntent {p.id} created: "
                f"user={user}, channel={channel}, amount=${amount_usd:.2f}, "
                f"fee={_micro_cents_to_usd_str(fee_mc)}, status=pending"
            )

    _run(_go())


@payment_app.command("mark-paid")
def payment_mark_paid(id_: Annotated[int, typer.Option("--id")]) -> None:
    """Mark a pending PaymentIntent as paid and credit user balance."""

    async def _go():
        async with SessionLocal() as db:
            p = await db.get(PaymentIntent, id_)
            if not p:
                console.print(f"[red]✗[/] Payment {id_} not found")
                raise typer.Exit(1)
            if p.status != "pending":
                console.print(f"[red]✗[/] Payment {id_} status is {p.status}, not pending")
                raise typer.Exit(1)
            u = await db.get(User, p.user_id)
            if not u:
                console.print(f"[red]✗[/] User {p.user_id} not found")
                raise typer.Exit(1)

            u.balance_micro_cents += p.credited_micro_cents
            u.total_topped_up_micro_cents += p.credited_micro_cents
            p.status = "paid"
            p.paid_at = datetime.now()

            db.add(BalanceTransaction(
                user_id=u.id,
                type="topup",
                amount_micro_cents=p.credited_micro_cents,
                balance_after_micro_cents=u.balance_micro_cents,
                related_payment_id=p.id,
                description=f"Payment #{p.id} marked paid via {p.channel}",
            ))
            await db.commit()
            await record_audit(
                db, actor="admin-cli", action="payment.mark_paid", target=str(id_),
                payload={"user_id": u.id, "credited_usd": p.credited_micro_cents / 100_000_000},
            )
            await db.commit()
            console.print(
                f"[green]✓[/] Payment {id_} paid; "
                f"user {u.id} balance now {_micro_cents_to_usd_str(u.balance_micro_cents)}"
            )

    _run(_go())


# =============================================================================
# oauth subcommands
# =============================================================================


def _update_env_file(env_path: str, updates: dict[str, str]) -> None:
    """Idempotent .env updater. Replaces existing keys, appends missing ones."""
    import os
    if not os.path.exists(env_path):
        # Touch
        with open(env_path, "w") as f:
            pass

    with open(env_path) as f:
        lines = f.readlines()

    seen = set()
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue
        key = stripped.split("=", 1)[0]
        if key in updates:
            new_lines.append(f"{key}={updates[key]}\n")
            seen.add(key)
        else:
            new_lines.append(line)

    for k, v in updates.items():
        if k not in seen:
            new_lines.append(f"{k}={v}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)


@oauth_app.command("set")
def oauth_set(
    provider: Annotated[str, typer.Option(help="github | google")],
    client_id: Annotated[str, typer.Option("--client-id")],
    client_secret: Annotated[str, typer.Option("--client-secret")],
    env_file: Annotated[str, typer.Option(help="Path to .env")] = "/opt/prism/.env",
    restart: Annotated[bool, typer.Option(help="Restart prism systemd unit after update")] = True,
) -> None:
    """Configure OAuth provider credentials in .env and restart the service.

    Example::

        prism-admin oauth set --provider github \\
          --client-id Iv1.xxxx --client-secret ghs_xxxx
    """
    if provider not in ("github", "google"):
        console.print(f"[red]✗[/] provider must be github or google, got {provider!r}")
        raise typer.Exit(1)

    p = provider.upper()
    updates = {
        f"PRISM_OAUTH_{p}_CLIENT_ID": client_id,
        f"PRISM_OAUTH_{p}_CLIENT_SECRET": client_secret,
    }
    _update_env_file(env_file, updates)
    console.print(f"[green]✓[/] Updated {env_file}: {provider} OAuth credentials")

    if restart:
        import os
        rc = os.system("sudo systemctl restart prism")
        if rc == 0:
            console.print("[green]✓[/] Restarted prism service")
        else:
            console.print(
                "[yellow]![/] Could not auto-restart. Run manually:\n"
                "  sudo systemctl restart prism"
            )

    console.print(
        f"\nVerify at https://www.ai100trading.cn/login — "
        f"the [bold]{provider.capitalize()}[/] button should appear."
    )


@oauth_app.command("status")
def oauth_status(
    env_file: Annotated[str, typer.Option(help="Path to .env")] = "/opt/prism/.env",
) -> None:
    """Show which OAuth providers are configured."""
    import os
    if not os.path.exists(env_file):
        console.print(f"[red]✗[/] {env_file} not found")
        raise typer.Exit(1)
    with open(env_file) as f:
        env = f.read()

    tbl = Table("Provider", "Configured", "Client ID prefix")
    for prov in ("github", "google"):
        p = prov.upper()
        cid_line = next(
            (ln for ln in env.splitlines() if ln.strip().startswith(f"PRISM_OAUTH_{p}_CLIENT_ID=")),
            "",
        )
        cid = cid_line.split("=", 1)[1].strip() if "=" in cid_line else ""
        cs_line = next(
            (ln for ln in env.splitlines() if ln.strip().startswith(f"PRISM_OAUTH_{p}_CLIENT_SECRET=")),
            "",
        )
        cs = cs_line.split("=", 1)[1].strip() if "=" in cs_line else ""
        configured = bool(cid) and bool(cs)
        tbl.add_row(
            prov,
            "✓" if configured else "✗",
            (cid[:12] + "…") if cid else "(not set)",
        )
    console.print(tbl)


# =============================================================================
# audit subcommands
# =============================================================================


@audit_app.command("list")
def audit_list(
    since: Annotated[
        str | None, typer.Option(help="ISO date e.g. 2026-05-01")
    ] = None,
    limit: Annotated[int, typer.Option()] = 50,
    actor: Annotated[str | None, typer.Option(help="Filter by actor")] = None,
    action: Annotated[str | None, typer.Option(help="Filter by action prefix, e.g. 'channel.'")] = None,
) -> None:
    async def _go():
        async with SessionLocal() as db:
            stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
            if since:
                since_dt = datetime.fromisoformat(since)
                stmt = stmt.where(AuditLog.created_at >= since_dt)
            if actor:
                stmt = stmt.where(AuditLog.actor == actor)
            if action:
                stmt = stmt.where(AuditLog.action.like(f"{action}%"))
            rows = (await db.execute(stmt)).scalars().all()

            tbl = Table("Time", "Actor", "Action", "Target", "Payload")
            for log in rows:
                payload_text = log.payload[:80] + "…" if log.payload and len(log.payload) > 80 else (log.payload or "")
                tbl.add_row(
                    log.created_at.isoformat()[:19],
                    log.actor,
                    log.action,
                    log.target or "-",
                    payload_text,
                )
            console.print(tbl)

    _run(_go())


# =============================================================================
# usage subcommands
# =============================================================================


@usage_app.command("stats")
def usage_stats(
    user_id: Annotated[int | None, typer.Option("--user-id")] = None,
    channel_id: Annotated[int | None, typer.Option("--channel-id")] = None,
    since: Annotated[
        str | None, typer.Option(help="ISO date, e.g. 2026-05-01")
    ] = None,
) -> None:
    async def _go():
        async with SessionLocal() as db:
            stmt = select(
                UsageLog.model_id,
                func.count().label("requests"),
                func.sum(UsageLog.prompt_tokens).label("in_tok"),
                func.sum(UsageLog.completion_tokens).label("out_tok"),
                func.sum(UsageLog.cost_micro_cents).label("cost"),
            ).group_by(UsageLog.model_id)

            if user_id is not None:
                stmt = stmt.where(UsageLog.user_id == user_id)
            if channel_id is not None:
                stmt = stmt.where(UsageLog.channel_id == channel_id)
            if since:
                since_dt = datetime.fromisoformat(since)
                stmt = stmt.where(UsageLog.created_at >= since_dt)

            rows = (await db.execute(stmt)).all()

            tbl = Table("Model", "Requests", "Input tok", "Output tok", "Cost (USD)")
            total_cost = 0
            for model_id, requests, in_tok, out_tok, cost in rows:
                cost = cost or 0
                total_cost += cost
                tbl.add_row(
                    model_id,
                    str(requests),
                    f"{in_tok or 0:,}",
                    f"{out_tok or 0:,}",
                    _micro_cents_to_usd_str(cost),
                )
            console.print(tbl)
            console.print(f"\n[bold]Total cost:[/] {_micro_cents_to_usd_str(total_cost)}")

    _run(_go())


# =============================================================================
# capacity subcommands
# =============================================================================


@capacity_app.command("report")
def capacity_report(
    window: Annotated[int, typer.Option("--window", help="Window minutes")] = 5,
) -> None:
    """Print the current per-channel rolling window stats."""
    from app.monitoring.capacity import collect_alerts, evaluate_window

    async def _go():
        async with SessionLocal() as db:
            stats = await evaluate_window(db, window_min=window)
            if not stats:
                console.print(f"[yellow]No usage in the last {window} min.[/]")
                return
            tbl = Table(
                "Channel", "Requests", "RPM", "TPM",
                "Errors", "Err %", "RPM quota",
            )
            for s in stats:
                tbl.add_row(
                    f"{s.channel_name} (#{s.channel_id})" if s.channel_id else s.channel_name,
                    str(s.requests),
                    f"{s.rpm:.1f}",
                    f"{s.tpm:.0f}",
                    str(s.errors),
                    f"{s.error_rate_pct:.2f}",
                    str(s.rpm_quota),
                )
            console.print(tbl)
            alerts = collect_alerts(stats)
            if alerts:
                console.print(f"\n[bold red]Alerts (would fire if not debounced):[/] {len(alerts)}")
                for a in alerts:
                    console.print(
                        f"  • {a.signal} on {a.channel_name}: "
                        f"value={a.value}, threshold={a.threshold}"
                    )
            else:
                console.print("\n[green]All channels within thresholds.[/]")

    _run(_go())


# =============================================================================
# email subcommands
# =============================================================================


@email_app.command("status")
def email_status() -> None:
    """Show which email provider would be used by send_email."""
    from app.email import email_provider_status
    s = email_provider_status()
    if s["configured"]:
        console.print(f"[green]✓[/] Provider: [bold]{s['provider']}[/]")
        for k, v in s.items():
            if k in ("provider", "configured"):
                continue
            console.print(f"  {k}: {v}")
    else:
        console.print(f"[yellow]✗[/] Provider: [bold]{s['provider']}[/] (emails are NOT being sent)")
        console.print(f"  hint: {s.get('hint', '')}")


@email_app.command("test")
def email_test(
    to: Annotated[str, typer.Option(help="Recipient email")],
    subject: Annotated[str, typer.Option(help="Subject")] = "Prism — SMTP test",
) -> None:
    """Send a test email to verify the configured provider works."""
    from app.email import email_provider_status, send_email

    async def _go():
        status = email_provider_status()
        console.print(f"Provider: [bold]{status['provider']}[/]")
        body = (
            f"This is a test email from Prism.\n\n"
            f"Provider: {status['provider']}\n"
            f"If you see this, email delivery is working.\n\n"
            f"— Prism · cost = price · always"
        )
        ok = await send_email(to, subject, body)
        if ok:
            console.print(f"[green]✓[/] Sent to {to}")
        else:
            console.print(
                f"[red]✗[/] Send failed (or no provider configured). "
                f"Check journalctl -u prism for details."
            )

    _run(_go())


# =============================================================================
# entrypoint
# =============================================================================


# =============================================================================
# price subcommands (v0.5)
# =============================================================================


@price_app.command("list")
def price_list() -> None:
    """Show current DB price + last-confirmed time + source URL for all enabled models."""
    from app.models.orm import Model

    async def _go():
        async with SessionLocal() as db:
            rows = (await db.execute(
                select(Model).where(Model.enabled.is_(True)).order_by(Model.id)
            )).scalars().all()
            tbl = Table(
                "id", "model_id", "in/M", "out/M", "cur",
                "set_at", "set_by", "source",
            )
            for r in rows:
                sym = "$" if (r.price_currency or "USD") == "USD" else "¥"
                set_at = (
                    r.price_set_at.strftime("%Y-%m-%d %H:%M") if r.price_set_at
                    else "(none)"
                )
                tbl.add_row(
                    str(r.id), r.model_id,
                    f"{sym}{r.price_input_per_million / 100_000_000:.4f}",
                    f"{sym}{r.price_output_per_million / 100_000_000:.4f}",
                    r.price_currency or "USD",
                    set_at,
                    r.price_set_by or "-",
                    (r.price_source_url or "-")[:40],
                )
            console.print(tbl)

    _run(_go())


@price_app.command("check")
def price_check(
    threshold: Annotated[float, typer.Option(help="Diff %% to flag as anomaly")] = 1.0,
) -> None:
    """Run one full check cycle now: pull all sources, diff, write anomalies."""
    from app.pricing.checker import run_check_cycle

    async def _go():
        async with SessionLocal() as db:
            result = await run_check_cycle(db, threshold_pct=threshold)
            console.print("[bold]Check cycle done[/]")
            console.print(f"  Sources run:           {result.sources_run}")
            console.print(f"  Sources failed:        {len(result.sources_failed)}")
            for src, err in result.sources_failed:
                console.print(f"    [yellow]✗[/] {src}: {err[:100]}")
            console.print(f"  Snapshots collected:   {result.snapshots_collected}")
            console.print(f"  Snapshots unchanged:   {result.snapshots_unchanged}")
            console.print(f"  [bold red]Anomalies created: {result.anomalies_created}[/]")
            console.print(f"  Unknown observed:      {result.unknown_models}")

    _run(_go())


@price_app.command("anomalies")
def price_anomalies(
    status: Annotated[str, typer.Option(help="Filter status")] = "pending",
) -> None:
    """List anomalies awaiting review."""
    from app.models.orm import PriceAnomaly

    async def _go():
        async with SessionLocal() as db:
            stmt = select(PriceAnomaly).order_by(PriceAnomaly.detected_at.desc())
            if status != "all":
                stmt = stmt.where(PriceAnomaly.status == status)
            rows = (await db.execute(stmt)).scalars().all()

            if not rows:
                console.print(f"[green]No {status} anomalies.[/]")
                return

            tbl = Table("id", "model_id", "source", "DB in→obs in", "DB out→obs out",
                        "diff%", "detected", "status")
            for r in rows:
                sym_d = "$" if r.current_db_input < 1_000_000_000 else "¥"
                tbl.add_row(
                    str(r.id), r.model_id, r.source,
                    f"{sym_d}{r.current_db_input/100_000_000:.3f}→{sym_d}{r.observed_input/100_000_000:.3f}",
                    f"{sym_d}{r.current_db_output/100_000_000:.3f}→{sym_d}{r.observed_output/100_000_000:.3f}",
                    f"{max(r.diff_pct_input, r.diff_pct_output):.1f}%",
                    r.detected_at.strftime("%m-%d %H:%M"),
                    r.status,
                )
            console.print(tbl)

    _run(_go())


@price_app.command("confirm")
def price_confirm(
    anomaly_id: Annotated[int, typer.Option("--id", help="anomaly id from `price anomalies`")],
    by: Annotated[str, typer.Option(help="Who is confirming (your email)")] = "admin-cli",
) -> None:
    """Apply observed value of this anomaly to the live model price + write history."""
    from app.pricing.checker import confirm_anomaly

    async def _go():
        async with SessionLocal() as db:
            try:
                history = await confirm_anomaly(db, anomaly_id=anomaly_id, confirmed_by=by)
            except ValueError as exc:
                console.print(f"[red]✗[/] {exc}")
                raise typer.Exit(1)
            console.print(
                f"[green]✓[/] Confirmed anomaly {anomaly_id}. "
                f"New history row id={history.id} for {history.model_id} "
                f"(in={history.price_input_per_million/1e8:.4f} "
                f"out={history.price_output_per_million/1e8:.4f})"
            )

    _run(_go())


@price_app.command("reject")
def price_reject(
    anomaly_id: Annotated[int, typer.Option("--id")],
    by: Annotated[str, typer.Option(help="Who is rejecting")] = "admin-cli",
    reason: Annotated[str | None, typer.Option(help="Why rejected")] = None,
) -> None:
    """Reject an anomaly: keep DB price, mark resolved."""
    from app.pricing.checker import reject_anomaly

    async def _go():
        async with SessionLocal() as db:
            try:
                await reject_anomaly(db, anomaly_id=anomaly_id, rejected_by=by, reason=reason)
            except ValueError as exc:
                console.print(f"[red]✗[/] {exc}")
                raise typer.Exit(1)
            console.print(f"[green]✓[/] Rejected anomaly {anomaly_id}")

    _run(_go())


@price_app.command("history")
def price_history(
    model_id: Annotated[str, typer.Option("--model-id")],
    limit: Annotated[int, typer.Option(help="Max rows")] = 20,
) -> None:
    """Show recent price changes for a model."""
    from app.models.orm import ModelPriceHistory

    async def _go():
        async with SessionLocal() as db:
            rows = (await db.execute(
                select(ModelPriceHistory)
                .where(ModelPriceHistory.model_id == model_id)
                .order_by(ModelPriceHistory.effective_at.desc())
                .limit(limit)
            )).scalars().all()
            if not rows:
                console.print(f"[yellow]No history for {model_id}[/]")
                return
            tbl = Table("id", "effective_at", "in/M", "out/M", "cur", "source", "by")
            for r in rows:
                sym = "$" if r.currency == "USD" else "¥"
                tbl.add_row(
                    str(r.id),
                    r.effective_at.strftime("%Y-%m-%d %H:%M"),
                    f"{sym}{r.price_input_per_million/1e8:.4f}",
                    f"{sym}{r.price_output_per_million/1e8:.4f}",
                    r.currency,
                    r.source,
                    r.confirmed_by or "-",
                )
            console.print(tbl)

    _run(_go())


def main() -> None:
    configure_logging()
    app()


if __name__ == "__main__":
    main()
