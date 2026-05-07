"""Google Gemini adapter (via OpenAI-compat endpoint) tests."""

from __future__ import annotations

import json

import pytest
import respx
from httpx import Response

from app.crypto import encrypt
from app.models.orm import Channel
from app.providers import make_provider
from app.providers.google import GoogleProvider


def make_channel(master_key: bytes, base_url: str) -> Channel:
    return Channel(
        id=3,
        name="test-google",
        provider="google",
        base_url=base_url,
        upstream_key_encrypted=encrypt("AIza-google-test-key", master_key),
        models=json.dumps(["gemini-3-pro"]),
        channel_group="default",
        priority=100,
        weight=100,
        enabled=True,
    )


def test_parse_usage_same_shape_as_openai():
    p = GoogleProvider.__new__(GoogleProvider)  # type: ignore[call-arg]
    body = {
        "usage": {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75}
    }
    u = p.parse_usage_non_streaming(body)
    assert u.prompt_tokens == 50
    assert u.completion_tokens == 25


@pytest.mark.asyncio
@respx.mock
async def test_chat_completions_uses_openai_compat_path_when_base_includes_openai():
    master_key = b"Z" * 32
    ch = make_channel(
        master_key, "https://generativelanguage.googleapis.com/v1beta/openai"
    )

    route = respx.post(
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    ).mock(return_value=Response(200, json={"choices": []}))

    p = make_provider(ch, master_key)
    try:
        await p.chat_completions({"model": "gemini-3-pro", "messages": []}, stream=False)
    finally:
        await p.aclose()

    assert route.called
    assert route.calls[0].request.headers["authorization"] == "Bearer AIza-google-test-key"


@pytest.mark.asyncio
@respx.mock
async def test_chat_completions_constructs_full_path_when_base_is_root():
    master_key = b"Z" * 32
    ch = make_channel(master_key, "https://generativelanguage.googleapis.com")

    route = respx.post(
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    ).mock(return_value=Response(200, json={"choices": []}))

    p = make_provider(ch, master_key)
    try:
        await p.chat_completions(
            {"model": "gemini-3-pro", "messages": []}, stream=True
        )
    finally:
        await p.aclose()

    assert route.called
