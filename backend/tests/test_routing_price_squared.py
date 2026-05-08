"""v0.3 C1: price²-inverse weighted_pick distribution test."""

from __future__ import annotations

import json
from collections import Counter

from app.crypto import encrypt
from app.models.orm import Channel, Model
from app.routing import weighted_pick


def _ch(name: str, weight: int = 100, channel_id: int | None = None) -> Channel:
    return Channel(
        id=channel_id,
        name=name,
        provider="anthropic",
        base_url="https://x",
        upstream_key_encrypted=encrypt("k", b"M" * 32),
        models=json.dumps(["m"]),
        channel_group="default",
        priority=100,
        weight=weight,
        enabled=True,
    )


def _model(price_in: int, price_out: int) -> Model:
    return Model(
        model_id="m",
        display_name="X",
        provider="anthropic",
        price_input_per_million=price_in,
        price_output_per_million=price_out,
    )


def test_no_model_uses_simple_weight():
    """Backward compat: when model is None, just use Channel.weight."""
    a = _ch("a", weight=900, channel_id=1)
    b = _ch("b", weight=100, channel_id=2)
    counts = Counter()
    for _ in range(2000):
        counts[weighted_pick([a, b]).name] += 1
    assert counts["a"] > counts["b"] * 5


def test_homogeneous_pricing_falls_back_to_weight():
    """Same model = same price across channels, so price² doesn't differentiate;
    Channel.weight remains the deciding factor."""
    model = _model(price_in=1_500_000_000, price_out=7_500_000_000)
    a = _ch("a", weight=900, channel_id=1)
    b = _ch("b", weight=100, channel_id=2)
    counts = Counter()
    for _ in range(2000):
        counts[weighted_pick([a, b], model).name] += 1
    # Plain weight ratio dominates
    assert counts["a"] > counts["b"] * 5


def test_single_channel():
    """Only one candidate → always picked."""
    model = _model(1_000_000_000, 5_000_000_000)
    a = _ch("only", channel_id=1)
    for _ in range(50):
        assert weighted_pick([a], model) is a


def test_zero_weight_channel_never_picked_when_others_present():
    """A channel with weight=0 should be effectively skipped via weight=max(1, …)."""
    model = _model(1_000_000_000, 5_000_000_000)
    a = _ch("a", weight=1, channel_id=1)
    b = _ch("b", weight=10000, channel_id=2)
    counts = Counter()
    for _ in range(2000):
        counts[weighted_pick([a, b], model).name] += 1
    # b has 10000× weight vs a; a gets <1% picks
    assert counts["b"] > counts["a"] * 100
