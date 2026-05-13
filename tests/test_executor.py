import config
import executor
import logger
from edge import Signal
from markets import Market


def test_execute_trade_dry_run_logs_trade(monkeypatch, tmp_path):
    db_path = tmp_path / "trades.db"
    monkeypatch.setattr(logger, "DB_PATH", db_path)
    logger.init_db()
    monkeypatch.setattr(config, "DRY_RUN", True)
    monkeypatch.setattr(config, "DAILY_LOSS_LIMIT_USD", 100)

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
    signal = Signal(
        market=market,
        claude_score=0.8,
        market_price=0.4,
        edge=0.48,
        side="YES",
        bet_amount=10,
        reasoning="Test signal.",
        headlines="Test headline.",
        news_source="test",
        classification="bullish",
        materiality=0.8,
        news_latency_ms=100,
        classification_latency_ms=25,
        total_latency_ms=125,
    )

    result = executor.execute_trade(signal)
    trades = logger.get_recent_trades(limit=1)

    assert result["status"] == "dry_run"
    assert len(trades) == 1
    assert trades[0]["classification"] == "bullish"
