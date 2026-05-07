"""Translate Anthropic Messages ⇄ OpenAI Chat Completions.

Used when client speaks Anthropic (Claude Code, /v1/messages) but the upstream
is OpenAI/Google.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any


# ─── Request: Anthropic → OpenAI ─────────────────────────────────────────────


def anth_request_to_oai(anth_body: dict) -> dict:
    out: dict[str, Any] = {
        "model": anth_body["model"],
    }
    if "max_tokens" in anth_body:
        out["max_tokens"] = anth_body["max_tokens"]

    new_messages: list[dict] = []

    # system: Anth has top-level field; in OAI it's a system message
    sys = anth_body.get("system")
    if sys:
        if isinstance(sys, str):
            new_messages.append({"role": "system", "content": sys})
        elif isinstance(sys, list):
            text = "\n\n".join(b.get("text", "") for b in sys if isinstance(b, dict) and b.get("type") == "text")
            if text:
                new_messages.append({"role": "system", "content": text})

    # messages translation
    for msg in anth_body.get("messages") or []:
        role = msg.get("role")
        content = msg.get("content")

        if role == "user" and isinstance(content, list) and any(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in content
        ):
            # tool_result → emit `tool` role messages
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    new_messages.append({
                        "role": "tool",
                        "tool_call_id": b.get("tool_use_id", ""),
                        "content": _block_to_string(b.get("content", "")),
                    })
            continue

        if role == "assistant" and isinstance(content, list) and any(
            isinstance(b, dict) and b.get("type") == "tool_use" for b in content
        ):
            # tool_use → assistant message with tool_calls
            text_parts: list[str] = []
            tool_calls: list[dict] = []
            for b in content:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    text_parts.append(b.get("text", ""))
                elif b.get("type") == "tool_use":
                    tool_calls.append({
                        "id": b.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": b.get("name", ""),
                            "arguments": json.dumps(b.get("input") or {}),
                        },
                    })
            new_msg: dict[str, Any] = {
                "role": "assistant",
                "content": "".join(text_parts) if text_parts else None,
            }
            if tool_calls:
                new_msg["tool_calls"] = tool_calls
            new_messages.append(new_msg)
            continue

        # Plain message
        if isinstance(content, str):
            new_messages.append({"role": role, "content": content})
        elif isinstance(content, list):
            text = "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
            new_messages.append({"role": role, "content": text})

    out["messages"] = new_messages

    # tools translation (Anth flat → OAI nested function)
    if (anth_tools := anth_body.get("tools")):
        oai_tools: list[dict] = []
        for t in anth_tools:
            oai_tools.append({
                "type": "function",
                "function": {
                    "name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema") or {"type": "object", "properties": {}},
                },
            })
        out["tools"] = oai_tools

    if (tc := anth_body.get("tool_choice")):
        if isinstance(tc, dict):
            t = tc.get("type")
            if t == "auto":
                out["tool_choice"] = "auto"
            elif t == "any":
                out["tool_choice"] = "required"
            elif t == "tool":
                out["tool_choice"] = {
                    "type": "function",
                    "function": {"name": tc.get("name", "")},
                }

    for k in ("temperature", "top_p"):
        if k in anth_body:
            out[k] = anth_body[k]
    if (ss := anth_body.get("stop_sequences")):
        out["stop"] = ss

    return out


def _block_to_string(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    return str(content)


# ─── Response: OpenAI → Anthropic (non-streaming) ────────────────────────────


def oai_response_to_anth(oai_body: dict, *, requested_model: str) -> dict:
    choices = oai_body.get("choices") or []
    if not choices:
        return {
            "id": "msg_" + uuid.uuid4().hex[:24],
            "type": "message",
            "role": "assistant",
            "model": requested_model,
            "content": [],
            "stop_reason": "end_turn",
            "usage": _oai_usage_to_anth(oai_body.get("usage") or {}),
        }

    msg = choices[0].get("message") or {}
    content_blocks: list[dict] = []
    if msg.get("content"):
        content_blocks.append({"type": "text", "text": msg["content"]})
    if (tcs := msg.get("tool_calls")):
        for tc in tcs:
            fn = tc.get("function") or {}
            try:
                args = json.loads(fn.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}
            content_blocks.append({
                "type": "tool_use",
                "id": tc.get("id", ""),
                "name": fn.get("name", ""),
                "input": args,
            })

    finish = choices[0].get("finish_reason") or "stop"
    stop_reason = {
        "stop": "end_turn",
        "length": "max_tokens",
        "tool_calls": "tool_use",
        "content_filter": "end_turn",
    }.get(finish, "end_turn")

    return {
        "id": "msg_" + (oai_body.get("id") or uuid.uuid4().hex[:24])[:24],
        "type": "message",
        "role": "assistant",
        "model": requested_model,
        "content": content_blocks,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": _oai_usage_to_anth(oai_body.get("usage") or {}),
    }


def _oai_usage_to_anth(u: dict) -> dict:
    cached = (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0) or 0
    prompt_total = u.get("prompt_tokens", 0)
    return {
        "input_tokens": max(0, prompt_total - cached),
        "output_tokens": u.get("completion_tokens", 0),
        "cache_read_input_tokens": cached,
        "cache_creation_input_tokens": 0,
    }


# ─── Streaming: OpenAI SSE → Anthropic SSE ───────────────────────────────────


async def oai_stream_to_anth(
    upstream_aiter, *, requested_model: str
) -> AsyncIterator[bytes]:
    """OpenAI SSE → Anthropic SSE.

    Strategy: emit message_start, then content_block_start (text), then
    content_block_delta for each token, then content_block_stop, then
    message_delta (with usage), then message_stop.
    """
    msg_id = "msg_" + uuid.uuid4().hex[:24]
    final_usage: dict[str, int] = {"input_tokens": 0, "output_tokens": 0}
    stop_reason: str | None = None
    block_open = False
    buffer = b""

    def _event(name: str, payload: dict) -> bytes:
        return f"event: {name}\ndata: {json.dumps(payload)}\n\n".encode("utf-8")

    started = False
    async for chunk in upstream_aiter:
        buffer += chunk
        while b"\n\n" in buffer:
            block, buffer = buffer.split(b"\n\n", 1)
            for line in block.split(b"\n"):
                line = line.decode("utf-8", errors="replace").rstrip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    if block_open:
                        yield _event("content_block_stop", {"type": "content_block_stop", "index": 0})
                        block_open = False
                    yield _event("message_delta", {
                        "type": "message_delta",
                        "delta": {
                            "stop_reason": stop_reason or "end_turn",
                            "stop_sequence": None,
                        },
                        "usage": {"output_tokens": final_usage["output_tokens"]},
                    })
                    yield _event("message_stop", {"type": "message_stop"})
                    return
                try:
                    payload = json.loads(data)
                except json.JSONDecodeError:
                    continue

                # Capture usage if present (last chunk)
                if (u := payload.get("usage")):
                    final_usage["input_tokens"] = u.get("prompt_tokens", 0)
                    final_usage["output_tokens"] = u.get("completion_tokens", 0)

                choices = payload.get("choices") or []
                if not choices:
                    continue
                ch = choices[0]
                delta = ch.get("delta") or {}
                fr = ch.get("finish_reason")

                if not started:
                    started = True
                    yield _event("message_start", {
                        "type": "message_start",
                        "message": {
                            "id": msg_id, "type": "message", "role": "assistant",
                            "content": [], "model": requested_model,
                            "stop_reason": None, "stop_sequence": None,
                            "usage": {"input_tokens": final_usage["input_tokens"], "output_tokens": 0},
                        },
                    })

                if delta.get("content") and not block_open:
                    yield _event("content_block_start", {
                        "type": "content_block_start", "index": 0,
                        "content_block": {"type": "text", "text": ""},
                    })
                    block_open = True

                if (txt := delta.get("content")):
                    yield _event("content_block_delta", {
                        "type": "content_block_delta", "index": 0,
                        "delta": {"type": "text_delta", "text": txt},
                    })

                if fr:
                    stop_reason = {
                        "stop": "end_turn",
                        "length": "max_tokens",
                        "tool_calls": "tool_use",
                    }.get(fr, "end_turn")
