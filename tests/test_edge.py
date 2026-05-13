from datetime import datetime, timezone

import config
from classifier import Classification
from edge import detect_edge_v2, size_position
from markets import Market
from news_stream import NewsEvent


def make_market(yes_price=0.4):
    return Market(
        condition_id="m1",
        question="Will OpenAI release GPT-5 before August 2026?",
        category="ai",
        yes_price=yes_price,
        no_price=1 - yes_price,
        volume=10000,
        end_date="2026-08-01",
        active=True,
        tokens=[],
    )


def make_event():
    now = datetime.now(timezone.utc)
    return NewsEvent(
        headline="OpenAI is reportedly preparing a major model launch",
        source="test",
        url="",
        received_at=now,
        published_at=now,
        latency_ms=100,
    )


def test_detect_edge_v2_rejects_low_materiality(monkeypatch):
    monkeypatch.setattr(config, "MATERIALITY_THRESHOLD", 0.6)
    classification = Classification("bullish", 0.5, "Below threshold.", 25, "test-model")

    assert detect_edge_v2(make_market(), classification, make_event()) is None


def test_detect_edge_v2_creates_bullish_yes_signal(monkeypatch):
    monkeypatch.setattr(config, "MATERIALITY_THRESHOLD", 0.6)
    monkeypatch.setattr(config, "EDGE_THRESHOLD", 0.1)
    classification = Classification("bullish", 0.8, "Strong positive evidence.", 25, "test-model")

    signal = detect_edge_v2(make_market(yes_price=0.4), classification, make_event())

    assert signal is not None
    assert signal.side == "YES"
    assert signal.classification == "bullish"
    assert signal.total_latency_ms == 125


def test_size_position_respects_max_bet(monkeypatch):
    monkeypatch.setattr(config, "MAX_BET_USD", 25)
    monkeypatch.setattr(config, "DAILY_LOSS_LIMIT_USD", 100)

    assert size_position(1.0) == 25
