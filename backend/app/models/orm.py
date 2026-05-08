"""SQLAlchemy ORM models for the 7 v0.1 tables.

Money is always stored as **integer micro-cents** to avoid floating-point drift.
1 USD = 100 cents = 100_000_000 micro-cents.

Token unit prices are stored per-million-tokens. e.g. $15.00 / 1M tokens →
1_500_000_000 micro-cents per million.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Common declarative base."""


# =============================================================================
# users
# =============================================================================


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tier: Mapped[str] = mapped_column(
        String(16), nullable=False, default="self-serve"
    )

    balance_micro_cents: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0
    )
    total_topped_up_micro_cents: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0
    )

    # v0.2 additions
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    api_keys: Mapped[list[ApiKey]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("tier IN ('self-serve','team')", name="ck_users_tier"),
    )


# =============================================================================
# api_keys (Prism virtual keys)
# =============================================================================


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(32), nullable=False)
    key_last4: Mapped[str] = mapped_column(String(8), nullable=False)
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model_whitelist: Mapped[str | None] = mapped_column(Text, nullable=True)
    rate_limit_rpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[User] = relationship(back_populates="api_keys")

    @property
    def whitelist_list(self) -> list[str] | None:
        if not self.model_whitelist:
            return None
        return list(json.loads(self.model_whitelist))


# =============================================================================
# models (catalog exposed to clients)
# =============================================================================


class Model(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_id: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    context_window: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # All prices are micro-cents per 1M tokens. e.g. $15/M = 1_500_000_000
    price_input_per_million: Mapped[int] = mapped_column(BigInteger, nullable=False)
    price_output_per_million: Mapped[int] = mapped_column(BigInteger, nullable=False)
    price_cache_read_per_million: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    price_cache_write_per_million: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )

    capabilities: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    __table_args__ = (
        CheckConstraint(
            "provider IN ('anthropic','openai','google')", name="ck_models_provider"
        ),
    )

    @property
    def capabilities_list(self) -> list[str]:
        if not self.capabilities:
            return []
        return list(json.loads(self.capabilities))


# =============================================================================
# channels (upstream API accounts)
# =============================================================================


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    upstream_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)

    models: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    channel_group: Mapped[str] = mapped_column(
        String(32), nullable=False, default="default"
    )

    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    weight: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    cooldown_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # v0.2: surface region + data policy in request detail panel ("渠道明牌")
    region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    policy_no_training: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    policy_log_retention_days: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=30
    )

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    __table_args__ = (
        CheckConstraint(
            "provider IN ('anthropic','openai','google')",
            name="ck_channels_provider",
        ),
        Index("idx_channels_provider_enabled", "provider", "enabled"),
    )

    @property
    def models_list(self) -> list[str]:
        return list(json.loads(self.models))


# =============================================================================
# usage_logs (one row per request, billing source-of-truth)
# =============================================================================


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    api_key_id: Mapped[int] = mapped_column(
        ForeignKey("api_keys.id"), nullable=False
    )
    channel_id: Mapped[int | None] = mapped_column(
        ForeignKey("channels.id"), nullable=True
    )

    model_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_write_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    reasoning_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    cost_micro_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    status: Mapped[str] = mapped_column(String(16), nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ttft_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_streaming: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # v0.2: track router retries for the request-detail panel
    attempt_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tried_channels: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, index=True
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('ok','error','cancelled','partial')",
            name="ck_usage_status",
        ),
        Index("idx_usage_user_time", "user_id", "created_at"),
        Index("idx_usage_channel_time", "channel_id", "created_at"),
    )


# =============================================================================
# balance_transactions (any change to user.balance leaves a trace)
# =============================================================================


class BalanceTransaction(Base):
    __tablename__ = "balance_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    type: Mapped[str] = mapped_column(String(16), nullable=False)

    amount_micro_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    balance_after_micro_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)

    related_usage_log_id: Mapped[int | None] = mapped_column(
        ForeignKey("usage_logs.id"), nullable=True
    )
    related_payment_id: Mapped[int | None] = mapped_column(
        ForeignKey("payment_intents.id"), nullable=True
    )

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, index=True
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('topup','inference','refund','adjust')",
            name="ck_btx_type",
        ),
        Index("idx_btx_user_time", "user_id", "created_at"),
    )


# =============================================================================
# payment_intents (top-up records; v0.1 admin-managed)
# =============================================================================


class PaymentIntent(Base):
    __tablename__ = "payment_intents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    channel: Mapped[str] = mapped_column(String(32), nullable=False)

    amount_micro_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fee_micro_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    credited_micro_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending"
    )

    external_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receiver_address: Mapped[str | None] = mapped_column(String(128), nullable=True)
    network: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # v0.3: chain-watch fields. expected_amount_micro_cents is what the chain
    # monitor matches against (= amount_micro_cents + memo-suffix-disambiguator).
    # tx_hash is unique once paid, providing dedupe protection.
    expected_amount_micro_cents: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    memo: Mapped[str | None] = mapped_column(String(16), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    tx_hash: Mapped[str | None] = mapped_column(
        String(128), nullable=True, unique=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "channel IN ('alipay','wechat','usdt-trc20','usdt-sol','usdt-evm','bank-wire','stripe')",
            name="ck_payment_channel",
        ),
        CheckConstraint(
            "status IN ('pending','paid','failed','refunded','expired')",
            name="ck_payment_status",
        ),
        Index("idx_payment_user_status", "user_id", "status"),
        Index("idx_payment_pending_expected", "status", "expected_amount_micro_cents"),
    )


# =============================================================================
# audit_log
# =============================================================================


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, index=True
    )


# =============================================================================
# v0.3: chain_monitor_state (per-network scan progress)
# =============================================================================


class ChainMonitorState(Base):
    """One row per chain. Drives resumable scanning so a restart doesn't
    re-scan the entire history (or worse, miss txs while we were down)."""

    __tablename__ = "chain_monitor_state"

    network: Mapped[str] = mapped_column(String(32), primary_key=True)
    last_block_height: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_scanned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    consecutive_failures: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)


# =============================================================================
# v0.2: oauth_accounts (GitHub / Google federated identities)
# =============================================================================


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(16), nullable=False)
    provider_uid: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    access_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    __table_args__ = (
        CheckConstraint(
            "provider IN ('github','google')", name="ck_oauth_provider"
        ),
        Index("idx_oauth_user", "user_id"),
        Index("uq_oauth_provider_uid", "provider", "provider_uid", unique=True),
    )


# =============================================================================
# v0.2: email_verifications (email-confirm tokens)
# =============================================================================


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    __table_args__ = (Index("idx_email_verif_user", "user_id"),)


# =============================================================================
# v0.2: sessions (JWT jti registry; supports active logout)
# =============================================================================


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    __table_args__ = (Index("idx_sessions_user_revoked", "user_id", "revoked_at"),)
