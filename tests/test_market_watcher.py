from datetime import datetime, timezone

from market_watcher import MarketSnapshot, MarketWatcher
from markets import Market


def test_handle_ws_message_ignores_non_price_messages():
    watcher = MarketWatcher()

    watcher._handle_ws_message({"type": "subscribed", "market": "token-yes"})

    assert watcher.stats["price_updates"] == 0


def test_handle_ws_message_updates_matching_token_price():
    watcher = MarketWatcher()
    market = Market(
        condition_id="m1",
        question="Will OpenAI release GPT-5?",
        category="ai",
        yes_price=0.4,
        no_price=0.6,
        volume=10000,
        end_date="",
        active=True,
        tokens=[{"token_id": "token-yes", "outcome": "Yes", "price": 0.4}],
    )
    watcher.snapshots["m1"] = MarketSnapshot(
        market=market,
        last_price=0.4,
        prev_price=0.4,
        last_update=datetime.now(timezone.utc),
    )

    watcher._handle_ws_message({"type": "price_change", "market": "token-yes", "price": 0.45})

    assert watcher.snapshots["m1"].last_price == 0.45
    assert watcher.stats["price_updates"] == 1
