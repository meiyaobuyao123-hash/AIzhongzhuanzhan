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
    topup_fee_basis_points: int = 5
    """5 bps = 0.05% = 万分之五"""

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

    # SMTP (empty = verification logs to journal)
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

    # USDT contract addresses
    tron_usdt_contract: str = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    solana_usdc_mint: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    bsc_usdt_contract: str = "0x55d398326f99059fF775485246999027B3197955"
    polygon_usdt_contract: str = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
    arbitrum_usdt_contract: str = "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"
    ethereum_usdt_contract: str = "0xdAC17F958D2ee523a2206206994597C13D831ec7"

    # Default EVM sub-chain (the one we tell users to send USDT on first)
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
