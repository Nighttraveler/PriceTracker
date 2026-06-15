## Why

La Anónima blocked the scraper's IP after repeated identical requests — the current `BaseScraper` creates a new session per URL (no cookie persistence), uses a fixed User-Agent, and treats a 403 block the same as any other error, continuing to hammer the site across all categories. This makes blocks both more likely and harder to detect. With a MWF 7am cron hitting 4 sources from a single IP, the other HTML source (Encombo) faces the same risk.

## What Changes

- **`ScraperBlockedError`** — new exception class raised on 403 responses, allowing callers to distinguish a block from a generic HTTP error.
- **Session at instance level** — `BaseScraper` creates one `requests.Session` per scraper instance instead of per request, enabling cookie persistence across category pages within a single scrape run.
- **Retry with exponential backoff for 429 and 5xx** — `BaseScraper.get()` retries transient errors (rate-limit, server errors) with the same pattern already used in `VTEXScraper`.
- **Abort source on first block** — when `ScraperBlockedError` is raised, the individual scraper propagates it up; `tracker.py` catches it, logs a loud error, and skips the remaining work for that source without affecting other sources.
- **`tracker.py` block handling** — add a specific `except ScraperBlockedError` branch that logs at `ERROR` level with a clear "BLOCKED" label, distinct from generic scraping errors.

No Alembic migration required. Does not affect cached routes or latest-price queries.

## Capabilities

### New Capabilities

- `scraper-block-detection`: Detect and surface HTTP 403 blocks as a distinct, named error so the system can abort cleanly and log visibly instead of silently retrying.
- `scraper-request-resilience`: Retry transient failures (429, 5xx) with exponential backoff and maintain session continuity across requests within a scrape run.

### Modified Capabilities

_(none)_

## Impact

- `scrapers/base.py`: Session moved to `__init__`, `get()` gains retry logic and `ScraperBlockedError` on 403.
- `tracker.py`: New `except ScraperBlockedError` branch in the per-source scraping loop.
- `scrapers/anonima.py`, `scrapers/encombo.py`: No code changes — they inherit the fix from `BaseScraper`.
- `scrapers/vtex_base.py`: No changes — already has its own retry logic.
- No new dependencies.
