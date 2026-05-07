"""Translate OpenAI Chat Completions ⇄ Anthropic Messages.

Used when:
  AnthropicProvider.chat_completions: client speaks OAI but we have an Anthropic
    upstream. We OAI→Anth before forwarding, Anth→OAI on response.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any


# ─── Request: OpenAI → Anthropic ─────────────────────────────────────────────


def oai_request_to_anth(oai_body: dict) -> dict:
    """Convert OpenAI /v1/chat/completions body → Anthropic /v1/messages body."""
    out: dict[str, Any] = {
        "model": oai_body["model"],
    }

    # max_tokens: OpenAI optional default, Anthropic required
    out["max_tokens"] = oai_body.get("max_tokens") or oai_body.get("max_completion_tokens") or 4096

    # messages: split out system, transform tool_calls/results
    system_parts: list[str] = []
    new_messages: list[dict] = []
    for msg in oai_body.get("messages") or []:
        role = msg.get("role")
        if role == "system":
            content = msg.get("content")
            if isinstance(content, str):
                system_parts.append(content)
            elif isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "text":
                        system_parts.append(b.get("text", ""))
            continue

        if role == "tool":
            # OAI: {"role":"tool", "tool_call_id":"call_xxx", "content":"..."}
            # Anth: {"role":"user", "content":[{"type":"tool_result","tool_use_id":"call_xxx","content":"..."}]}
            new_messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": msg.get("tool_call_id", ""),
                    "content": _str_content(msg.get("content", "")),
                }],
            })
            continue

        if role == "assistant" and msg.get("tool_calls"):
            # OAI: {"role":"assistant", "content": "...", "tool_calls":[{...}]}
            # Anth: {"role":"assistant", "content":[{"type":"text",...}, {"type":"tool_use",...}]}
            blocks: list[dict] = []
            txt = msg.get("content")
            if txt:
                blocks.append({"type": "text", "text": _str_content(txt)})
            for tc in msg["tool_calls"]:
                fn = tc.get("function") or {}
                try:
                    args = json.loads(fn.get("arguments", "{}")) if isinstance(fn.get("arguments"), str) else fn.get("arguments", {})
                except json.JSONDecodeError:
                    args = {}
                blocks.append({
                    "type": "tool_use",
                    "id": tc.get("id", ""),
                    "name": fn.get("name", ""),
                    "input": args,
                })
            new_messages.append({"role": "assistant", "content": blocks})
            continue

        # Default: copy role + content
        new_messages.append({"role": role, "content": _content_to_anth(msg.get("content"))})

    if system_parts:
        out["system"] = "\n\n".join(system_parts)
    out["messages"] = new_messages

    # tools: OAI has nested function shape, Anthropic is flat
    if (oai_tools := oai_body.get("tools")):
        anth_tools: list[dict] = []
        for t in oai_tools:
            if t.get("type") != "function":
                continue
            fn = t.get("function") or {}
            anth_tools.append({
                "name": fn.get("name", ""),
                "description": fn.get("description", ""),
                "input_schema": fn.get("parameters") or {"type": "object", "properties": {}},
            })
        if anth_tools:
            out["tools"] = anth_tools

    if (tc := oai_body.get("tool_choice")):
        if tc == "auto":
            out["tool_choice"] = {"type": "auto"}
        elif tc == "none":
            pass  # Anthropic default: no tool use
        elif tc == "required":
            out["tool_choice"] = {"type": "any"}
        elif isinstance(tc, dict) and tc.get("type") == "function":
            out["tool_choice"] = {
                "type": "tool",
                "name": tc.get("function", {}).get("name", ""),
            }

    # Pass-through scalars
    for k in ("temperature", "top_p", "stop"):
        if k in oai_body:
            if k == "stop":
                out["stop_sequences"] = oai_body["stop"] if isinstance(oai_body["stop"], list) else [oai_body["stop"]]
            else:
                out[k] = oai_body[k]

    return out


def _content_to_anth(content) -> Any:
    """Convert OAI message content (string or list of blocks) to Anthropic shape."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out_blocks: list[dict] = []
        for b in content:
            if isinstance(b, dict):
                if b.get("type") == "text":
                    out_blocks.append({"type": "text", "text": b.get("text", "")})
                # image/audio blocks would translate here in v0.3
        return out_blocks if out_blocks else ""
    return content


def _str_content(c) -> str:
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "".join(b.get("text", "") for b in c if isinstance(b, dict))
    return str(c)


# ─── Response: Anthropic → OpenAI (non-streaming) ────────────────────────────


