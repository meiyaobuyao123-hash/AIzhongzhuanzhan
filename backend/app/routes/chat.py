"""POST /v1/chat/completions — OpenAI-compatible (also accepts Gemini models).

Same pipeline as /v1/messages but for the OpenAI dialect. Routes to either the
OpenAIProvider or GoogleProvider based on the resolved model's `provider` field.

For Anthropic models: v0.1 returns 400 "use /v1/messages instead". v0.2 will
add OpenAI↔Anthropic protocol translation.
"""

from __future__ import annotations

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
from app.config import settings
from app.deps import client_ip, get_db
from app.errors import PrismException, error_response
from app.providers import make_provider
from app.routing import find_model, route
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

    # ---- 1. Auth ------------------------------------------------------------
    try:
        raw_key = parse_authorization(authorization, x_api_key)
        user, api_key = await authenticate(raw_key, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    # ---- 2. Model + channel -------------------------------------------------
    try:
        model_id = body.get("model")
        if not model_id:
            return error_response(400, "Missing 'model' field", "invalid_request_error", param="model")

        if api_key.whitelist_list is not None and model_id not in api_key.whitelist_list:
            return error_response(
                403,
                f"Model {model_id} not allowed for this API key",
                "permission_error",
                code="model_not_in_whitelist",
            )

        model = await find_model(model_id, db)
        if model.provider == "anthropic":
            return error_response(
                400,
                f"Anthropic model {model_id} should use /v1/messages, not /v1/chat/completions. "
                "(OpenAI↔Anthropic protocol translation lands in v0.2.)",
                "invalid_request_error",
                param="model",
            )
        channel = await route(model, db)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    # ---- 3. Balance pre-flight ---------------------------------------------
    estimated_input = _estimate_prompt_tokens(body)
    max_output = int(body.get("max_tokens") or body.get("max_completion_tokens") or 4096)
    estimated_max = estimate_max_cost_micro_cents(estimated_input, max_output, model)
    try:
        await check_balance_or_402(db, user, estimated_max)
    except PrismException as exc:
        return error_response(exc.status_code, exc.message, exc.error_type, exc.code)

    # ---- 4. Forward --------------------------------------------------------
    is_streaming = bool(body.get("stream"))
    provider = make_provider(channel, settings.master_key)

    try:
        upstream = await provider.chat_completions(body, stream=is_streaming)
    except Exception as exc:
        await provider.aclose()
        await record_request_outcome(
            db, request_id=request_id, user=user, api_key=api_key, channel=channel,
            model=model, usage=Usage(), cost_micro_cents=0, status="error",
            error_message=f"Upstream connect failure: {type(exc).__name__}: {exc}",
            is_streaming=is_streaming, client_ip=client_ip(request),
        )
        return error_response(
            502, "Upstream connection failed", "api_error", code="upstream_unreachable"
        )

    if upstream.status_code >= 400:
        await upstream.aread()
        try:
            upstream_body = upstream.json()
        except Exception:
            upstream_body = {"error": {"message": upstream.text}}
        await provider.aclose()
        await record_request_outcome(
            db, request_id=request_id, user=user, api_key=api_key, channel=channel,
            model=model, usage=Usage(), cost_micro_cents=0, status="error",
            http_status=upstream.status_code,
            error_message=str(upstream_body)[:1000],
            is_streaming=is_streaming, client_ip=client_ip(request),
        )
        return JSONResponse(status_code=upstream.status_code, content=upstream_body)

    # ---- 5a. Non-streaming -------------------------------------------------
    if not is_streaming:
        try:
            await upstream.aread()
            response_body = upstream.json()
            usage = provider.parse_usage_non_streaming(response_body)
            cost = calculate_cost_micro_cents(usage, model)
            await record_request_outcome(
                db, request_id=request_id, user=user, api_key=api_key,
                channel=channel, model=model, usage=usage,
                cost_micro_cents=cost, status="ok",
                http_status=upstream.status_code,
                is_streaming=False, client_ip=client_ip(request),
            )
            return JSONResponse(status_code=upstream.status_code, content=response_body)
        finally:
            await provider.aclose()

    # ---- 5b. Streaming ------------------------------------------------------
    async def on_complete(state: StreamingState) -> None:
        usage = state.usage
        cost = calculate_cost_micro_cents(usage, model)
        await record_request_outcome(
            db, request_id=request_id, user=user, api_key=api_key, channel=channel,
            model=model, usage=usage, cost_micro_cents=cost,
            status="ok" if state.stats.finished_normally else "partial",
            http_status=state.stats.upstream_status,
            stats=state.stats, is_streaming=True, client_ip=client_ip(request),
        )
        await provider.aclose()

    return StreamingResponse(
        stream_with_usage(upstream, provider, on_complete),
        media_type="text/event-stream",
        headers={"x-prism-request-id": request_id},
    )


def _estimate_prompt_tokens(body: dict[str, Any]) -> int:
    """OpenAI: messages = list[{role, content: str | list[{text|...}]}]."""
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
