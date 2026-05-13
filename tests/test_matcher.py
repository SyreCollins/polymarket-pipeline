from markets import Market
from matcher import extract_keywords, match_news_to_markets


def make_market(question, category="ai"):
    return Market(
        condition_id=question[:8],
        question=question,
        category=category,
        yes_price=0.5,
        no_price=0.5,
        volume=10000,
        end_date="",
        active=True,
        tokens=[],
    )


def test_extract_keywords_drops_common_market_words():
    keywords = extract_keywords("Will OpenAI release GPT-5 before August 2026?")

    assert "will" not in keywords
    assert "before" not in keywords
    assert "openai" in keywords
    assert "gpt-5" in keywords


def test_match_news_to_markets_orders_by_keyword_overlap():
    openai_market = make_market("Will OpenAI release GPT-5 before August 2026?")
    bitcoin_market = make_market("Will Bitcoin hit 100k before June?", "crypto")

    matches = match_news_to_markets(
        "OpenAI is testing GPT-5 with partners before a possible launch",
        [bitcoin_market, openai_market],
    )

    assert matches[0] == openai_market
    assert bitcoin_market not in matches
