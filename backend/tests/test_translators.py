"""OAI ↔ Anthropic translator unit tests."""

from __future__ import annotations

import json

from app.providers.translators.anth_to_oai import (
    anth_request_to_oai,
    oai_response_to_anth,
)
from app.providers.translators.oai_to_anth import (
    anth_response_to_oai,
    oai_request_to_anth,
)

# ─── OAI → Anthropic ─────────────────────────────────────────────────────────


def test_oai_to_anth_basic_chat():
    oai = {
        "model": "claude-haiku-4-5",
        "messages": [
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": "Hi"},
        ],
        "max_tokens": 100,
        "temperature": 0.5,
    }
    anth = oai_request_to_anth(oai)
    assert anth["model"] == "claude-haiku-4-5"
    assert anth["max_tokens"] == 100
    assert anth["system"] == "Be helpful"
    assert anth["messages"] == [{"role": "user", "content": "Hi"}]
    assert anth["temperature"] == 0.5


def test_oai_to_anth_default_max_tokens():
    """Anthropic requires max_tokens; we fill in default if OAI omits."""
    oai = {"model": "x", "messages": [{"role": "user", "content": "hi"}]}
    anth = oai_request_to_anth(oai)
    assert anth["max_tokens"] == 4096


def test_oai_to_anth_multiple_system_messages_concatenated():
    oai = {
        "model": "x",
        "messages": [
            {"role": "system", "content": "Rule 1"},
            {"role": "system", "content": "Rule 2"},
            {"role": "user", "content": "hi"},
        ],
    }
    anth = oai_request_to_anth(oai)
    assert anth["system"] == "Rule 1\n\nRule 2"


def test_oai_to_anth_tools():
    oai = {
        "model": "x",
        "messages": [{"role": "user", "content": "hi"}],
        "tools": [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Look up weather",
                "parameters": {"type": "object", "properties": {"city": {"type": "string"}}},
            },
        }],
        "tool_choice": "auto",
    }
    anth = oai_request_to_anth(oai)
    assert anth["tools"] == [{
        "name": "get_weather",
        "description": "Look up weather",
        "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}},
    }]
    assert anth["tool_choice"] == {"type": "auto"}


def test_oai_to_anth_assistant_with_tool_calls():
    oai = {
        "model": "x",
        "messages": [
            {"role": "user", "content": "weather?"},
            {
                "role": "assistant",
                "content": "Let me check.",
                "tool_calls": [{
                    "id": "call_abc",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"city":"NYC"}',
                    },
                }],
            },
            {
                "role": "tool",
                "tool_call_id": "call_abc",
                "content": "Sunny, 70F",
            },
        ],
    }
    anth = oai_request_to_anth(oai)
    msgs = anth["messages"]
    # user → user
    assert msgs[0]["role"] == "user"
    # assistant with tool_use block
    assert msgs[1]["role"] == "assistant"
    blocks = msgs[1]["content"]
    assert any(b.get("type") == "text" and b.get("text") == "Let me check." for b in blocks)
    tu = next(b for b in blocks if b.get("type") == "tool_use")
    assert tu["name"] == "get_weather"
    assert tu["input"] == {"city": "NYC"}
    assert tu["id"] == "call_abc"
    # tool → user with tool_result
    assert msgs[2]["role"] == "user"
    tr = msgs[2]["content"][0]
    assert tr["type"] == "tool_result"
    assert tr["tool_use_id"] == "call_abc"


# ─── Anthropic response → OAI ────────────────────────────────────────────────


def test_anth_response_to_oai_basic():
    anth = {
        "id": "msg_xyz",
        "model": "claude-haiku-4-5",
        "content": [{"type": "text", "text": "Hi there"}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 5, "output_tokens": 3},
    }
    oai = anth_response_to_oai(anth, requested_model="claude-haiku-4-5")
    assert oai["object"] == "chat.completion"
    assert oai["choices"][0]["message"]["content"] == "Hi there"
    assert oai["choices"][0]["finish_reason"] == "stop"
    assert oai["usage"]["prompt_tokens"] == 5
    assert oai["usage"]["completion_tokens"] == 3


