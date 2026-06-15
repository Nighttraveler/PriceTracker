## 1. scrapers/base.py — ScraperBlockedError and session

- [x] 1.1 Add `ScraperBlockedError(Exception)` class at the top of `base.py`, before `HEADERS`
- [x] 1.2 Add `__init__(self)` to `BaseScraper`: create `self.session = requests.Session()` and call `self.session.headers.update(HEADERS)`
- [x] 1.3 Rewrite `BaseScraper.get()`: remove the `with requests.Session() as s:` block; use `self.session.get()` instead
- [x] 1.4 In `get()`, check `resp.status_code == 403` before raise_for_status and raise `ScraperBlockedError(f"Blocked (403): {url}")`
- [x] 1.5 In `get()`, add retry loop for 429 and 5xx: MAX_RETRIES=3, RETRY_BASE_WAIT=5, backoff = RETRY_BASE_WAIT * 2^attempt; after exhausting retries raise `requests.exceptions.RetryError`

## 2. tracker.py — handle ScraperBlockedError

- [x] 2.1 Import `ScraperBlockedError` from `scrapers.base`
- [x] 2.2 In the per-source scraping loop, add `except ScraperBlockedError as e:` before the generic `except Exception` block; log `log.error(f"BLOCKED: {source_name} — {e}")` and `continue`

## 3. Verify

- [x] 3.1 Run `pytest tests/ -m "not integration"` — all existing unit tests pass
- [x] 3.2 Dry-run a working source to confirm session fix doesn't break normal flow: `python tracker.py --source dia --dry-run --limit 5`
- [x] 3.3 Manually verify block detection: simulate a 403 by temporarily pointing AnonimaScraper at a URL that returns 403 (or inspect logs after next Anónima run)
