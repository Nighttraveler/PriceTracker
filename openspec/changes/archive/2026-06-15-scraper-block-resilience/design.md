## Context

Current state of `BaseScraper.get()`:
```
get(url):
  sleep(random 1.5–3.5s)
  Session()           ← new session per call, no cookie persistence
    GET url
    raise_for_status() ← 403 and 404 and 503 all look the same to caller
    return BeautifulSoup
```

`AnonimaScraper.fetch_all()` calls `self.get(url)` inside a `try/except Exception` that logs `log.warning(f"Error en {url}: {e}")` — a block silently becomes a warning and the loop continues with the next category, making 6 more blocked requests before finishing.

`VTEXScraper` already has the right pattern: catches 429 explicitly, retries with exponential backoff, raises `RetryError` on persistent failure. `BaseScraper` should converge toward the same model.

## Goals / Non-Goals

**Goals:**
- One `requests.Session` per scraper instance — cookies persist across all `get()` calls within a single `fetch_all()` run.
- 403 raises `ScraperBlockedError` immediately — no retry, no continuation.
- 429 and 5xx retry with exponential backoff (max 3 attempts), same constants as VTEX.
- `tracker.py` catches `ScraperBlockedError` and logs `ERROR: BLOCKED: <source>`, then skips to next source.

**Non-Goals:**
- IP rotation or proxy support — out of scope for this change.
- User-Agent rotation — out of scope; kept for a future stealth change if needed.
- Changing `VTEXScraper` — it already works; don't unify into `BaseScraper` now.
- Soft-block detection (200 with CAPTCHA body) — deferred; requires per-site heuristics.

## Decisions

**`ScraperBlockedError` in `base.py`, not a separate `exceptions.py`**
The project has no existing exceptions module. Adding one for a single class is premature. `base.py` is imported by all scrapers already.

**Session created in `__init__`, headers set there too**
This mirrors how `requests.Session` is meant to be used. The session is shared across all `get()` calls in a scrape run and closed when the object goes out of scope (context manager not needed — scraper instances are short-lived).

**403 → abort immediately, no retry**
A 403 from a WAF is a deliberate block, not a transient error. Retrying makes the block more severe. One failed request is better than three.

**Retry constants: MAX_RETRIES=3, RETRY_BASE_WAIT=5s (same as VTEX)**
Consistent behavior across scrapers. The 5s base with doubling (5, 10, 20) gives up to 35s of waiting before raising — acceptable for a background cron job.

**`tracker.py` skips the source, doesn't abort the whole run**
If Anónima is blocked, Día/Carrefour/Encombo should still run. The `except ScraperBlockedError` branch in the per-source loop logs the block and `continue`s.

## Risks / Trade-offs

- [Session carries cookies across categories] → For most sites this is desirable (mimics browser). Edge case: a site sets a session cookie that expires mid-run and returns 403 for a different reason. Risk is low; `ScraperBlockedError` would surface it.
- [Retry adds latency on 5xx] → Up to 35s extra per failed page. Cron at 7am has ample slack; acceptable.
- [Encombo uses pagination — a mid-run block would raise after partial data] → The partial products already collected for that category are returned; `tracker.py` saves what it has. No data loss, just incomplete coverage for that category.
