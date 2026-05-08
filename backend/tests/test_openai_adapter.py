"""OpenAI adapter tests."""

from __future__ import annotations

import json

import pytest
import respx
from httpx import Response

from app.crypto import encrypt
from app.models.orm import Channel
from app.providers import make_provider
from app.providers.openai import OpenAIProvider


def make_channel(master_key: bytes) -> Channel:
    return Channel(
        id=2,
        name="test-openai",
        provider="openai",
        base_url="https://api.openai.com",
        upstream_key_encrypted=encrypt("sk-openai-test-key", master_key),
        models=json.dumps(["gpt-5"]),
        channel_group="default",
        priority=100,
        weight=100,
        enabled=True,
    )


def test_parse_usage_non_streaming_basic():
    p = OpenAIProvider.__new__(OpenAIProvider)  # type: ignore[call-arg]
    body = {
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
    }
    u = p.parse_usage_non_streaming(body)
    assert u.prompt_tokens == 100
    assert u.completion_tokens == 50
    assert u.cache_read_tokens == 0
    assert u.reasoning_tokens == 0


def test_parse_usage_with_cached_tokens():
    """OpenAI's cached_tokens is part of prompt_tokens; we split it out."""
    p = OpenAIProvider.__new__(OpenAIProvider)  # type: ignore[call-arg]
    body = {
        "usage": {
            "prompt_tokens": 1000,
            "completion_tokens": 50,
            "prompt_tokens_details": {"cached_tokens": 800},
        }
    }
    u = p.parse_usage_non_streaming(body)
    # prompt_tokens (uncached) = 1000 - 800 = 200
    assert u.prompt_tokens == 200
    assert u.cache_read_tokens == 800
    assert u.completion_tokens == 50


def test_parse_usage_with_reasoning_tokens():
    """OpenAI o-series: reasoning_tokens is part of completion_tokens; split out."""
    p = OpenAIProvider.__new__(OpenAIProvider)  # type: ignore[call-arg]
    body = {
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 1000,  # includes 800 reasoning
            "completion_tokens_details": {"reasoning_tokens": 800},
        }
    }
    u = p.parse_usage_non_streaming(body)
    assert u.prompt_tokens == 100
    assert u.completion_tokens == 200  # 1000 - 800
    assert u.reasoning_tokens == 800


@pytest.mark.asyncio
@respx.mock
async def test_chat_completions_forces_include_usage_when_streaming():
    master_key = b"Y" * 32
    ch = make_channel(master_key)

    route = respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=Response(200, content=b'data: [DONE]\n\n', headers={"content-type": "text/event-stream"})
    )

    p = make_provider(ch, master_key)
    try:
        await p.chat_completions(
            {"model": "gpt-5", "messages": [{"role": "user", "content": "hi"}]},
            stream=True,
        )
    finally:
        await p.aclose()

    sent = route.calls[0].request
    body = json.loads(sent.content)
    assert body["stream"] is True
    assert body["stream_options"]["include_usage"] is True
    assert sent.headers["authorization"] == "Bearer sk-openai-test-key"


@pytest.mark.asyncio
@respx.mock
async def test_chat_completions_non_streaming_no_stream_options():
    master_key = b"Y" * 32
    ch = make_channel(master_key)

    route = respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=Response(200, json={"choices": [], "usage": {"prompt_tokens": 1, "completion_tokens": 1}})
    )

    p = make_provider(ch, master_key)
    try:
        await p.chat_completions({"model": "gpt-5", "messages": []}, stream=False)
    finally:
        await p.aclose()

    body = json.loads(route.calls[0].request.content)
    assert body["stream"] is False
    assert "stream_options" not in body


def test_streaming_usage_extracted_from_final_chunk():
    """OpenAI emits usage in the LAST data chunk (when include_usage=true)."""
    p = OpenAIProvider.__new__(OpenAIProvider)  # type: ignore[call-arg]

    final_chunk = (
        b'data: {"choices":[],"usage":{"prompt_tokens":42,"completion_tokens":17,"total_tokens":59}}\n\n'
        b"data: [DONE]\n\n"
    )
    events = list(p.extract_streaming_usage_events(final_chunk))
    assert len(events) == 1
    assert events[0].prompt_tokens == 42
    assert events[0].completion_tokens == 17


def test_streaming_no_usage_in_intermediate_chunks():
    p = OpenAIProvider.__new__(OpenAIProvider)  # type: ignore[call-arg]
    intermediate = (
        b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\n'
    )
    events = list(p.extract_streaming_usage_events(intermediate))
    assert events == []


def test_chat_completions_path_detection():
    """v0.3 fix: derive correct chat-completions path from base_url
    so non-standard upstreams (Doubao /api/v3, ...) work without hardcoded /v1."""
    from app.providers.openai import chat_completions_path

    # Vanilla / DeepSeek / Anthropic-OAI-compat — default /v1/chat/completions
    assert chat_completions_path("https://api.openai.com") == "/v1/chat/completions"
    assert chat_completions_path("https://api.openai.com/") == "/v1/chat/completions"
    assert chat_completions_path("https://api.deepseek.com") == "/v1/chat/completions"
    assert chat_completions_path("https://api.minimaxi.com") == "/v1/chat/completions"

    # Already has /v1 in path → just /chat/completions
    assert chat_completions_path("https://api.openai.com/v1") == "/chat/completions"
    assert chat_completions_path("https://api.minimaxi.com/v1") == "/chat/completions"

    # Volcengine Doubao /api/v3
    assert chat_completions_path(
        "https://ark.cn-beijing.volces.com/api/v3"
    ) == "/chat/completions"

    # Trailing slash variants
    assert chat_completions_path(
        "https://ark.cn-beijing.volces.com/api/v3/"
    ) == "/chat/completions"
