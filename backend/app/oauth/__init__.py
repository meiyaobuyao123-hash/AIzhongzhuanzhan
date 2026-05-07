"""OAuth provider abstractions + factory."""

from app.oauth.base import OAuthProfile, OAuthProvider
from app.oauth.github import GitHubProvider
from app.oauth.google import GoogleProvider

PROVIDERS: dict[str, OAuthProvider] = {
    "github": GitHubProvider(),
    "google": GoogleProvider(),
}


def get_provider(name: str) -> OAuthProvider | None:
    p = PROVIDERS.get(name)
    if p is None or not p.is_configured():
        return None
    return p


__all__ = ["OAuthProfile", "OAuthProvider", "get_provider", "PROVIDERS"]
