"""POST /v1/chat/completions — OpenAI-compatible (also serves Gemini).

Uses app/routing/executor.py for retry + circuit breaker. v0.2 supports OpenAI +
Google via direct passthrough; Anthropic models on this endpoint will be enabled
in v0.2 B5 via protocol translator.
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
)
from app.deps import client_ip, get_db
from app.errors import PrismException, error_response
from app.limits import check_rpm_limit, default_rpm_for_user
from app.redis_client import get_redis
from app.routes.messages import record_request_outcome_v02
from app.routing import (
    AllChannelsFailed,
    attempts_to_json,
    execute_with_retry,
    find_model,
)
from app.schemas.common import StreamingState, Usage
from app.streaming import stream_with_usage

router = APIRouter(tags=["chat"])


@router.post("/v1/chat/completions")
async def post_chat_completions(
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

    # ---- 2. Model lookup ---------------------------------------------------
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

    if model.provider == "anthropic":
        return error_response(
            400,
            f"Anthropic model {model_id} should use /v1/messages until v0.2 B5 "
            "adds OAI↔Anthropic translation.",
            "invalid_request_error",
            param="model",
            code="provider_translation_not_yet_supported",
        )

    # ---- 3. Balance pre-flight --------------------------------------------
    estimated_input = _estimate_prompt_tokens(body)
    max_output = int(body.get("max_tokens") or body.get("max_completion_tokens") or 4096)
    estimated_max = estimate_max_cost_micro_cents(estimated_input, max_output, model)
    try:
        await check_balance_or_402(db, user, estimated_max)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    # ---- 4. Execute via retry chain ----------------------------------------
    is_streaming = bool(body.get("stream"))
    redis = get_redis()

    try:
        result = await execute_with_retry(
            model=model,
            request_body=body,
            is_streaming=is_streaming,
            db=db,
            redis_client=redis,
            method="chat_completions",
        )
    except AllChannelsFailed as exc:
        await record_request_outcome_v02(
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

    if upstream.status_code >= 400:
        try:
            return JSONResponse(
                status_code=upstream.status_code,
                content=result.response_body,
            )
        finally:
            await provider.aclose()
            latency_ms = int((time.monotonic() - started) * 1000)
            await record_request_outcome_v02(
                db, request_id=request_id, user=user, api_key=api_key,
                channel=channel, model=model, usage=Usage(),
                cost_micro_cents=0, status="error",
                http_status=upstream.status_code,
                error_message=str(result.response_body)[:1000],
                latency_ms=latency_ms,
                attempt_index=attempt_index,
                tried_channels=tried,
                is_streaming=is_streaming, client_ip=client_ip(request),
            )

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
            return JSONResponse(status_code=upstream.status_code, content=response_body)
        finally:
            await provider.aclose()

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

    return StreamingResponse(
        stream_with_usage(upstream, provider, on_complete),
        media_type="text/event-stream",
        headers={"x-prism-request-id": request_id},
    )


def _estimate_prompt_tokens(body: dict[str, Any]) -> int:
    chars = 0
    for m in body.get("messages") or []:
        c = m.get("content")
        if isinstance(c, str):
            chars += len(c)
        elif isinstance(c, list):
            for block in c:
                if isinstance(block, dict):
                    chars += len(str(block.get("text", "") or block))
    if (tools := body.get("tools")):
        chars += sum(len(str(t)) for t in tools)
    return max(100, chars // 4)
