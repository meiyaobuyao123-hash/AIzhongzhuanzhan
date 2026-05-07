"""Google OAuth.

Flow:
  authorize:  https://accounts.google.com/o/oauth2/v2/auth?client_id=&redirect_uri=&state=&scope=&response_type=code&access_type=offline
  callback gives ?code=&state=
  POST https://oauth2.googleapis.com/token
  GET https://www.googleapis.com/oauth2/v3/userinfo
"""

from __future__ import annotations

from urllib.parse import urlencode

import httpx

from app.config import settings
from app.errors import PrismException
from app.oauth.base import OAuthProfile, OAuthProvider


class GoogleProvider(OAuthProvider):
    name = "google"
    authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    scope = "openid email profile"

    def is_configured(self) -> bool:
        return bool(settings.oauth_google_client_id and settings.oauth_google_client_secret)

    def authorize_redirect(self, *, state: str, redirect_uri: str) -> str:
        params = {
            "client_id": settings.oauth_google_client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": self.scope,
            "response_type": "code",
            "access_type": "online",  # offline if we want refresh tokens
            "prompt": "select_account",
        }
        return f"{self.authorize_url}?{urlencode(params)}"

    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthProfile:
        async with httpx.AsyncClient(timeout=15) as client:
            tok = await client.post(
                self.token_url,
                data={
                    "client_id": settings.oauth_google_client_id,
                    "client_secret": settings.oauth_google_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            if tok.status_code != 200:
                raise PrismException(f"Google token exchange failed: HTTP {tok.status_code}")
            tok_data = tok.json()
            access_token = tok_data.get("access_token")
            if not access_token:
                raise PrismException(
                    f"Google token exchange returned no access_token: {tok_data}"
                )

            user_resp = await client.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if user_resp.status_code != 200:
                raise PrismException(f"Google userinfo failed: HTTP {user_resp.status_code}")
            ui = user_resp.json()

        return OAuthProfile(
            provider=self.name,
            provider_uid=str(ui["sub"]),
            email=ui.get("email"),
            display_name=ui.get("name"),
            avatar_url=ui.get("picture"),
            access_token=access_token,
        )
