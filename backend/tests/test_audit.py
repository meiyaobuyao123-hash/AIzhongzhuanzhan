"""Audit log helper tests."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import select

from app.audit import _redact, record_audit
from app.models.orm import AuditLog


def test_redact_removes_secret_keys():
    redacted = _redact({"name": "alice", "password": "supersecret123"})
    assert redacted["name"] == "alice"
    assert redacted["password"] != "supersecret123"
    assert "***" in redacted["password"]


def test_redact_handles_short_secrets():
    redacted = _redact({"api_key": "abc"})
    assert redacted["api_key"] == "***"


def test_redact_recursive():
    redacted = _redact({"user": {"name": "x", "private_token": "should-hide"}})
    assert redacted["user"]["name"] == "x"
    assert "***" in redacted["user"]["private_token"]


def test_redact_keeps_long_secret_prefix_for_grep():
    redacted = _redact({"upstream_key": "sk-ant-api03-abc1234567890"})
    s = redacted["upstream_key"]
    assert s.startswith("sk-a")  # first 4
    assert "***" in s


@pytest.mark.asyncio
async def test_record_audit_inserts_row(db_session):
    await record_audit(
        db_session,
        actor="admin-cli",
        action="user.create",
        target="42",
        payload={"email": "test@example.com"},
        ip="127.0.0.1",
    )
    await db_session.commit()

    rows = (await db_session.execute(select(AuditLog))).scalars().all()
    assert len(rows) == 1
    log = rows[0]
    assert log.actor == "admin-cli"
    assert log.action == "user.create"
    assert log.target == "42"
    assert json.loads(log.payload)["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_record_audit_redacts_payload_secrets(db_session):
    await record_audit(
        db_session,
        actor="admin-cli",
        action="channel.create",
        target="1",
        payload={
            "provider": "anthropic",
            "upstream_key": "sk-ant-api03-real-secret-12345",
        },
    )
    await db_session.commit()

    log = (await db_session.execute(select(AuditLog))).scalar_one()
    payload = json.loads(log.payload)
    assert payload["provider"] == "anthropic"
    assert payload["upstream_key"] != "sk-ant-api03-real-secret-12345"
    assert "***" in payload["upstream_key"]


@pytest.mark.asyncio
async def test_record_audit_does_not_raise_on_failure(db_session):
    """Even with weird input, record_audit must not raise (auditing is best-effort)."""
    # Pass a non-serializable payload value via type misuse
    class Bad:
        pass

    # Should not raise — record_audit catches and logs
    await record_audit(
        db_session,
        actor="admin",
        action="weird",
        payload={"obj": Bad()},
    )
