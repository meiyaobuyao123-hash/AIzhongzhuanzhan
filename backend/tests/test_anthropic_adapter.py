"""Anthropic adapter: usage parsing + factory wiring."""

from __future__ import annotations

import json

import pytest
import respx
from httpx import Response

from app.crypto import encrypt
from app.models.orm import Channel
from app.providers import make_provider
from app.providers.anthropic import AnthropicProvider
from app.schemas.common import Usage


def make_channel(master_key: bytes) -> Channel:
    return Channel(
        id=1,
        name="test",
        provider="anthropic",
        base_url="https://api.anthropic.com",
        upstream_key_encrypted=encrypt("sk-ant-test-key", master_key),
        models=json.dumps(["claude-opus-4-5"]),
        channel_group="default",
        priority=100,
        weight=100,
        enabled=True,
    )


# ---- usage parsing ----------------------------------------------------------


def test_parse_usage_non_streaming_basic():
    p = AnthropicProvider.__new__(AnthropicProvider)  # type: ignore[call-arg]
    body = {
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50,
        }
    }
    u = p.parse_usage_non_streaming(body)
    assert u.prompt_tokens == 100
    assert u.completion_tokens == 50
    assert u.cache_read_tokens == 0
    assert u.cache_write_tokens == 0


def test_parse_usage_non_streaming_with_cache():
    p = AnthropicProvider.__new__(AnthropicProvider)  # type: ignore[call-arg]
    body = {
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_read_input_tokens": 80,
            "cache_creation_input_tokens": 20,
        }
    }
    u = p.parse_usage_non_streaming(body)
    assert u.prompt_tokens == 100
    assert u.completion_tokens == 50
    assert u.cache_read_tokens == 80
    assert u.cache_write_tokens == 20


def test_streaming_usage_events_assembly():
    """Anthropic SSE streaming: message_start + message_delta carries usage."""
    p = AnthropicProvider.__new__(AnthropicProvider)  # type: ignore[call-arg]

    msg_start = (
        b"event: message_start\n"
        b'data: {"type":"message_start","message":{"id":"msg_x","type":"message",'
        b'"role":"assistant","content":[],"model":"claude-opus-4-5",'
        b'"usage":{"input_tokens":42,"output_tokens":1,'
        b'"cache_read_input_tokens":10,"cache_creation_input_tokens":5}}}\n\n'
    )
    msg_delta = (
        b"event: message_delta\n"
        b'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"},'
        b'"usage":{"output_tokens":123}}\n\n'
    )

    starts = list(p.extract_streaming_usage_events(msg_start))
    deltas = list(p.extract_streaming_usage_events(msg_delta))

    assert len(starts) == 1
    assert starts[0].prompt_tokens == 42
    assert starts[0].cache_read_tokens == 10
    assert starts[0].cache_write_tokens == 5

    assert len(deltas) == 1
    assert deltas[0].completion_tokens == 123


# ---- factory + decryption ---------------------------------------------------


def test_factory_decrypts_upstream_key():
    master_key = b"X" * 32
    ch = make_channel(master_key)
    p = make_provider(ch, master_key)
    assert isinstance(p, AnthropicProvider)
    assert p.upstream_key == "sk-ant-test-key"


# ---- HTTP forwarding (mocked upstream) -------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_messages_forwards_to_anthropic():
    master_key = b"X" * 32
    ch = make_channel(master_key)

    expected_response = {
        "id": "msg_test",
        "model": "claude-opus-4-5",
        "content": [{"type": "text", "text": "hi"}],
        "usage": {"input_tokens": 5, "output_tokens": 2},
    }
    route = respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=Response(200, json=expected_response)
    )

    p = make_provider(ch, master_key)
    try:
        resp = await p.messages({"model": "claude-opus-4-5", "messages": []}, stream=False)
        assert resp.status_code == 200
        body = resp.json()
        assert body == expected_response
    finally:
        await p.aclose()

    assert route.called
    sent = route.calls[0].request
    # Verify our headers
    assert sent.headers["x-api-key"] == "sk-ant-test-key"
    assert sent.headers["anthropic-version"] == "2023-06-01"
    sent_body = json.loads(sent.content)
    assert sent_body["stream"] is False


@pytest.mark.asyncio
@respx.mock
async def test_messages_forwards_streaming_with_correct_accept_header():
    master_key = b"X" * 32
    ch = make_channel(master_key)

    sse_body = (
        b"event: message_start\n"
        b'data: {"type":"message_start","message":{"usage":{"input_tokens":1,"output_tokens":1}}}\n\n'
        b"event: message_stop\ndata: {}\n\n"
    )
    route = respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=Response(200, content=sse_body, headers={"content-type": "text/event-stream"})
    )

    p = make_provider(ch, master_key)
    try:
        resp = await p.messages(
            {"model": "claude-opus-4-5", "messages": []}, stream=True
        )
        assert resp.status_code == 200
        # Read streaming bytes
        content = b""
        async for chunk in resp.aiter_bytes():
            content += chunk
        assert b"message_start" in content
    finally:
        await p.aclose()

    sent = route.calls[0].request
    assert sent.headers["accept"] == "text/event-stream"
