"""GitHub OAuth.

Flow:
  authorize:  https://github.com/login/oauth/authorize?client_id=&redirect_uri=&state=&scope=
  callback gives ?code=&state=
  POST https://github.com/login/oauth/access_token  (form-encoded, returns JSON)
  GET https://api.github.com/user                  (with Authorization: Bearer)
"""

from __future__ import annotations

from urllib.parse import urlencode

import httpx

from app.config import settings
from app.errors import PrismException
from app.oauth.base import OAuthProfile, OAuthProvider


class GitHubProvider(OAuthProvider):
    name = "github"
    authorize_url = "https://github.com/login/oauth/authorize"
    token_url = "https://github.com/login/oauth/access_token"
    user_url = "https://api.github.com/user"
    user_emails_url = "https://api.github.com/user/emails"
    scope = "read:user user:email"

    def is_configured(self) -> bool:
        return bool(settings.oauth_github_client_id and settings.oauth_github_client_secret)

    def authorize_redirect(self, *, state: str, redirect_uri: str) -> str:
        params = {
            "client_id": settings.oauth_github_client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": self.scope,
        }
        return f"{self.authorize_url}?{urlencode(params)}"

    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthProfile:
        async with httpx.AsyncClient(timeout=15) as client:
            tok = await client.post(
                self.token_url,
                data={
                    "client_id": settings.oauth_github_client_id,
                    "client_secret": settings.oauth_github_client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            if tok.status_code != 200:
                raise PrismException(f"GitHub token exchange failed: HTTP {tok.status_code}")
            tok_data = tok.json()
            access_token = tok_data.get("access_token")
            if not access_token:
                raise PrismException(
                    f"GitHub token exchange returned no access_token: {tok_data}"
                )

            user_resp = await client.get(
                self.user_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if user_resp.status_code != 200:
                raise PrismException(f"GitHub user fetch failed: HTTP {user_resp.status_code}")
            user_data = user_resp.json()

            email = user_data.get("email")
            if not email:
                # public email may be hidden; fetch the verified primary
                emails_resp = await client.get(
                    self.user_emails_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if emails_resp.status_code == 200:
                    for e in emails_resp.json():
                        if e.get("primary") and e.get("verified"):
                            email = e.get("email")
                            break

        return OAuthProfile(
            provider=self.name,
            provider_uid=str(user_data["id"]),
            email=email,
            display_name=user_data.get("name") or user_data.get("login"),
            avatar_url=user_data.get("avatar_url"),
            access_token=access_token,
        )