def test_anth_response_to_oai_tool_use():
    anth = {
        "id": "msg_x",
        "model": "claude-haiku-4-5",
        "content": [
            {"type": "text", "text": "calling tool"},
            {"type": "tool_use", "id": "toolu_1", "name": "get_weather", "input": {"city": "Paris"}},
        ],
        "stop_reason": "tool_use",
        "usage": {"input_tokens": 10, "output_tokens": 5},
    }
    oai = anth_response_to_oai(anth, requested_model="claude-haiku-4-5")
    msg = oai["choices"][0]["message"]
    assert msg["content"] == "calling tool"
    tcs = msg["tool_calls"]
    assert tcs[0]["function"]["name"] == "get_weather"
    assert json.loads(tcs[0]["function"]["arguments"]) == {"city": "Paris"}
    assert oai["choices"][0]["finish_reason"] == "tool_calls"


# ─── Anthropic → OAI request ─────────────────────────────────────────────────


def test_anth_to_oai_basic():
    anth = {
        "model": "gpt-5",
        "system": "Be terse",
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 100,
        "temperature": 0.4,
        "stop_sequences": ["END"],
    }
    oai = anth_request_to_oai(anth)
    assert oai["model"] == "gpt-5"
    assert oai["max_tokens"] == 100
    assert oai["temperature"] == 0.4
    assert oai["stop"] == ["END"]
    assert oai["messages"][0] == {"role": "system", "content": "Be terse"}
    assert oai["messages"][1] == {"role": "user", "content": "Hi"}


def test_anth_to_oai_tool_use_roundtrip():
    anth = {
        "model": "x",
        "messages": [
            {"role": "user", "content": "weather?"},
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Calling tool"},
                    {"type": "tool_use", "id": "toolu_1", "name": "get_weather",
                     "input": {"city": "NYC"}},
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "toolu_1", "content": "Sunny"},
                ],
            },
        ],
    }
    oai = anth_request_to_oai(anth)
    msgs = oai["messages"]
    # Assistant message with tool_calls
    asst = next(m for m in msgs if m["role"] == "assistant")
    assert asst["content"] == "Calling tool"
    assert asst["tool_calls"][0]["function"]["name"] == "get_weather"
    # tool_result → role=tool
    tool_msg = next(m for m in msgs if m["role"] == "tool")
    assert tool_msg["tool_call_id"] == "toolu_1"
    assert tool_msg["content"] == "Sunny"


# ─── OAI response → Anthropic ────────────────────────────────────────────────


def test_oai_response_to_anth_basic():
    oai = {
        "id": "chatcmpl-x",
        "model": "gpt-5",
        "choices": [{
            "message": {"role": "assistant", "content": "Hi there"},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
    }
    anth = oai_response_to_anth(oai, requested_model="gpt-5")
    assert anth["role"] == "assistant"
    assert anth["content"] == [{"type": "text", "text": "Hi there"}]
    assert anth["stop_reason"] == "end_turn"
    assert anth["usage"]["input_tokens"] == 5
    assert anth["usage"]["output_tokens"] == 3


def test_oai_response_to_anth_with_cached_tokens():
    """OAI cached_tokens → Anthropic cache_read_input_tokens; uncached → input_tokens"""
    oai = {
        "id": "x",
        "model": "gpt-5",
        "choices": [{"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
        "usage": {
            "prompt_tokens": 1000,
            "completion_tokens": 50,
            "prompt_tokens_details": {"cached_tokens": 800},
        },
    }
    anth = oai_response_to_anth(oai, requested_model="gpt-5")
    assert anth["usage"]["input_tokens"] == 200       # 1000 - 800
    assert anth["usage"]["cache_read_input_tokens"] == 800
    assert anth["usage"]["output_tokens"] == 50


def test_oai_response_to_anth_tool_calls():
    oai = {
        "id": "x", "model": "gpt-5",
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "fetching",
                "tool_calls": [{
                    "id": "call_1", "type": "function",
                    "function": {"name": "get_weather", "arguments": '{"city":"NYC"}'},
                }],
            },
            "finish_reason": "tool_calls",
        }],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    anth = oai_response_to_anth(oai, requested_model="gpt-5")
    blocks = anth["content"]
    text_block = next(b for b in blocks if b["type"] == "text")
    tu_block = next(b for b in blocks if b["type"] == "tool_use")
    assert text_block["text"] == "fetching"
    assert tu_block["name"] == "get_weather"
    assert tu_block["input"] == {"city": "NYC"}
    assert anth["stop_reason"] == "tool_use"
