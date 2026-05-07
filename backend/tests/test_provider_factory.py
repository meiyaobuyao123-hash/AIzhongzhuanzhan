"""Provider factory + registration."""

from __future__ import annotations

import json

import pytest

from app.crypto import encrypt
from app.models.orm import Channel
from app.providers import list_providers, make_provider
from app.providers.anthropic import AnthropicProvider
from app.providers.google import GoogleProvider
from app.providers.openai import OpenAIProvider


def test_three_providers_registered():
    names = list_providers()
    assert "anthropic" in names
    assert "openai" in names
    assert "google" in names


def test_factory_returns_correct_class():
    master_key = b"K" * 32

    def ch(provider: str, base_url: str) -> Channel:
        return Channel(
            id=1, name="t", provider=provider, base_url=base_url,
            upstream_key_encrypted=encrypt("sk-test", master_key),
            models=json.dumps(["m"]), channel_group="default",
            priority=100, weight=100, enabled=True,
        )

    assert isinstance(make_provider(ch("anthropic", "https://x"), master_key), AnthropicProvider)
    assert isinstance(make_provider(ch("openai", "https://x"), master_key), OpenAIProvider)
    assert isinstance(make_provider(ch("google", "https://x"), master_key), GoogleProvider)


def test_factory_unknown_provider_raises():
    master_key = b"K" * 32
    with pytest.raises(ValueError, match="Unknown provider"):
        ch = Channel(
            id=1, name="t", provider="not_real", base_url="https://x",
            upstream_key_encrypted=encrypt("sk", master_key),
            models=json.dumps([]), channel_group="default",
            priority=100, weight=100, enabled=True,
        )
        make_provider(ch, master_key)
