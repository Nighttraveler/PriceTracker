## Why

The La Anónima scraper gets IP-blocked by CloudFront/AWS WAF (503 responses) after scraping, and is currently disabled in `tracker.py`. The block is fingerprint-based, not rate-based: a run is only 7 sequential GETs, but plain `requests` exposes a non-browser TLS/JA3 fingerprint that AWS WAF bot control detects regardless of delays. The interim mitigation (global delay bump to 2–15.5s) also slows Encombo without fixing the root cause, and the current retry loop hammers an already-blocking WAF with fast 5/10/20s retries.

## What Changes

- Replace `requests.Session` in `BaseScraper` with `curl_cffi.requests.Session(impersonate="chrome")` so all base-class scrapers (Anónima, Encombo) present a real Chrome TLS fingerprint. New dependency: `curl_cffi`.
- Trim static `HEADERS`: drop the hardcoded Chrome User-Agent and fake Google Referer (a manual UA mismatched with the TLS fingerprint is itself a bot signal); keep only `Accept-Language: es-AR`. Impersonation supplies UA and sec-ch-ua headers.
- Treat exhausted 429/5xx retries as a block: raise `ScraperBlockedError` instead of `requests.exceptions.RetryError`.
- Gentler backoff: `RETRY_BASE_WAIT` 5 → 15 (waits 15/30/60s instead of 5/10/20s).
- Move delays from global to per-scraper: restore `BaseScraper` defaults (1.5–3.5s), give `AnonimaScraper` its own 8–20s delays.
- Anónima warm-up request (homepage GET) before category pages so requests carry cookies like a real visit.
- Anónima fails fast on block: `fetch_all()` re-raises `ScraperBlockedError` instead of swallowing it per-category, so a blocked run aborts instead of hitting 6 more categories.
- Re-enable `"anonima"` in `tracker.py` `SCRAPERS`.
- Document the CloudFront/WAF pitfall in `docs/maintenance.md`.

## Capabilities

### New Capabilities
- `scraper-browser-impersonation`: base-class scrapers present a browser-consistent TLS fingerprint and headers via curl_cffi impersonation; per-scraper request pacing; Anónima session warm-up.

### Modified Capabilities
- `scraper-request-resilience`: exhausted 429/5xx retries raise `ScraperBlockedError` (was `requests.exceptions.RetryError`); backoff waits change from 5/10/20s to 15/30/60s; the persistent session is a curl_cffi impersonated session (cookie/session semantics unchanged).
- `scraper-block-detection`: block detection extends beyond 403 — sustained 429/5xx after retries is also surfaced as `ScraperBlockedError`; Anónima's `fetch_all()` propagates the error immediately (aborts remaining categories) instead of swallowing it.

## Impact

- **Code**: `scrapers/base.py`, `scrapers/anonima.py`, `tracker.py`, `requirements.txt`, `docs/maintenance.md`.
- **Dependencies**: adds `curl_cffi` (prebuilt aarch64 wheels — installs on the Raspberry Pi and in the Docker image built from `requirements.txt`).
- **Blast radius**: Encombo inherits the new session and restored 1.5–3.5s delays (drop-in; needs a regression dry-run). VTEX scrapers (Día, Carrefour) use `vtex_base.py` and are untouched.
- **No Alembic migration required** — no schema changes.
- **No cached routes affected** (/, /precios, /ahorro, /buscar untouched); **no latest-price queries touched** (no `max_por_fuente` changes).
