"""SSE chunk parser tests."""

from __future__ import annotations

from app.providers._sse import iter_sse_data_jsons


def test_simple_data_event():
    chunk = b'data: {"hello":"world"}\n\n'
    events = list(iter_sse_data_jsons(chunk))
    assert events == [(None, {"hello": "world"})]


def test_named_event():
    chunk = b'event: message_start\ndata: {"type":"message_start"}\n\n'
    events = list(iter_sse_data_jsons(chunk))
    assert events == [("message_start", {"type": "message_start"})]


def test_done_sentinel():
    chunk = b"data: [DONE]\n\n"
    events = list(iter_sse_data_jsons(chunk))
    assert events == [(None, None)]


def test_multiple_events_one_chunk():
    chunk = (
        b'event: a\ndata: {"x":1}\n\n'
        b'event: b\ndata: {"y":2}\n\n'
        b"data: [DONE]\n\n"
    )
    events = list(iter_sse_data_jsons(chunk))
    assert events == [("a", {"x": 1}), ("b", {"y": 2}), (None, None)]


def test_comment_skipped():
    chunk = b": this is a comment\ndata: {\"k\":1}\n\n"
    events = list(iter_sse_data_jsons(chunk))
    assert events == [(None, {"k": 1})]


def test_malformed_json_skipped():
    chunk = b"data: {bad json\n\ndata: {\"ok\":true}\n\n"
    events = list(iter_sse_data_jsons(chunk))
    assert events == [(None, {"ok": True})]
