"""Auth tests: key generation, header parsing, lookup."""

from __future__ import annotations

import pytest

from app.auth import (
    authenticate,
    generate_prism_key,
    parse_authorization,
)
from app.errors import InvalidAPIKey, UserDisabled
from app.models.orm import ApiKey, User


def test_generate_prism_key_format():
    full, hashed, prefix, last4 = generate_prism_key()
    assert full.startswith("sk-prism-")
    assert len(full) > 30
    assert hashed != full and hashed.startswith("$argon2")
    assert prefix == full[:13]   # "sk-prism-XXXX"
    assert last4 == full[-4:]


def test_generate_unique_keys():
    keys = {generate_prism_key()[0] for _ in range(20)}
    assert len(keys) == 20


# parse_authorization ---------------------------------------------------------


def test_parse_bearer():
    assert parse_authorization("Bearer sk-prism-abc123") == "sk-prism-abc123"


def test_parse_bearer_lowercase():
    assert parse_authorization("bearer sk-prism-abc123") == "sk-prism-abc123"


def test_parse_no_bearer_prefix():
    assert parse_authorization("sk-prism-direct") == "sk-prism-direct"


def test_parse_x_api_key():
    assert parse_authorization(None, x_api_key="sk-prism-via-xapi") == "sk-prism-via-xapi"


def test_parse_authorization_takes_precedence_over_x_api_key():
    got = parse_authorization("Bearer sk-prism-auth", x_api_key="sk-prism-other")
    assert got == "sk-prism-auth"


def test_parse_missing_raises():
    with pytest.raises(InvalidAPIKey):
        parse_authorization(None)


def test_parse_invalid_format_raises():
    with pytest.raises(InvalidAPIKey):
        parse_authorization("Bearer notakey")


# authenticate ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_authenticate_success(db_session):
    full, hashed, prefix, last4 = generate_prism_key()
    user = User(email="alice@example.com")
    db_session.add(user)
    await db_session.flush()
    db_session.add(ApiKey(
        user_id=user.id, key_hash=hashed, key_prefix=prefix, key_last4=last4
    ))
    await db_session.commit()

    got_user, got_key = await authenticate(full, db_session)
    assert got_user.id == user.id
    assert got_key.key_prefix == prefix


@pytest.mark.asyncio
async def test_authenticate_invalid_key(db_session):
    user = User(email="bob@example.com")
    db_session.add(user)
    await db_session.flush()
    full, hashed, prefix, last4 = generate_prism_key()
    db_session.add(ApiKey(
        user_id=user.id, key_hash=hashed, key_prefix=prefix, key_last4=last4
    ))
    await db_session.commit()

    with pytest.raises(InvalidAPIKey):
        await authenticate("sk-prism-totallywrong-key-doesnt-exist", db_session)


@pytest.mark.asyncio
async def test_authenticate_disabled_key_skipped(db_session):
    full, hashed, prefix, last4 = generate_prism_key()
    user = User(email="carol@example.com")
    db_session.add(user)
    await db_session.flush()
    db_session.add(ApiKey(
        user_id=user.id, key_hash=hashed, key_prefix=prefix, key_last4=last4,
        enabled=False,
    ))
    await db_session.commit()

    with pytest.raises(InvalidAPIKey):
        await authenticate(full, db_session)


@pytest.mark.asyncio
async def test_authenticate_disabled_user_raises_user_disabled(db_session):
    full, hashed, prefix, last4 = generate_prism_key()
    user = User(email="dan@example.com", enabled=False)
    db_session.add(user)
    await db_session.flush()
    db_session.add(ApiKey(
        user_id=user.id, key_hash=hashed, key_prefix=prefix, key_last4=last4
    ))
    await db_session.commit()

    with pytest.raises(UserDisabled):
        await authenticate(full, db_session)
