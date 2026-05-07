"""OpenAI /v1/chat/completions adapter.

Direct passthrough. We force `stream_options.include_usage=true` for streaming
requests so OpenAI returns a final usage chunk (which it omits by default).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import httpx

from app.providers._sse import iter_sse_data_jsons
from app.providers.base import Provider, register_provider
from app.schemas.common import Usage


@register_provider
class OpenAIProvider(Provider):
    name = "openai"

    async def chat_completions(
        self, body: dict[str, Any], *, stream: bool
    ) -> httpx.Response:
        body = {**body, "stream": stream}
        if stream:
            opts = dict(body.get("stream_options") or {})
            opts.setdefault("include_usage", True)
            body["stream_options"] = opts

        request = self.client.build_request(
            "POST",
            "/v1/chat/completions",
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
        """v0.2 B5: client speaks Anthropic but routes to OpenAI upstream."""
        from app.providers.translators.anth_to_oai import anth_request_to_oai

        oai_body = anth_request_to_oai(body)
        return await self.chat_completions(oai_body, stream=stream)

    # ---- Usage parsing ------------------------------------------------------

    def parse_usage_non_streaming(self, body: dict[str, Any]) -> Usage:
        u = body.get("usage") or {}
        prompt_details = u.get("prompt_tokens_details") or {}
        completion_details = u.get("completion_tokens_details") or {}

        cached = int(prompt_details.get("cached_tokens", 0) or 0)
        reasoning = int(completion_details.get("reasoning_tokens", 0) or 0)
        prompt_total = int(u.get("prompt_tokens", 0))
        completion_total = int(u.get("completion_tokens", 0))

        # OpenAI bills `cached_tokens` at half the input price.
        # In our schema, we treat the cached portion as cache_read_tokens
        # (so the prism `models` table's price_cache_read_per_million applies)
        # and the rest as plain prompt_tokens.
        prompt_tokens = max(0, prompt_total - cached)
        # completion_tokens already includes reasoning_tokens per OpenAI's spec.
        # We split them out: completion_tokens_visible = total - reasoning, then
        # reasoning_tokens billed separately at output rate.
        completion_visible = max(0, completion_total - reasoning)
        return Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_visible,
            cache_read_tokens=cached,
            reasoning_tokens=reasoning,
        )

    def extract_streaming_usage_events(self, chunk: bytes) -> Iterable[Usage]:
        for _, payload in iter_sse_data_jsons(chunk):
            if payload is None:
                continue
            usage_obj = payload.get("usage")
            if not usage_obj:
                continue
            # OpenAI emits the usage object **once** in the very last data event
            # (when stream_options.include_usage=true). Convert via the same
            # logic as non-streaming.
            yield self.parse_usage_non_streaming({"usage": usage_obj})
