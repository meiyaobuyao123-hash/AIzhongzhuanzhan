"""SSE streaming pump.

Three responsibilities, executed concurrently per-chunk:
  1. Forward each upstream chunk to the client unchanged
  2. Parse usage from each chunk via the Provider
  3. Track timing (first byte) and bytes sent

Client-disconnect handling: if the client cancels mid-stream, we **continue
reading the upstream** to drain its full response — so the final usage chunk
arrives and we can bill correctly. Without this, every cancelled stream would
be billed as 0 tokens (free for the user, paid by us).
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Awaitable, Callable

import httpx

from app.providers.base import Provider
from app.schemas.common import ResponseStats, StreamingState, Usage


async def stream_with_usage(
    upstream: httpx.Response,
    provider: Provider,
    on_complete: Callable[[StreamingState], Awaitable[None]],
) -> AsyncIterator[bytes]:
    """Generator that forwards bytes upstream→client while accumulating usage.

    Yields raw bytes for the client. After the upstream closes (or we drain it
    after a client disconnect), `on_complete(state)` is awaited with final usage.

    The caller wraps this in fastapi.responses.StreamingResponse.
    """
    state = StreamingState()
    started = time.monotonic()
    try:
        async for chunk in upstream.aiter_bytes():
            if state.stats.ttft_ms is None:
                state.stats.ttft_ms = int((time.monotonic() - started) * 1000)

            # Forward to client first (fast path)
            yield chunk

            # Accumulate usage from this chunk
            try:
                for u in provider.extract_streaming_usage_events(chunk):
                    state.usage = _merge_usage(state.usage, u)
            except Exception:
                # Defensive: never let usage parsing break streaming.
                pass

            state.stats.bytes_sent += len(chunk)

        state.stats.finished_normally = True

    except (asyncio.CancelledError, GeneratorExit):
        # Client disconnected. Drain upstream so we still get the final usage event.
        try:
            async for chunk in upstream.aiter_bytes():
                try:
                    for u in provider.extract_streaming_usage_events(chunk):
                        state.usage = _merge_usage(state.usage, u)
                except Exception:
                    pass
        except Exception:
            pass
        # Re-raise so FastAPI knows the response was aborted
        raise

    finally:
        state.stats.upstream_status = upstream.status_code
        try:
            await upstream.aclose()
        except Exception:
            pass
        try:
            await on_complete(state)
        except Exception:
            # We've already responded to the client; on_complete failure shouldn't blow up
            # the response. Real impl logs this.
            pass


def _merge_usage(acc: Usage, evt: Usage) -> Usage:
    """Merge a streaming usage event into the running total.

    Key tricky bits per provider:
      * Anthropic message_start gives input_tokens + cache_*. message_delta gives
        the cumulative output_tokens (not delta).
      * OpenAI emits usage exactly once at the end with totals.

    Strategy:
      - Use the LATEST non-zero value for each "absolute" field (prompt, cache_*).
      - For completion_tokens and reasoning_tokens, prefer the latest non-zero
        absolute value (Anthropic delta is cumulative; OpenAI fires once).

    This means merge isn't strictly additive but rather "adopt latest authoritative
    figure". For v0.1 single-channel this is correct; multi-channel chained
    streaming would need different handling but isn't in v0.1 scope.
    """
    return Usage(
        prompt_tokens=evt.prompt_tokens or acc.prompt_tokens,
        completion_tokens=evt.completion_tokens or acc.completion_tokens,
        cache_read_tokens=evt.cache_read_tokens or acc.cache_read_tokens,
        cache_write_tokens=evt.cache_write_tokens or acc.cache_write_tokens,
        reasoning_tokens=evt.reasoning_tokens or acc.reasoning_tokens,
    )


def merge_usage_public(acc: Usage, evt: Usage) -> Usage:
    """Public reexport for tests."""
    return _merge_usage(acc, evt)


__all__ = ["stream_with_usage", "merge_usage_public", "ResponseStats", "StreamingState"]
