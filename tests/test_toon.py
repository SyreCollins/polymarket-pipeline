import toon


def test_scalar_flattens_newlines_and_escapes_backslashes():
    assert toon.scalar("hello\nC:\\tmp") == "hello C:\\\\tmp"


def test_mapping_uses_one_key_value_per_line():
    assert toon.mapping({"market": "Will GPT-5 ship?", "yes_price": "0.42"}) == (
        "market: Will GPT-5 ship?\nyes_price: 0.42"
    )


def test_rows_use_compact_toon_shape():
    result = toon.rows(
        "news",
        ["id", "source", "headline"],
        [{"id": 0, "source": "rss", "headline": "OpenAI news"}],
    )

    assert result == "news[1]{id,source,headline}:\n  0,rss,OpenAI news"
