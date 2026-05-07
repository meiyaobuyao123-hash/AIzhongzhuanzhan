"""Cross-protocol translators (OpenAI ↔ Anthropic).

v0.2 scope:
  - Non-streaming: full request/response conversion (text + tool use)
  - Streaming: pass-through of upstream SSE rewrapped into the target format,
    with a minimal but correct accounting of usage at the end

NOT covered (deferred to v0.3+):
  - Vision (image/audio in messages)
  - Multi-content-block content arrays beyond text+tool_use+tool_result
  - Stop sequences edge cases
"""