def anth_response_to_oai(anth_body: dict, *, requested_model: str) -> dict:
    """Anthropic Messages response → OpenAI Chat Completion response."""
    content_blocks = anth_body.get("content") or []
    text_parts: list[str] = []
    tool_calls: list[dict] = []
    for b in content_blocks:
        if isinstance(b, dict):
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

    message: dict = {
        "role": "assistant",
        "content": "".join(text_parts) if text_parts else None,
    }
    if tool_calls:
        message["tool_calls"] = tool_calls

    finish_reason = _stop_reason_to_finish(anth_body.get("stop_reason"))

    usage_anth = anth_body.get("usage") or {}
    prompt_tokens = int(usage_anth.get("input_tokens", 0))
    completion_tokens = int(usage_anth.get("output_tokens", 0))

    return {
        "id": "chatcmpl-" + (anth_body.get("id") or uuid.uuid4().hex)[:24],
        "object": "chat.completion",
        "created": int(time.time()),
        "model": requested_model,
        "choices": [{
            "index": 0,
            "message": message,
            "finish_reason": finish_reason,
        }],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def _stop_reason_to_finish(anth_stop: str | None) -> str:
    return {
        "end_turn": "stop",
        "max_tokens": "length",
        "stop_sequence": "stop",
        "tool_use": "tool_calls",
    }.get(anth_stop or "", "stop")


# ─── Streaming: Anthropic SSE → OpenAI SSE ───────────────────────────────────


async def anth_stream_to_oai(
    upstream_aiter, *, requested_model: str
) -> AsyncIterator[bytes]:
    """Translate Anthropic SSE to OpenAI SSE chunks.

    Anthropic events:
      message_start, content_block_start, content_block_delta (text_delta),
      content_block_stop, message_delta (usage), message_stop
    OpenAI chunks:
      data: {"choices":[{"delta":{"role":"assistant"}}]}
      data: {"choices":[{"delta":{"content":"hi"}}]}
      data: {"choices":[{"delta":{},"finish_reason":"stop"}],
             "usage":{"prompt_tokens":...,"completion_tokens":...}}
      data: [DONE]
    """
    chatcmpl_id = "chatcmpl-" + uuid.uuid4().hex[:24]
    created = int(time.time())

    sent_role = False
    final_usage: dict = {"prompt_tokens": 0, "completion_tokens": 0}
    finish_reason = "stop"
    buffer = b""

    def _wrap(delta: dict, *, finish: str | None = None, usage: dict | None = None) -> bytes:
        chunk = {
            "id": chatcmpl_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": requested_model,
            "choices": [{
                "index": 0,
                "delta": delta,
                "finish_reason": finish,
            }],
        }
        if usage is not None:
            chunk["usage"] = usage
        return f"data: {json.dumps(chunk)}\n\n".encode("utf-8")

    async for chunk in upstream_aiter:
        buffer += chunk
        # Process complete events (split on \n\n)
        while b"\n\n" in buffer:
            event_block, buffer = buffer.split(b"\n\n", 1)
            event_lines = event_block.split(b"\n")
            event_name: str | None = None
            data: str | None = None
            for ln in event_lines:
                ln = ln.decode("utf-8", errors="replace").rstrip()
                if ln.startswith("event:"):
                    event_name = ln[6:].strip()
                elif ln.startswith("data:"):
                    data = ln[5:].strip()
            if not data:
                continue
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue

            event_type = event_name or payload.get("type")

            if event_type == "message_start":
                msg = payload.get("message") or {}
                u = msg.get("usage") or {}
                final_usage["prompt_tokens"] = int(u.get("input_tokens", 0))
                if not sent_role:
                    yield _wrap({"role": "assistant", "content": ""})
                    sent_role = True

            elif event_type == "content_block_delta":
                delta = payload.get("delta") or {}
                if delta.get("type") == "text_delta":
                    yield _wrap({"content": delta.get("text", "")})
                # tool_use_delta: harder; skip in v0.2 streaming

            elif event_type == "message_delta":
                delta = payload.get("delta") or {}
                if delta.get("stop_reason"):
                    finish_reason = _stop_reason_to_finish(delta["stop_reason"])
                u = payload.get("usage") or {}
                if u.get("output_tokens") is not None:
                    final_usage["completion_tokens"] = int(u["output_tokens"])

            elif event_type == "message_stop":
                # Final chunk with usage + finish_reason
                final_usage["total_tokens"] = (
                    final_usage["prompt_tokens"] + final_usage["completion_tokens"]
                )
                yield _wrap({}, finish=finish_reason, usage=final_usage)
                yield b"data: [DONE]\n\n"
                return
