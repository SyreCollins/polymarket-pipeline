import classifier
from markets import Market


def test_load_json_object_from_wrapped_text():
    result = classifier._load_json_object(
        'Here is the result:\n{"direction":"bullish","materiality":0.8,"reasoning":"Relevant."}'
    )

    assert result["direction"] == "bullish"
    assert result["materiality"] == 0.8


def test_load_json_object_rejects_empty_text():
    try:
        classifier._load_json_object("")
    except ValueError as e:
        assert "empty response" in str(e)
    else:
        raise AssertionError("Expected ValueError")


def test_classification_toon_is_compact():
    market = Market(
        condition_id="m1",
        question="Will OpenAI release GPT-5 before August 2026?",
        category="ai",
        yes_price=0.4,
        no_price=0.6,
        volume=10000,
        end_date="",
        active=True,
        tokens=[],
    )

    result = classifier._classification_toon("OpenAI news", market, "rss")

    assert "market: Will OpenAI release GPT-5" in result
    assert "yes_price: 0.40" in result
    assert "news: OpenAI news" in result
