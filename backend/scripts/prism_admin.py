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

from app.auth import generate_prism_key
from app.config import settings
from app.crypto import encrypt
from app.db import SessionLocal
from app.logging_config import configure_logging
from app.models.orm import (
    ApiKey,
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
app.add_typer(user_app, name="user")
app.add_typer(key_app, name="key")
app.add_typer(channel_app, name="channel")
app.add_typer(model_app, name="model")
app.add_typer(payment_app, name="payment")
app.add_typer(usage_app, name="usage")


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
                u = User(email=email, tier=tier, is_admin=admin)
                db.add(u)
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
            await db.commit()
            console.print(f"[yellow]✓[/] User {id_} disabled")

    _run(_go())


@user_app.command("topup")
def user_topup(
    id_: Annotated[int, typer.Option("--id", help="User ID")],
    amount: Annotated[float, typer.Option(help="Amount in USD")],
    channel: Annotated[str, typer.Option(help="Payment channel")] = "manual",
    note: Annotated[str | None, typer.Option(help="Operator note")] = None,
) -> None:
    """Top-up user balance. Auto-applies 0.05% fee."""

    async def _go():
        async with SessionLocal() as db:
            u = await db.get(User, id_)
            if not u:
                console.print(f"[red]✗[/] User {id_} not found")
                raise typer.Exit(1)

            amount_mc = _amount_usd_to_micro_cents(amount)
            fee_mc = amount_mc * settings.topup_fee_basis_points // 10_000
            credited_mc = amount_mc - fee_mc

            u.balance_micro_cents += credited_mc
            u.total_topped_up_micro_cents += credited_mc

            db.add(BalanceTransaction(
                user_id=u.id,
                type="topup",
                amount_micro_cents=credited_mc,
                balance_after_micro_cents=u.balance_micro_cents,
                description=f"Top-up via {channel}; gross ${amount:.2f}, fee {_micro_cents_to_usd_str(fee_mc)}{f'; note: {note}' if note else ''}",
            ))
            await db.commit()

            console.print(
                f"[green]✓[/] Topped up user {id_}: "
                f"gross={amount:.2f} USD, fee={_micro_cents_to_usd_str(fee_mc)} (万 5), "
                f"credited={_micro_cents_to_usd_str(credited_mc)}, "
                f"new balance={_micro_cents_to_usd_str(u.balance_micro_cents)}"
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
            await db.commit()
            await db.refresh(ak)

            console.print(f"[green]✓[/] Created Prism Key (id={ak.id}) for user {user_id}")
            console.print(f"\n[bold yellow]This is the only time the full key is shown:[/]\n")
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
            await db.commit()
            await db.refresh(ch)
            console.print(
                f"[green]✓[/] Added channel {ch.id}: {provider}/{name} "
                f"(models={model_list}, priority={priority}, weight={weight})"
            )

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
            console.print(
                f"[green]✓[/] Payment {id_} paid; "
                f"user {u.id} balance now {_micro_cents_to_usd_str(u.balance_micro_cents)}"
            )

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
# entrypoint
# =============================================================================


def main() -> None:
    configure_logging()
    app()


if __name__ == "__main__":
    main()
