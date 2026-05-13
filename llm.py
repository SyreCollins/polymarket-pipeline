from __future__ import annotations

from dataclasses import dataclass
import logging
import threading
import time

import config

log = logging.getLogger(__name__)
_request_lock = threading.Lock()
_last_request_at = 0.0


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str


def has_anthropic_key() -> bool:
    return bool(config.ANTHROPIC_API_KEY) and config.ANTHROPIC_API_KEY != "sk-ant-..."


def has_gemini_key() -> bool:
    return bool(config.GEMINI_API_KEY)


def selected_provider() -> str:
    if has_anthropic_key():
        return "anthropic"
    if has_gemini_key():
        return "gemini"
    return "none"


def selected_model(purpose: str) -> str:
    provider = selected_provider()
    if provider == "gemini":
        return _gemini_model_for(purpose)
    return _anthropic_model_for(purpose)


def generate_text(
    prompt: str,
    *,
    purpose: str,
    max_tokens: int,
    temperature: float,
    response_json: bool = False,
) -> LLMResponse:
    """
    Generate model text using Anthropic first, with Gemini as a fallback when
    Anthropic credentials are not configured or the Anthropic call fails.
    """
    provider = selected_provider()
    if provider == "anthropic":
        try:
            return _generate_anthropic(
                prompt,
                purpose=purpose,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception:
            if has_gemini_key():
                return _generate_gemini(
                    prompt,
                    purpose=purpose,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_json=response_json,
                )
            raise
    if provider == "gemini":
        return _generate_gemini(
            prompt,
            purpose=purpose,
            max_tokens=max_tokens,
            temperature=temperature,
            response_json=response_json,
        )
    raise RuntimeError("No AI provider configured. Set ANTHROPIC_API_KEY or GEMINI_API_KEY.")


def _anthropic_model_for(purpose: str) -> str:
    if purpose == "classification":
        return config.CLASSIFICATION_MODEL
    return config.SCORING_MODEL


def _gemini_model_for(purpose: str) -> str:
    if purpose == "classification":
        return config.GEMINI_CLASSIFICATION_MODEL
    return config.GEMINI_SCORING_MODEL


def _generate_anthropic(
    prompt: str,
    *,
    purpose: str,
    max_tokens: int,
    temperature: float,
) -> LLMResponse:
    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError("anthropic package is not installed") from e

    model = _anthropic_model_for(purpose)
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return LLMResponse(
        text=response.content[0].text.strip(),
        provider="anthropic",
        model=model,
    )


def _generate_gemini(
    prompt: str,
    *,
    purpose: str,
    max_tokens: int,
    temperature: float,
    response_json: bool,
) -> LLMResponse:
    try:
        from google import genai
    except ImportError as e:
        raise RuntimeError("google-genai package is not installed") from e

    model = _gemini_model_for(purpose)
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    gemini_config = {
        "max_output_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_json:
        gemini_config["response_mime_type"] = "application/json"

    _wait_for_rate_limit()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=gemini_config,
    )
    text = _gemini_response_text(response)
    if not text and response_json:
        log.debug("[llm] Gemini returned empty JSON-mode response; retrying without JSON mode")
        _wait_for_rate_limit()
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        text = _gemini_response_text(response)

    if not text:
        raise RuntimeError(f"Gemini returned empty response ({_gemini_response_reason(response)})")

    return LLMResponse(
        text=text,
        provider="gemini",
        model=model,
    )


def _gemini_response_text(response) -> str:
    text = getattr(response, "text", None)
    if text:
        return text.strip()

    chunks: list[str] = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            part_text = getattr(part, "text", None)
            if part_text:
                chunks.append(part_text)

    return "".join(chunks).strip()


def _gemini_response_reason(response) -> str:
    reasons: list[str] = []
    prompt_feedback = getattr(response, "prompt_feedback", None)
    block_reason = getattr(prompt_feedback, "block_reason", None)
    if block_reason:
        reasons.append(f"block_reason={block_reason}")

    for candidate in getattr(response, "candidates", []) or []:
        finish_reason = getattr(candidate, "finish_reason", None)
        if finish_reason:
            reasons.append(f"finish_reason={finish_reason}")

    return ", ".join(reasons) if reasons else "no reason provided"


def _wait_for_rate_limit():
    global _last_request_at
    interval = max(0.0, config.AI_MIN_REQUEST_INTERVAL_SECONDS)
    if interval <= 0:
        return

    with _request_lock:
        now = time.monotonic()
        wait_seconds = interval - (now - _last_request_at)
        if wait_seconds > 0:
            log.info(f"[llm] Waiting {wait_seconds:.1f}s for AI rate limit")
            time.sleep(wait_seconds)
        _last_request_at = time.monotonic()
