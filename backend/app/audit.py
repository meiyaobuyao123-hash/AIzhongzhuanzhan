"""Audit log helpers.

Every privileged action (admin CLI mutation, user account changes, etc.) calls
`record_audit(...)` which inserts an `audit_log` row.

Failures here are logged but never raise — auditing should never break the
underlying operation.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import logger
from app.models.orm import AuditLog


async def record_audit(
    db: AsyncSession,
    *,
    actor: str,
    action: str,
    target: str | None = None,
    payload: dict[str, Any] | None = None,
    ip: str | None = None,
) -> None:
    """Insert an audit_log row in the same transaction as the caller's session."""
    try:
        # Strip any obvious secret values from payload (defensive)
        cleaned = _redact(payload) if payload else None
        db.add(AuditLog(
            actor=actor,
            action=action,
            target=target,
            payload=json.dumps(cleaned) if cleaned else None,
            ip=ip,
        ))
        # We don't commit here — caller's commit picks it up
    except Exception as exc:
        logger.warning("audit_record_failed", action=action, error=str(exc))


_SENSITIVE_KEY_FRAGMENTS = ("password", "secret", "token", "key", "private")


def _redact(d: dict[str, Any]) -> dict[str, Any]:
    """Replace secret-like values with '***'. Best effort, not perfect."""
    out: dict[str, Any] = {}
    for k, v in d.items():
        kl = k.lower()
        if any(frag in kl for frag in _SENSITIVE_KEY_FRAGMENTS):
            if isinstance(v, str) and len(v) > 8:
                out[k] = f"{v[:4]}***{v[-2:]}"
            else:
                out[k] = "***"
        elif isinstance(v, dict):
            out[k] = _redact(v)
        else:
            out[k] = v
    return out
