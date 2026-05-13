# Polymarket Pipeline Handoff

## Where We Are

This repo is a Python Polymarket news-to-market dry-run trading pipeline.

The main command under active testing is:

```powershell
python cli.py watch
```

The V2 flow is:

```text
news streams -> market matching -> AI classification -> edge detection -> dry-run trade log
```

Live trading is not the current focus. Keep `DRY_RUN=true` while testing.

## What We Changed

- Fixed the old V1 scorer model bug:
  - `scorer.py` now uses `config.SCORING_MODEL` instead of missing `config.CLAUDE_MODEL`.
- Added Gemini fallback:
  - New shared provider module: `llm.py`
  - Anthropic is preferred when `ANTHROPIC_API_KEY` is set.
  - Gemini is used when Anthropic is missing or unavailable and `GEMINI_API_KEY` is set.
- Added Gemini dependency:
  - `google-genai>=1.0.0` in `requirements.txt`.
- Added AI provider verification in `cli.py verify`.
- Added configurable SQLite DB path:
  - `POLYMARKET_DB_PATH`, mainly for tests.
- Added pytest harness:
  - `requirements-dev.txt`
  - `pytest.ini`
  - `tests/`
- Added TOON-style prompt input:
  - New `toon.py`
  - `classifier.py` and `scorer.py` now pass compact TOON input to the model.
  - Output is still JSON for parser reliability.
- Added Gemini quota protection:
  - `MAX_MATCHES_PER_NEWS=1`
  - `AI_MIN_REQUEST_INTERVAL_SECONDS=12`
  - `AI_QUOTA_COOLDOWN_SECONDS=60`
  - If Gemini returns quota errors, `llm.py` starts a cooldown and `pipeline.py` skips classification during that window.
- Made Polymarket WebSocket handling more tolerant:
  - Empty/non-JSON WebSocket messages are ignored instead of forcing reconnect loops.

## Current Runtime Behavior

With Gemini free tier, the pipeline is intentionally slow. Gemini free tier appears to allow about 5 requests/minute for `gemini-2.5-flash`, so the app now spaces AI calls about 12 seconds apart.

If the process was already running before recent patches, stop and restart it. Old running processes will still show the old vague error:

```text
[classifier] Error: Expecting value: line 1 column 1 (char 0)
```

After restart, empty AI responses should produce clearer errors.

## Important Env Vars

Minimum dry-run Gemini setup:

```env
DRY_RUN=true
GEMINI_API_KEY=your_key_here
MAX_MATCHES_PER_NEWS=1
AI_MIN_REQUEST_INTERVAL_SECONDS=12
AI_QUOTA_COOLDOWN_SECONDS=60
```

When Anthropic is available again:

```env
ANTHROPIC_API_KEY=your_key_here
```

Anthropic will be used first. Gemini remains fallback.

## Commands To Run

Install:

```powershell
python -m pip install -r requirements-dev.txt
```

Test:

```powershell
python -m pytest
```

Verify config/API access:

```powershell
python cli.py verify
```

Run dry-run watcher:

```powershell
python cli.py watch
```

## What To Watch For

- Gemini quota errors:
  - Should now trigger cooldown instead of repeated API calls.
- Classifier empty-response errors:
  - If they persist after restart, inspect Gemini safety/finish reasons from `llm.py`.
- Match quality:
  - Matching is still keyword overlap in `matcher.py`.
  - This is probably the next highest-impact improvement.
- RSS flood:
  - RSS fallback can produce many initial events.
  - Since `MAX_MATCHES_PER_NEWS=1`, this is manageable but still noisy.

## Suggested Next Steps

1. Restart the watcher after these code changes.
2. Run tests locally with `python -m pytest`.
3. Let `python cli.py watch` run for a few minutes and confirm quota cooldown behavior.
4. Improve matching quality:
   - Require stronger keyword overlap.
   - Prefer named entities/ticker-like terms.
   - Skip broad category-only matches unless no direct match exists.
5. Add a local mock classifier mode for development:
   - This would let the pipeline run without spending AI quota.
6. Once Anthropic is available, test provider fallback:
   - Anthropic set: should use Claude first.
   - Anthropic unset: should use Gemini.
   - Anthropic failing + Gemini set: should fall back to Gemini.

## Current Caution

Do not enable `--live` yet. The dry-run pipeline is still being tuned for provider limits, matching quality, and stable classification behavior.
