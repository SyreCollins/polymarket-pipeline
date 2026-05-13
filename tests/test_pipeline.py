import asyncio

import config
import pipeline


def test_pipeline_uses_configured_max_matches(monkeypatch):
    captured = {}

    def fake_match(headline, markets, max_matches=5):
        captured["max_matches"] = max_matches
        return []

    monkeypatch.setattr(config, "MAX_MATCHES_PER_NEWS", 1)
    monkeypatch.setattr(pipeline, "match_news_to_markets", fake_match)

    fake_event = type(
        "Event",
        (),
        {
            "headline": "OpenAI news",
            "source": "test",
            "received_at": type("Received", (), {"isoformat": lambda self: "now"})(),
            "latency_ms": 0,
        },
    )()

    pipe = pipeline.PipelineV2()
    pipe.market_watcher.tracked_markets = []
    monkeypatch.setattr(pipeline.logger, "log_news_event", lambda **kwargs: 1)

    async def run_once():
        await pipe.news_queue.put(fake_event)
        task = asyncio.create_task(pipe._process_news())
        await asyncio.sleep(0)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(run_once())

    assert captured["max_matches"] == 1
