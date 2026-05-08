"""Request executor: routing + retry chain + failure tracking + circuit breaker.

Used by both /v1/messages and /v1/chat/completions routes. Handles:
  - Picking healthy candidates
  - Forwarding via the right Provider
  - Mapping upstream errors → cooldown / retry / give up
  - Tracking which channels were tried (for usage_log.tried_channels)

v0.2 retry policy:
  - Up to MAX_ATTEMPTS (3) tries, each on a different channel
  - Network errors / timeouts / 5xx → mark_failure + retry on next channel
  - 429 → mark_failure with retry_after = upstream Retry-After header
  - 401/403 → DON'T cooldown (key is broken; admin needs to fix); fail fast
  - 4xx other (400/404/etc) → return to client, don't retry
  - Streaming: only retry if no bytes written to client yet
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from app.config import settings
from app.errors import NoChannelAvailable, PrismException
from app.limits import (
    mark_channel_failure,
    mark_channel_success,
)
from app.logging_config import logger
from app.models.orm import Channel, Model
from app.providers import make_provider
from app.providers.base import Provider
from app.routing.router import pick_one

MAX_ATTEMPTS = 3
NON_RETRYABLE_4XX = {400, 401, 403, 404, 422}


class AllChannelsFailed(PrismException):
    """All channel attempts exhausted, last error attached."""

    status_code = 502
    error_type = "api_error"
    code = "all_channels_failed"


@dataclass
class ExecutionAttempt:
    channel_id: int
    upstream_status: int | None = None
    error: str | None = None


@dataclass
class ExecutionResult:
    """What an executor returns for a non-streaming response."""

    channel: Channel
    upstream: httpx.Response
    response_body: dict | None  # parsed JSON; None if streaming
    attempts: list[ExecutionAttempt]
    provider: Provider  # caller closes


async def execute_with_retry(
    *,
    model: Model,
    request_body: dict,
    is_streaming: bool,
    db,
    redis_client,
    method: str = "messages",  # "messages" or "chat_completions"
) -> ExecutionResult:
    """Drive the retry chain. Returns ExecutionResult for the SUCCESSFUL attempt.

    For non-streaming: returns the parsed JSON response. Caller billing.
    For streaming: returns the open httpx.Response (caller pumps it).

    Raises AllChannelsFailed if everything tried.
    """
    tried: set[int] = set()
    attempts: list[ExecutionAttempt] = []
    last_error: PrismException | None = None

    for attempt_idx in range(MAX_ATTEMPTS):
        try:
            channel = await pick_one(
                model, db, redis_client,
                exclude=tried, request_body=request_body,
            )
        except NoChannelAvailable as exc:
            last_error = exc
            break

        tried.add(channel.id)
        attempt = ExecutionAttempt(channel_id=channel.id)
        attempts.append(attempt)

        provider = make_provider(channel, settings.master_key)
        # Strip Prism-internal hint fields (e.g. __prism_user_id) before forwarding.
        # Upstream APIs might reject unknown fields, and we never want to leak our
        # routing metadata.
        upstream_body = {
            k: v for k, v in request_body.items() if not k.startswith("__prism_")
        }
        try:
            if method == "messages":
                upstream = await provider.messages(upstream_body, stream=is_streaming)
            elif method == "chat_completions":
                upstream = await provider.chat_completions(upstream_body, stream=is_streaming)
            else:
                raise ValueError(f"Unknown method: {method}")
        except httpx.HTTPError as exc:
            await provider.aclose()
            attempt.error = f"connect_error:{type(exc).__name__}"
            await mark_channel_failure(channel.id, redis_client)
            last_error = PrismException(f"Upstream connection failed: {exc}")
            logger.warning(
                "executor_connect_error",
                channel_id=channel.id, attempt=attempt_idx, error=str(exc),
            )
            continue

        attempt.upstream_status = upstream.status_code

        # ─── Classify the response ───
        if upstream.status_code < 300:
            # Success path
            await mark_channel_success(channel.id, redis_client)
            # v0.3 C1: record sticky route for prompt-cache requests
            try:
                from app.routing.sticky import record_sticky
                await record_sticky(model, request_body, channel.id, redis_client)
            except Exception:
                pass  # sticky failure must not break the request
            if is_streaming:
                return ExecutionResult(
                    channel=channel, upstream=upstream, response_body=None,
                    attempts=attempts, provider=provider,
                )
            else:
                await upstream.aread()
                try:
                    body = upstream.json()
                except Exception:
                    body = {}
                return ExecutionResult(
                    channel=channel, upstream=upstream, response_body=body,
                    attempts=attempts, provider=provider,
                )

        # Read upstream body (for error messages)
        await upstream.aread()
        upstream_body_text = upstream.text[:1000]
        attempt.error = f"http_{upstream.status_code}:{upstream_body_text[:200]}"

        # 4xx that are NOT retryable: return to client
        if upstream.status_code in NON_RETRYABLE_4XX:
            # 401/403 means our upstream key is bad → mark_failure to cooldown
            # (operator should rotate the key)
            if upstream.status_code in (401, 403):
                await mark_channel_failure(channel.id, redis_client)
                logger.error(
                    "executor_upstream_auth_failure",
                    channel_id=channel.id, status=upstream.status_code,
                )
            # Don't retry — return upstream response as-is to client
            return ExecutionResult(
                channel=channel, upstream=upstream, response_body=_safe_json(upstream),
                attempts=attempts, provider=provider,
            )

        # 429 → honour Retry-After
        if upstream.status_code == 429:
            retry_after = _parse_retry_after(upstream.headers.get("retry-after"))
            await mark_channel_failure(
                channel.id, redis_client, retry_after_s=retry_after
            )
            await provider.aclose()
            last_error = PrismException(
                f"Upstream {channel.name} rate-limited (429)"
            )
            logger.warning(
                "executor_rate_limit", channel_id=channel.id, retry_after=retry_after,
            )
            continue

        # 5xx
        if upstream.status_code >= 500:
            await mark_channel_failure(channel.id, redis_client)
            await provider.aclose()
            last_error = PrismException(
                f"Upstream {channel.name} returned {upstream.status_code}"
            )
            logger.warning(
                "executor_upstream_5xx",
                channel_id=channel.id, status=upstream.status_code,
            )
            continue

        # Catch-all: return to client
        return ExecutionResult(
            channel=channel, upstream=upstream, response_body=_safe_json(upstream),
            attempts=attempts, provider=provider,
        )

    # Out of attempts
    if last_error is None:
        last_error = PrismException("All channels failed (no specific error)")
    raise AllChannelsFailed(
        f"All {len(attempts)} channel attempts failed: {last_error.message}",
    )


def _parse_retry_after(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return max(0, int(value))
    except (ValueError, TypeError):
        return None


def _safe_json(resp: httpx.Response) -> dict:
    try:
        return resp.json()
    except Exception:
        return {"error": {"message": resp.text[:1000], "type": "api_error"}}


def attempts_to_json(attempts: list[ExecutionAttempt]) -> str:
    return json.dumps([
        {"channel_id": a.channel_id, "status": a.upstream_status, "error": a.error}
        for a in attempts
    ])
