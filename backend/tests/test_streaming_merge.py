"""Test the streaming usage merge logic."""

from __future__ import annotations

from app.schemas.common import Usage
from app.streaming import merge_usage_public as merge


def test_merge_first_event():
    """Merging onto an empty Usage = the new event."""
    acc = Usage()
    evt = Usage(prompt_tokens=42, cache_read_tokens=10, cache_write_tokens=5)
    out = merge(acc, evt)
    assert out.prompt_tokens == 42
    assert out.cache_read_tokens == 10
    assert out.cache_write_tokens == 5


def test_merge_anthropic_streaming_pattern():
    """Anthropic emits message_start (input + cache) THEN message_delta (final output)."""
    msg_start = Usage(prompt_tokens=42, cache_read_tokens=10, cache_write_tokens=5)
    msg_delta = Usage(completion_tokens=123)

    acc = Usage()
    acc = merge(acc, msg_start)
    acc = merge(acc, msg_delta)

    assert acc.prompt_tokens == 42
    assert acc.cache_read_tokens == 10
    assert acc.cache_write_tokens == 5
    assert acc.completion_tokens == 123


def test_merge_openai_pattern():
    """OpenAI: usage arrives once at the end with totals."""
    acc = Usage()
    final = Usage(prompt_tokens=100, completion_tokens=50, reasoning_tokens=200)
    acc = merge(acc, final)
    assert acc.prompt_tokens == 100
    assert acc.completion_tokens == 50
    assert acc.reasoning_tokens == 200


def test_merge_does_not_overwrite_with_zero():
    """If a new event has 0 for a field, the accumulator's value stays."""
    acc = Usage(prompt_tokens=42)
    evt = Usage(prompt_tokens=0, completion_tokens=5)
    out = merge(acc, evt)
    assert out.prompt_tokens == 42
    assert out.completion_tokens == 5
