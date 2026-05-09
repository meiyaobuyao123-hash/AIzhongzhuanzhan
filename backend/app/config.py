"""Environment-driven configuration."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime config in one place. Pulled from env / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PRISM_",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    host: str = "127.0.0.1"
    port: int = 8765
    log_level: str = "INFO"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./prism.db"

    # Crypto
    # AES-256-GCM master key. 32 bytes hex (= 64 chars). Generate:
    #   openssl rand -hex 32
    master_key_hex: str = Field(
        default="0" * 64,
        description="Hex-encoded 32-byte key for AES-GCM. MUST be set in production.",
    )

    # Routing / timeouts
    request_timeout_s: int = 600
    upstream_connect_timeout_s: int = 10

    # Billing
    topup_fee_basis_points: int = 150
    """150 bps = 1.5% — covers Stripe / 商户号 / 链上 gas 等通道成本"""

    # v0.4 dual-wallet cross-currency FX rates.
    # Mid-market is ~7.20 CNY/USD; we apply asymmetric rates (both worse
    # for the user than mid-market) to leave us a spread covering FX risk.
    # Same-currency wallet → same-currency model = 1:1, no FX applied.
    fx_usd_to_cny_for_cn_model: float = 6.5
    """USD wallet 用于国内模型: 1 USD 抵 6.5 CNY (用户多付 ~10% vs 7.20 mid)"""
    fx_cny_to_usd_for_intl_model: float = 7.0
    """CNY wallet 用于国外模型: 7 CNY 抵 1 USD (用户多付 ~3% vs 7.20 mid)"""

    # Redis
    redis_url: str = "redis://127.0.0.1:6379/0"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_ttl_days: int = 30

    # Rate limit tiers (RPM)
    rpm_tier_lt_50: int = 60
    rpm_tier_lt_500: int = 240
    rpm_tier_lt_5000: int = 600
    rpm_tier_ge_5000: int = 1200

    # OAuth (empty = provider disabled)
    oauth_github_client_id: str = ""
    oauth_github_client_secret: str = ""
    oauth_google_client_id: str = ""
    oauth_google_client_secret: str = ""
    oauth_redirect_base: str = "https://www.ai100trading.cn/suanli-api"

    # When False, registration auto-verifies the email and immediately issues
    # a JWT — no verification mail is sent. Use when SMTP isn't configured.
    # Default: True (production behaviour). Server .env overrides to False.
    email_verification_required: bool = True

    # Email — pick ONE provider. Order of precedence:
    #   1. Resend (HTTP API; easiest — sign up at resend.com, get key)
    #   2. SMTP (if smtp_host + smtp_user set)
    #   3. Fallback: log link to journal (current state)
    resend_api_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "Prism <noreply@ai100trading.cn>"
    frontend_base: str = "https://www.ai100trading.cn"

    # v0.3 chain monitors — comma-separated list of enabled chains.
    # Set to "" to disable all (e.g. local dev where you don't want background polling).
    chain_monitors: str = "tron,solana,evm"
    chain_poll_interval_s: int = 30
    chain_topup_intent_ttl_min: int = 30

    # USDT receive addresses (also surfaced on the homepage)
    chain_tron_address: str = "TT24g41HLptouzxGycZxQKmWaTENK4K4HG"
    chain_solana_address: str = "66p5tnV6Fd7x5QmRE6X772PMVmVUVgozRzATJ4Ns9iQn"
    chain_evm_address: str = "0xC862ff9Fd79D180950E546DBB8b108d5c9c38582"

    # USDC contract addresses (we accept USDC across all chains, NOT USDT).
    # ⚠️ 上线前用 tronscan / bscscan 等浏览器复核每个合约。
    tron_usdc_contract: str = "TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8"
    solana_usdc_mint: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    bsc_usdc_contract: str = "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d"
    polygon_usdc_contract: str = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
    arbitrum_usdc_contract: str = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
    ethereum_usdc_contract: str = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

    # Default EVM sub-chain (the one we tell users to send USDC on first)
    evm_default_chain: str = "bsc"

    # Public RPC / Etherscan-style API endpoints
    tron_api_base: str = "https://api.trongrid.io"
    solana_rpc_url: str = "https://api.mainnet-beta.solana.com"
    bscscan_api_base: str = "https://api.bscscan.com/api"
    polygonscan_api_base: str = "https://api.polygonscan.com/api"
    arbiscan_api_base: str = "https://api.arbiscan.io/api"
    etherscan_api_base: str = "https://api.etherscan.io/api"

    # Optional API keys (improve rate limits)
    trongrid_api_key: str = ""
    bscscan_api_key: str = ""
    polygonscan_api_key: str = ""
    arbiscan_api_key: str = ""
    etherscan_api_key: str = ""

    # v0.3 capacity alerts
    capacity_window_min: int = 5
    capacity_check_interval_s: int = 60
    capacity_5xx_warn_pct: float = 5.0
    capacity_rpm_warn_pct: float = 80.0
    capacity_default_rpm_quota: int = 1000  # used if channel.rpm_quota not set
    capacity_alert_debounce_min: int = 30
    admin_alert_emails: str = ""  # comma-separated

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def master_key(self) -> bytes:
        if len(self.master_key_hex) != 64:
            raise ValueError(
                "PRISM_MASTER_KEY_HEX must be 64 hex chars (32 bytes). "
                "Generate with: openssl rand -hex 32"
            )
        return bytes.fromhex(self.master_key_hex)


settings = Settings()
