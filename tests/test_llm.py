import config
import llm


def test_selected_provider_prefers_anthropic(monkeypatch):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "sk-ant-real")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "gemini-key")

    assert llm.selected_provider() == "anthropic"


def test_selected_provider_falls_back_to_gemini(monkeypatch):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "gemini-key")

    assert llm.selected_provider() == "gemini"
    assert llm.selected_model("classification") == config.GEMINI_CLASSIFICATION_MODEL


def test_selected_provider_none_without_keys(monkeypatch):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")

    assert llm.selected_provider() == "none"


def test_generate_text_falls_back_to_gemini_when_anthropic_fails(monkeypatch):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "sk-ant-real")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "gemini-key")

    def fail_anthropic(*args, **kwargs):
        raise RuntimeError("anthropic unavailable")

    def fake_gemini(*args, **kwargs):
        return llm.LLMResponse(text="{}", provider="gemini", model=config.GEMINI_SCORING_MODEL)

    monkeypatch.setattr(llm, "_generate_anthropic", fail_anthropic)
    monkeypatch.setattr(llm, "_generate_gemini", fake_gemini)

    response = llm.generate_text(
        "prompt",
        purpose="scoring",
        max_tokens=10,
        temperature=0.1,
        response_json=True,
    )

    assert response.provider == "gemini"


def test_gemini_response_text_reads_candidate_parts():
    class Part:
        text = '{"direction":"neutral"}'

    class Content:
        parts = [Part()]

    class Candidate:
        content = Content()

    class Response:
        text = ""
        candidates = [Candidate()]

    assert llm._gemini_response_text(Response()) == '{"direction":"neutral"}'


def test_wait_for_rate_limit_noops_when_disabled(monkeypatch):
    monkeypatch.setattr(config, "AI_MIN_REQUEST_INTERVAL_SECONDS", 0)

    llm._wait_for_rate_limit()
