"""Google Gemini adapter via the OpenAI-compatible endpoint.

Google AI Studio exposes:
    https://generativelanguage.googleapis.com/v1beta/openai/chat/completions

This is an OpenAI-style endpoint that accepts standard OpenAI request bodies
and returns OpenAI-style responses. The differences vs OpenAI proper:
  - `Authorization: Bearer {GEMINI_API_KEY}` (the AI Studio key)
  - Some response fields are minor variations (usage works the same)
  - `model` strings: gemini-3-pro / gemini-3-flash etc.

For streaming usage, Google also supports stream_options.include_usage,
so the OpenAI handler logic carries over directly.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import httpx

from app.providers._sse import iter_sse_data_jsons
from app.providers.base import Provider, register_provider
from app.providers.openai import OpenAIProvider
from app.schemas.common import Usage


@register_provider
class GoogleProvider(Provider):
    """Gemini via Google's OpenAI-compat shim."""

    name = "google"

    async def chat_completions(
        self, body: dict[str, Any], *, stream: bool
    ) -> httpx.Response:
        body = {**body, "stream": stream}
        if stream:
            opts = dict(body.get("stream_options") or {})
            opts.setdefault("include_usage", True)
            body["stream_options"] = opts

        # Note: Google's compat endpoint sits at /v1beta/openai/chat/completions
        # Channel.base_url should already include /v1beta/openai — the path here
        # is just /chat/completions. We support both: if base_url ends with
        # /openai, we use the relative path; otherwise we stick the full path.
        base_url = str(self.client.base_url).rstrip("/")
        if base_url.endswith("/openai"):
            path = "/chat/completions"
        else:
            path = "/v1beta/openai/chat/completions"

        request = self.client.build_request(
            "POST",
            path,
            headers={
                "Authorization": f"Bearer {self.upstream_key}",
                "content-type": "application/json",
                "accept": "text/event-stream" if stream else "application/json",
            },
            json=body,
        )
        return await self.client.send(request, stream=stream)

    async def messages(
        self, body: dict[str, Any], *, stream: bool
    ) -> httpx.Response:
        """v0.2 B5: client speaks Anthropic but routes to Google (Gemini)."""
        from app.providers.translators.anth_to_oai import anth_request_to_oai

        oai_body = anth_request_to_oai(body)
        return await self.chat_completions(oai_body, stream=stream)

    # ---- Usage parsing (delegate to OpenAI logic; identical fields) ---------

    def parse_usage_non_streaming(self, body: dict[str, Any]) -> Usage:
        # Reuse OpenAI's parser by static call (no instance needed)
        return OpenAIProvider.parse_usage_non_streaming(self, body)  # type: ignore[arg-type]

    def extract_streaming_usage_events(self, chunk: bytes) -> Iterable[Usage]:
        for _, payload in iter_sse_data_jsons(chunk):
            if payload is None:
                continue
            usage_obj = payload.get("usage")
            if not usage_obj:
                continue
            yield self.parse_usage_non_streaming({"usage": usage_obj})
