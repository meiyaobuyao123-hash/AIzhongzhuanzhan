"""Provider abstraction.

A `Provider` knows how to:
  1. Forward a normalized request to an upstream channel (Anthropic / OpenAI / etc.)
  2. Parse the upstream's `usage` field into our normalized `Usage` shape
  3. (For streaming) extract usage events from each SSE chunk

The actual SSE pump (orchestrating client ↔ provider) lives in app/streaming/sse.py;
this module just defines the per-provider shape.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any, ClassVar

import httpx

from app.crypto import decrypt
from app.models.orm import Channel
from app.schemas.common import Usage


class Provider(ABC):
    """Abstract base for upstream provider adapters."""

    name: ClassVar[str]
    """Provider key matching channels.provider, e.g. 'anthropic'."""

    def __init__(
        self,
        channel: Channel,
        master_key: bytes,
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = 600.0,
    ) -> None:
        self.channel = channel
        self.upstream_key = decrypt(channel.upstream_key_encrypted, master_key)
        if client is None:
            client = httpx.AsyncClient(
                base_url=channel.base_url,
                timeout=httpx.Timeout(timeout, connect=10.0),
            )
        self.client = client

    async def aclose(self) -> None:
        await self.client.aclose()

    # ---- Capability methods. Subclasses implement what they support ---------

    async def messages(
        self, body: dict[str, Any], *, stream: bool
    ) -> httpx.Response:
        """Anthropic-native /v1/messages call. Default: not implemented."""
        raise NotImplementedError(f"{self.name} provider does not support /v1/messages")

    async def chat_completions(
        self, body: dict[str, Any], *, stream: bool
    ) -> httpx.Response:
        """OpenAI-compatible /v1/chat/completions call. Default: not implemented."""
        raise NotImplementedError(
            f"{self.name} provider does not support /v1/chat/completions"
        )

    # ---- Usage extraction ---------------------------------------------------

    @abstractmethod
    def parse_usage_non_streaming(self, body: dict[str, Any]) -> Usage:
        """Extract Usage from a non-streaming JSON response body."""

    @abstractmethod
    def extract_streaming_usage_events(
        self, sse_chunk: bytes
    ) -> Iterable[Usage]:
        """Yield Usage updates parsed from an SSE chunk (or empty if none).

        Called for every chunk the streaming pump receives. Implementations should
        be defensive: SSE messages may span chunk boundaries, so partial JSON
        should be tolerated. v0.1: simplified — assume each SSE event arrives
        fully formed in one chunk (which httpx + Anthropic/OpenAI respect in
        practice).
        """


# =============================================================================
# Factory
# =============================================================================


_PROVIDER_REGISTRY: dict[str, type[Provider]] = {}


def register_provider(cls: type[Provider]) -> type[Provider]:
    """Decorator: register a Provider subclass by its `name`."""
    _PROVIDER_REGISTRY[cls.name] = cls
    return cls


def make_provider(channel: Channel, master_key: bytes, **kwargs) -> Provider:
    """Instantiate the right Provider subclass for a channel."""
    if channel.provider not in _PROVIDER_REGISTRY:
        raise ValueError(f"Unknown provider: {channel.provider}")
    return _PROVIDER_REGISTRY[channel.provider](channel, master_key, **kwargs)


def list_providers() -> list[str]:
    return sorted(_PROVIDER_REGISTRY)
