"""POST /v1/messages — Anthropic-native protocol passthrough.

Uses app/routing/executor.py for the full retry chain (multi-channel + circuit
breaker + failover). v0.2: protocol translator handles non-Anthropic models if
the user routes them through /v1/messages (e.g. /v1/messages with model=gpt-5
auto-translates to OpenAI). v0.1 used to 400 in this case.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import authenticate, parse_authorization
from app.billing import (
    calculate_cost_micro_cents,
    check_balance_or_402,
    estimate_max_cost_micro_cents,
    record_request_outcome,
)
from app.deps import client_ip, get_db
from app.errors import PrismException, error_response
from app.limits import check_rpm_limit, default_rpm_for_user
from app.redis_client import get_redis
from app.routing import (
    AllChannelsFailed,
    attempts_to_json,
    execute_with_retry,
    find_model,
)
from app.schemas.common import StreamingState, Usage
from app.streaming import stream_with_usage

router = APIRouter(tags=["messages"])


@router.post("/v1/messages")
async def post_messages(
    body: dict[str, Any],
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
    db: AsyncSession = Depends(get_db),
):
    request_id = str(uuid.uuid4())
    started = time.monotonic()

    # ---- 1. Auth ------------------------------------------------------------
    try:
        raw_key = parse_authorization(authorization, x_api_key)
        user, api_key = await authenticate(raw_key, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    # ---- 1b. Rate limit -----------------------------------------------------
    try:
        rpm = api_key.rate_limit_rpm or default_rpm_for_user(
            user.total_topped_up_micro_cents, user.tier
        )
        await check_rpm_limit(api_key.id, rpm, get_redis())
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    # ---- 2. Model + provider check -----------------------------------------
    try:
        model_id = body.get("model")
        if not model_id:
            return error_response(
                400, "Missing 'model' field", "invalid_request_error", param="model"
            )

        if api_key.whitelist_list is not None and model_id not in api_key.whitelist_list:
            return error_response(
                403,
                f"Model {model_id} not allowed for this API key",
                "permission_error",
                code="model_not_in_whitelist",
            )

        model = await find_model(model_id, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    # v0.2 B5: any provider works on /v1/messages — translators handle non-Anthropic.
    needs_translation = model.provider != "anthropic"

    # ---- 3. Balance pre-flight --------------------------------------------
    estimated_input = _estimate_prompt_tokens(body)
    max_output = int(body.get("max_tokens", 4096) or 4096)
    estimated_max = estimate_max_cost_micro_cents(estimated_input, max_output, model)
    try:
        await check_balance_or_402(db, user, estimated_max)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    # ---- 4. Execute via retry chain ----------------------------------------
    is_streaming = bool(body.get("stream"))
    redis = get_redis()

    # v0.3 C1: tag the body so sticky-routing can read user_id without leaking
    # it to upstream (we strip it before forwarding via dict copy in providers,
    # but defensively check anyway in oai_request_to_anth/etc.)
    body_with_uid = {**body, "__prism_user_id": user.id}

    try:
        result = await execute_with_retry(
            model=model,
            request_body=body_with_uid,
            is_streaming=is_streaming,
            db=db,
            redis_client=redis,
            method="messages",
        )
    except AllChannelsFailed as exc:
        await record_request_outcome(
            db, request_id=request_id, user=user, api_key=api_key,
            channel=None, model=model, usage=Usage(),
            cost_micro_cents=0, status="error",
            error_message=exc.message,
            is_streaming=is_streaming, client_ip=client_ip(request),
        )
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    channel = result.channel
    provider = result.provider
    upstream = result.upstream
    tried = attempts_to_json(result.attempts)
    attempt_index = len(result.attempts) - 1

    # Upstream non-2xx that the executor decided to surface
    if upstream.status_code >= 400:
        try:
            return JSONResponse(
                status_code=upstream.status_code,
                content=result.response_body,
            )
        finally:
            await provider.aclose()
            latency_ms = int((time.monotonic() - started) * 1000)
            await record_request_outcome(
                db, request_id=request_id, user=user, api_key=api_key,
                channel=channel, model=model, usage=Usage(),
                cost_micro_cents=0, status="error",
                http_status=upstream.status_code,
                error_message=str(result.response_body)[:1000],
                is_streaming=is_streaming, client_ip=client_ip(request),
            )

    # ---- 5a. Non-streaming success ----------------------------------------
    if not is_streaming:
        try:
            response_body = result.response_body or {}
            usage = provider.parse_usage_non_streaming(response_body)
            cost = calculate_cost_micro_cents(usage, model)
            latency_ms = int((time.monotonic() - started) * 1000)
            await record_request_outcome_v02(
                db, request_id=request_id, user=user, api_key=api_key,
                channel=channel, model=model, usage=usage,
                cost_micro_cents=cost, status="ok",
                http_status=upstream.status_code,
                latency_ms=latency_ms,
                attempt_index=attempt_index,
                tried_channels=tried,
                is_streaming=False, client_ip=client_ip(request),
            )

            # B5: if upstream wasn't anthropic, translate the response back to
            # Anthropic format (since this is /v1/messages, client expects Anthropic shape)
            if needs_translation:
                from app.providers.translators.anth_to_oai import oai_response_to_anth
                response_body = oai_response_to_anth(response_body, requested_model=model_id)

            return JSONResponse(status_code=upstream.status_code, content=response_body)
        finally:
            await provider.aclose()

    # ---- 5b. Streaming success --------------------------------------------
    async def on_complete(state: StreamingState) -> None:
        usage = state.usage
        cost = calculate_cost_micro_cents(usage, model)
        latency_ms = int((time.monotonic() - started) * 1000)
        await record_request_outcome_v02(
            db, request_id=request_id, user=user, api_key=api_key,
            channel=channel, model=model, usage=usage, cost_micro_cents=cost,
            status="ok" if state.stats.finished_normally else "partial",
            http_status=state.stats.upstream_status,
            latency_ms=latency_ms,
            ttft_ms=state.stats.ttft_ms,
            attempt_index=attempt_index,
            tried_channels=tried,
            is_streaming=True, client_ip=client_ip(request),
        )
        await provider.aclose()

    if needs_translation:
        # OpenAI/Google upstream → translate stream to Anthropic SSE
        from app.providers.translators.anth_to_oai import oai_stream_to_anth
        translated = oai_stream_to_anth(upstream.aiter_bytes(), requested_model=model_id)
        return StreamingResponse(
            _wrap_translated_stream(translated, provider, on_complete, upstream),
            media_type="text/event-stream",
            headers={"x-prism-request-id": request_id},
        )

    return StreamingResponse(
        stream_with_usage(upstream, provider, on_complete),
        media_type="text/event-stream",
        headers={"x-prism-request-id": request_id},
    )


async def _wrap_translated_stream(translated_iter, provider, on_complete, upstream):
    """For translated streams we don't accumulate usage incrementally — provider
    can't parse foreign-format chunks. Read full upstream usage at end via
    a separate path. v0.2 simplification: emit translated chunks; bill from
    final usage tracker in translator output (which contains usage in the last
    Anthropic message_delta event)."""
    import json

    from app.schemas.common import StreamingState, Usage

    state = StreamingState()
    try:
        async for chunk in translated_iter:
            yield chunk
            # Try to extract usage from message_delta events (Anthropic format)
            if b"message_delta" in chunk:
                try:
                    text = chunk.decode("utf-8", errors="replace")
                    for line in text.split("\n"):
                        if line.startswith("data:"):
                            data = json.loads(line[5:].strip())
                            u = data.get("usage") or {}
                            if u.get("output_tokens"):
                                state.usage = Usage(
                                    prompt_tokens=state.usage.prompt_tokens or 0,
                                    completion_tokens=u["output_tokens"],
                                )
                except Exception:
                    pass
            elif b"message_start" in chunk:
                try:
                    text = chunk.decode("utf-8", errors="replace")
                    for line in text.split("\n"):
                        if line.startswith("data:"):
                            data = json.loads(line[5:].strip())
                            u = (data.get("message") or {}).get("usage") or {}
                            state.usage = Usage(
                                prompt_tokens=u.get("input_tokens", 0),
                                completion_tokens=state.usage.completion_tokens,
                            )
                except Exception:
                    pass
        state.stats.finished_normally = True
    finally:
        try:
            await upstream.aclose()
        except Exception:
            pass
        await on_complete(state)


# ---- Helpers ----------------------------------------------------------------


async def record_request_outcome_v02(
    db,
    *,
    request_id,
    user,
    api_key,
    channel,
    model,
    usage,
    cost_micro_cents,
    status,
    http_status=None,
    error_message=None,
    latency_ms=None,
    ttft_ms=None,
    attempt_index=0,
    tried_channels=None,
    is_streaming=False,
    client_ip=None,
):
    """Wrap v0.1 record_request_outcome to also save attempt_index + tried_channels."""
    # Direct insert with v0.2 fields
    from app.models.orm import BalanceTransaction, UsageLog
    log = UsageLog(
        request_id=request_id,
        user_id=user.id,
        api_key_id=api_key.id,
        channel_id=channel.id if channel else None,
        model_id=model.model_id,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        cache_read_tokens=usage.cache_read_tokens,
        cache_write_tokens=usage.cache_write_tokens,
        reasoning_tokens=usage.reasoning_tokens,
        cost_micro_cents=cost_micro_cents,
        status=status,
        http_status=http_status,
        error_message=error_message,
        latency_ms=latency_ms,
        ttft_ms=ttft_ms,
        attempt_index=attempt_index,
        tried_channels=tried_channels,
        is_streaming=is_streaming,
        client_ip=client_ip,
    )
    db.add(log)
    await db.flush()

    if cost_micro_cents > 0:
        await db.refresh(user)
        actual = min(cost_micro_cents, user.balance_micro_cents)
        if actual > 0:
            user.balance_micro_cents -= actual
            db.add(BalanceTransaction(
                user_id=user.id,
                type="inference",
                amount_micro_cents=-actual,
                balance_after_micro_cents=user.balance_micro_cents,
                related_usage_log_id=log.id,
                description=f"{model.model_id} via channel {channel.id if channel else 'n/a'}",
            ))

    await db.commit()
    return log


def _estimate_prompt_tokens(body: dict[str, Any]) -> int:
    chars = 0
    if (s := body.get("system")):
        chars += len(s) if isinstance(s, str) else sum(len(str(b)) for b in s if isinstance(b, dict))
    for m in body.get("messages") or []:
        c = m.get("content")
        if isinstance(c, str):
            chars += len(c)
        elif isinstance(c, list):
            for block in c:
                if isinstance(block, dict):
                    chars += len(str(block.get("text", "") or block.get("source", "") or ""))
    if (tools := body.get("tools")):
        chars += sum(len(str(t)) for t in tools)
    return max(100, chars // 4)
