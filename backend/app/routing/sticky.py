"""Prompt cache sticky routing.

Anthropic's prompt cache is bound to a single upstream account: account A's
cache is invisible to account B. If we randomly pick a channel for each
request from the same conversation, we'd persistently miss the cache.

Strategy: compute a fingerprint of the request's first system + first user
message, and stick subsequent requests with the same fingerprint to the same
channel for 5 minutes (matches Anthropic's cache TTL).

Only enabled when the request body contains ``cache_control`` blocks
(Anthropic dialect). For OpenAI dialect we don't sticky-route in v0.3 because
OpenAI prompt cache is automatic and channel-level — sticking doesn't help.
"""

from __future__ import annotations

import hashlib
import json

from app.models.orm import Model

STICKY_TTL_SECONDS = 5 * 60  # match Anthropic prompt cache TTL


def has_cache_control(request_body: dict) -> bool:
    """Detect whether the request opts into prompt caching.

    Anthropic style:
      messages: [{role, content: [{type:'text', text:'...', cache_control:{type:'ephemeral'}}]}]
      system:   [{type:'text', text:'...', cache_control:{...}}]
      tools:    [{name, ..., cache_control:{...}}]

    Returns True if any cache_control field appears anywhere in the body.
    """
    return _walk_for_cache_control(request_body)


def _walk_for_cache_control(obj) -> bool:
    if isinstance(obj, dict):
        if "cache_control" in obj:
            return True
        return any(_walk_for_cache_control(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_walk_for_cache_control(v) for v in obj)
    return False


def compute_fingerprint(request_body: dict) -> str:
    """Hash the first system + first user message to group conversations.

    We deliberately ignore later messages in the conversation — the cache key
    is the *prefix* (system + initial context), and Anthropic caches at the
    prefix level. So a long ongoing conversation routes to the same channel as
    its initial turn.
    """
    parts: list[str] = []

    sys = request_body.get("system")
    if isinstance(sys, str):
        parts.append("S:" + sys)
    elif isinstance(sys, list):
        for b in sys:
            if isinstance(b, dict) and b.get("type") == "text":
                parts.append("S:" + (b.get("text") or ""))

    # First user message only
    for msg in request_body.get("messages") or []:
        if msg.get("role") == "user":
            content = msg.get("content")
            if isinstance(content, str):
                parts.append("U:" + content)
            elif isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "text":
                        parts.append("U:" + (b.get("text") or ""))
            break

    if not parts:
        # No usable prefix — can't fingerprint
        return ""

    h = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return h[:24]


def _sticky_key(user_id: int, model_id: str, fingerprint: str) -> str:
    return f"prism:sticky:{user_id}:{model_id}:{fingerprint}"


async def lookup_sticky(
    model: Model, request_body: dict, redis_client
) -> int | None:
    """Return previously-routed channel_id for this request's prefix, or None.

    Returns None when:
      - request body doesn't opt into prompt caching (no cache_control)
      - no prior route recorded for this fingerprint
      - user_id missing in body (set by middleware in v0.3)
    """
    if not has_cache_control(request_body):
        return None
    user_id = request_body.get("__prism_user_id")
    if user_id is None:
        return None
    fp = compute_fingerprint(request_body)
    if not fp:
        return None
    raw = await redis_client.get(_sticky_key(user_id, model.model_id, fp))
    if raw is None:
        return None
    try:
        return int(raw)
    except (ValueError, TypeError):
        return None


async def record_sticky(
    model: Model,
    request_body: dict,
    channel_id: int,
    redis_client,
) -> None:
    """Persist the (user, model, fingerprint) → channel_id mapping for 5 min."""
    if not has_cache_control(request_body):
        return
    user_id = request_body.get("__prism_user_id")
    if user_id is None:
        return
    fp = compute_fingerprint(request_body)
    if not fp:
        return
    await redis_client.setex(
        _sticky_key(user_id, model.model_id, fp),
        STICKY_TTL_SECONDS,
        str(channel_id),
    )


__all__ = [
    "STICKY_TTL_SECONDS",
    "has_cache_control",
    "compute_fingerprint",
    "lookup_sticky",
    "record_sticky",
]
