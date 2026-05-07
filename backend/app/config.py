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
