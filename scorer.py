from __future__ import annotations

import json

import config
import llm
import toon
from scraper import NewsItem
from markets import Market


SCORING_PROMPT = """Estimate probability market resolves YES from recent news. Do not anchor to market price.
Use base rates, recency, and source credibility. Be calibrated: 0.50=no info, 0.90+=near certainty.

Input (TOON):
{input_toon}

Return ONLY JSON:
{{"confidence":0.0,"reasoning":"2-3 sentences","relevant_headlines":[0]}}"""


def score_market(market: Market, news: list[NewsItem]) -> dict:
    """Score a market question against recent news using the configured AI provider."""
    headlines_text = _news_rows(news)

    if not news:
        return {
            "confidence": 0.5,
            "reasoning": "No relevant news found - returning baseline.",
            "relevant_headlines": [],
        }

    prompt = SCORING_PROMPT.format(
        input_toon=_scoring_toon(market, headlines_text),
    )

    try:
        response = llm.generate_text(
            prompt,
            purpose="scoring",
            max_tokens=500,
            temperature=0.2,
            response_json=True,
        )
        result = _load_json_object(response.text)
        result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))
        return result

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        return {
            "confidence": 0.5,
            "reasoning": f"Parsing error: {e}",
            "relevant_headlines": [],
        }
    except Exception as e:
        return {
            "confidence": 0.5,
            "reasoning": f"Scoring error ({type(e).__name__}): {e}",
            "relevant_headlines": [],
        }


def filter_news_for_market(market: Market, news: list[NewsItem]) -> list[NewsItem]:
    """Quick keyword filter to reduce noise before scoring."""
    keywords = _extract_keywords(market.question)
    if not keywords:
        return news[:30]

    relevant = []
    for item in news:
        text = f"{item.headline} {item.summary}".lower()
        if any(kw in text for kw in keywords):
            relevant.append(item)

    return relevant[:30] if relevant else news[:15]


def _extract_keywords(question: str) -> list[str]:
    """Extract meaningful keywords from a market question."""
    stopwords = {
        "will", "the", "a", "an", "be", "by", "in", "on", "at", "to",
        "of", "for", "is", "it", "this", "that", "and", "or", "not",
        "before", "after", "end", "yes", "no", "any", "has", "have",
        "does", "do", "than", "more", "less", "over", "under",
    }
    words = question.lower().split()
    return [w.strip("?.,!") for w in words if w.strip("?.,!") not in stopwords and len(w) > 2]


def _news_rows(news: list[NewsItem]) -> str:
    items = [
        {
            "id": i,
            "source": item.source,
            "age_h": f"{item.age_hours():.1f}",
            "headline": item.headline,
        }
        for i, item in enumerate(news)
    ]
    return toon.rows("news", ["id", "source", "age_h", "headline"], items)


def _scoring_toon(market: Market, headlines_text: str) -> str:
    return "\n".join([
        toon.mapping({
            "market": market.question,
            "yes_price": f"{market.yes_price:.2f}",
            "lookback_h": config.NEWS_LOOKBACK_HOURS,
        }),
        headlines_text,
    ])


def _load_json_object(text: str) -> dict:
    text = text.strip()
    if not text:
        raise ValueError("AI provider returned an empty response")
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]

    return json.loads(text)


if __name__ == "__main__":
    from scraper import scrape_all

    test_market = Market(
        condition_id="test",
        question="Will OpenAI release GPT-5 before July 2025?",
        category="ai",
        yes_price=0.35,
        no_price=0.65,
        volume=500000,
        end_date="2025-07-01",
        active=True,
        tokens=[],
    )

    print("Scraping news...")
    news = scrape_all()
    filtered = filter_news_for_market(test_market, news)
    print(f"Found {len(filtered)} relevant headlines")

    print("\nScoring market...")
    result = score_market(test_market, filtered)
    print(f"\nConfidence: {result['confidence']:.2f}")
    print(f"Reasoning: {result['reasoning']}")
