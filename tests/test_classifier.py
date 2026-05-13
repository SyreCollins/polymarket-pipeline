import classifier


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
