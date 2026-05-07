"""SSE chunk parsing helper.

Server-Sent Events format:
    event: optional_event_name\n
    data: <json>\n
    \n

Multiple chunks may share an event. Some providers (Anthropic) emit explicit
event: lines; others (OpenAI) only emit data: lines with a [DONE] sentinel.

This is a minimal parser for v0.1: it processes byte chunks line-by-line and
yields parsed JSON dicts for each `data:` line that contains JSON. Non-JSON
data lines (like `data: [DONE]`) yield None.
"""

from __future__ import annotations

import json
from collections.abc import Iterable


def iter_sse_data_jsons(chunk: bytes) -> Iterable[tuple[str | None, dict | None]]:
    """Yield (event_name, parsed_json) pairs from an SSE chunk.

    Caveats:
      - Assumes each chunk contains complete events (true for httpx + most LLM
        providers). v0.2 should add a buffered streaming parser if not.
      - Lines starting with `:` are SSE comments — skipped.
      - `data: [DONE]` yields (event, None).
    """
    text = chunk.decode("utf-8", errors="replace")
    current_event: str | None = None

    for raw_line in text.split("\n"):
        line = raw_line.rstrip("\r")
        if not line:
            # Event boundary; reset event name
            current_event = None
            continue
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            current_event = line[len("event:") :].strip()
            continue
        if line.startswith("data:"):
            payload = line[len("data:") :].lstrip()
            if payload == "[DONE]":
                yield (current_event, None)
                continue
            try:
                yield (current_event, json.loads(payload))
            except json.JSONDecodeError:
                # Malformed; skip but don't break the stream
                continue
