from datetime import datetime, timezone
import config
import llm
import scorer
from markets import Market
from scraper import NewsItem


def test_score_market_uses_configured_scoring_model(monkeypatch):
    captured = {}

    def fake_generate_text(prompt, **kwargs):
        captured.update(kwargs)
        return llm.LLMResponse(
            text='{"confidence": 0.62, "reasoning": "Relevant news.", "relevant_headlines": [0]}',
            provider="anthropic",
            model=config.SCORING_MODEL,
        )

    monkeypatch.setattr(scorer.llm, "generate_text", fake_generate_text)

    market = Market(
        condition_id="m1",
        question="Will OpenAI release GPT-5 before August 2026?",
        category="ai",
        yes_price=0.4,
        no_price=0.6,
        volume=10000,
        end_date="2026-08-01",
        active=True,
        tokens=[],
    )
    news = [
        NewsItem(
            headline="OpenAI is reportedly preparing a major model release",
            source="test",
            url="",
            published_at=datetime.now(timezone.utc),
        )
    ]

    result = scorer.score_market(market, news)

    assert captured["purpose"] == "scoring"
    assert captured["response_json"] is True
    assert result["confidence"] == 0.62


def test_score_market_returns_baseline_without_news():
    market = Market(
        condition_id="m1",
        question="Will Bitcoin hit 100k?",
        category="crypto",
        yes_price=0.5,
        no_price=0.5,
        volume=10000,
        end_date="",
        active=True,
        tokens=[],
    )

    result = scorer.score_market(market, [])

    assert result["confidence"] == 0.5
    assert result["relevant_headlines"] == []
