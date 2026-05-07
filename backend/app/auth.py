"""Prism Key generation + verification.

Key format: ``sk-prism-`` + 32 chars urlsafe base64 (≈41 chars total).

We store argon2 hash + prefix + last4. To authenticate, brute-force iterate enabled
keys and argon2.verify each. v0.1 OK; v0.2 will add prefix index for O(1) lookup.
"""

from __future__ import annotations

import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import InvalidAPIKey, UserDisabled
from app.models.orm import ApiKey, User

_PASSWORD_HASHER = PasswordHasher()
_PREFIX = "sk-prism-"


def generate_prism_key() -> tuple[str, str, str, str]:
    """Generate a new key.

    Returns:
        (full_key, key_hash, key_prefix, key_last4)

    The full key is shown to the user **once** at creation time. Only its hash
    + display fields are stored.
    """
    raw = secrets.token_urlsafe(24)  # ~32 chars urlsafe base64
    full = f"{_PREFIX}{raw}"
    hashed = _PASSWORD_HASHER.hash(full)
    prefix = full[: len(_PREFIX) + 4]   # "sk-prism-XXXX"
    last4 = full[-4:]
    return full, hashed, prefix, last4


def parse_authorization(
    authorization: str | None, x_api_key: str | None = None
) -> str:
    """Extract raw Prism Key from headers.

    Supports:
      - "Authorization: Bearer sk-prism-..."
      - "Authorization: sk-prism-..."
      - "x-api-key: sk-prism-..."  (Anthropic style)
    """
    candidate: str | None = None
    if authorization:
        a = authorization.strip()
        if a.lower().startswith("bearer "):
            candidate = a[7:].strip()
        elif a.startswith(_PREFIX):
            candidate = a
    if not candidate and x_api_key:
        candidate = x_api_key.strip()

    if not candidate or not candidate.startswith(_PREFIX):
        raise InvalidAPIKey("Missing or malformed API key")
    return candidate


async def authenticate(
    raw_key: str, db: AsyncSession
) -> tuple[User, ApiKey]:
    """Verify a raw key against all enabled api_keys.

    O(N) with argon2.verify per row — acceptable for v0.1 scale (<10k keys).
    v0.2 will index by prefix and only verify matching prefix.
    """
    rows = await db.execute(select(ApiKey).where(ApiKey.enabled.is_(True)))
    for ak in rows.scalars():
        try:
            _PASSWORD_HASHER.verify(ak.key_hash, raw_key)
        except VerifyMismatchError:
            continue
        # Match found
        user = await db.get(User, ak.user_id)
        if user is None:
            continue
        if not user.enabled:
            raise UserDisabled("User account is disabled")
        return user, ak

    raise InvalidAPIKey("Invalid API key")
