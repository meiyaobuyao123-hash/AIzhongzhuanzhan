"""Anthropic /v1/messages adapter.

Direct passthrough — clients (Claude Code, anthropic-sdk-python) hit our
/v1/messages with Anthropic-format payloads, we forward to api.anthropic.com
unchanged save for swapping the API key.

Streaming: Anthropic emits SSE events including:
  - message_start  (carries usage.input_tokens + initial usage.output_tokens=N)
  - content_block_start / content_block_delta / content_block_stop
  - message_delta  (carries usage.output_tokens — final / cumulative)
  - message_stop

We accumulate usage from message_start (input side) and message_delta (output side).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import httpx

from app.providers._sse import iter_sse_data_jsons
from app.providers.base import Provider, register_provider
from app.schemas.common import Usage


@register_provider
class AnthropicProvider(Provider):
    name = "anthropic"
    api_version = "2023-06-01"

    async def messages(
        self, body: dict[str, Any], *, stream: bool
    ) -> httpx.Response:
        """Forward to upstream /v1/messages; caller is responsible for closing
        the response (or, in streaming mode, iterating it)."""
        body = {**body, "stream": stream}
        # Build request explicitly so we can return the underlying httpx.Response
        # for streaming consumption by the SSE pump in app/streaming/sse.py.
        request = self.client.build_request(
            "POST",
            "/v1/messages",
            headers={
                "x-api-key": self.upstream_key,
                "anthropic-version": self.api_version,
                "content-type": "application/json",
                "accept": "text/event-stream" if stream else "application/json",
            },
            json=body,
        )
        return await self.client.send(request, stream=stream)

    # ---- Usage parsing ------------------------------------------------------

    def parse_usage_non_streaming(self, body: dict[str, Any]) -> Usage:
        u = body.get("usage") or {}
        return Usage(
            prompt_tokens=int(u.get("input_tokens", 0)),
            completion_tokens=int(u.get("output_tokens", 0)),
            cache_read_tokens=int(u.get("cache_read_input_tokens", 0) or 0),
            cache_write_tokens=int(u.get("cache_creation_input_tokens", 0) or 0),
        )

    def extract_streaming_usage_events(self, chunk: bytes) -> Iterable[Usage]:
        for event_name, payload in iter_sse_data_jsons(chunk):
            if payload is None:
                continue
            event_type = event_name or payload.get("type")

            if event_type == "message_start":
                msg = payload.get("message") or {}
                u = msg.get("usage") or {}
                yield Usage(
                    prompt_tokens=int(u.get("input_tokens", 0)),
                    # output_tokens at start is 1-2 (priming); we'll overwrite from message_delta
                    completion_tokens=0,
                    cache_read_tokens=int(u.get("cache_read_input_tokens", 0) or 0),
                    cache_write_tokens=int(
                        u.get("cache_creation_input_tokens", 0) or 0
                    ),
                )
            elif event_type == "message_delta":
                # message_delta carries the *cumulative* output token count.
                # We replace (not add) by emitting a Usage with the new count.
                # The streaming pump's merge() preserves prompt/cache from earlier
                # message_start and uses the latest output_tokens via merge logic.
                # However our merge() adds completion_tokens — so we emit just the
                # delta from previously-known.
                u = payload.get("usage") or {}
                # Emit final value as if it were additive; pump should treat
                # 'message_delta' specially. To keep merge() additive-safe in v0.1,
                # we use a marker: we include the absolute value once at end of stream.
                yield Usage(
                    completion_tokens=int(u.get("output_tokens", 0)),
                )
