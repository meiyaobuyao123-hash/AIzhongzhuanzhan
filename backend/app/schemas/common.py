"""Common schemas shared across providers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Usage:
    """Normalized token usage across all providers.

    Field meanings (provider-agnostic):
      prompt_tokens     — billed at model.price_input_per_million
      completion_tokens — billed at model.price_output_per_million
      cache_read_tokens — billed at model.price_cache_read_per_million (if set)
      cache_write_tokens— billed at model.price_cache_write_per_million (if set)
      reasoning_tokens  — billed at model.price_output_per_million (OpenAI o-series)
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0

    def merge(self, other: Usage) -> Usage:
        """⚠️ DEPRECATED — DO NOT USE for streaming accumulation.

        This adds completion_tokens / reasoning_tokens, which is wrong for
        Anthropic (whose message_delta carries CUMULATIVE output_tokens, not
        deltas). Use `app.streaming.sse._merge_usage` instead, which uses
        "latest non-zero wins" semantics and handles all providers correctly.

        Kept only for legacy callers that did simple additive aggregation
        of fully-closed Usage objects (not streaming chunks). New code
        should NOT call this.
        """
        return Usage(
            prompt_tokens=self.prompt_tokens or other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            cache_read_tokens=self.cache_read_tokens or other.cache_read_tokens,
            cache_write_tokens=self.cache_write_tokens or other.cache_write_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
        )

    def is_empty(self) -> bool:
        return (
            self.prompt_tokens == 0
            and self.completion_tokens == 0
            and self.cache_read_tokens == 0
            and self.cache_write_tokens == 0
            and self.reasoning_tokens == 0
        )

    def to_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "reasoning_tokens": self.reasoning_tokens,
        }


@dataclass
class ResponseStats:
    """Performance metadata accumulated during streaming."""

    ttft_ms: int | None = None
    bytes_sent: int = 0
    finished_normally: bool = False
    upstream_status: int | None = None


@dataclass
class StreamingState:
    """Mutable accumulator passed between SSE chunk handlers."""

    usage: Usage = field(default_factory=Usage)
    stats: ResponseStats = field(default_factory=ResponseStats)
