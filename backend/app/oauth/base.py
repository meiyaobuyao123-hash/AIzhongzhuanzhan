"""OAuth 2.0 provider base + normalized profile shape."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OAuthProfile:
    """Normalized profile shape across providers."""

    provider: str
    provider_uid: str
    email: str | None
    display_name: str | None
    avatar_url: str | None
    access_token: str  # short-lived; we encrypt + store for future use


class OAuthProvider(ABC):
    name: str
    authorize_url: str
    scope: str

    @abstractmethod
    def is_configured(self) -> bool:
        """True if client_id + client_secret are set in env."""

    @abstractmethod
    def authorize_redirect(self, *, state: str, redirect_uri: str) -> str:
        """Build the URL the user should be redirected to."""

    @abstractmethod
    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthProfile:
        """Exchange auth code for access_token + fetch user profile."""
