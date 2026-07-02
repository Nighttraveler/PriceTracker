## 1. Dependency

- [x] 1.1 Add `curl_cffi>=0.7.0` to `requirements.txt` and install it in the venv (`source .venv/bin/activate && pip install -r requirements.txt`)

## 2. Base scraper: impersonation and block handling

- [x] 2.1 In `scrapers/base.py`, replace `requests.Session()` with `curl_cffi.requests.Session(impersonate="chrome")`; drop the `requests` import
- [x] 2.2 Trim `HEADERS` to only `Accept-Language: es-AR,es;q=0.9` (remove hardcoded User-Agent, Accept, and Google Referer)
- [x] 2.3 Restore base delays: `delay_min = 1.5`, `delay_max = 3.5`
- [x] 2.4 Bump `RETRY_BASE_WAIT` from 5 to 15 (backoff becomes 15/30/60s)
- [x] 2.5 On exhausted 429/5xx retries, raise `ScraperBlockedError` (include the URL) instead of `requests.exceptions.RetryError`

## 3. Anónima scraper

- [x] 3.1 In `scrapers/anonima.py`, set class attributes `delay_min = 8`, `delay_max = 20` on `AnonimaScraper`
- [x] 3.2 Add a homepage warm-up GET (`self.session.get(self.url_base, timeout=15)`) at the start of `fetch_all()`
- [x] 3.3 Add `except ScraperBlockedError: raise` before the generic per-category `except` so a block aborts the run (import it from `scrapers.base`)

## 4. Re-enable and document

- [x] 4.1 Uncomment `"anonima": AnonimaScraper,` in the `SCRAPERS` dict in `tracker.py`
- [x] 4.2 Add a Known pitfalls entry to `docs/maintenance.md`: La Anónima is behind CloudFront/AWS WAF; requires the curl_cffi impersonated session and slow per-scraper delays; on a block, wait hours before retrying — do not tighten retries; proxy rotation is the escalation path

## 5. Verification

- [x] 5.1 Dry-run Anónima with a small limit: `python tracker.py --source anonima --dry-run --limit 10` — expect products logged, no 403/503
- [x] 5.2 Regression dry-run Encombo on the shared base class: `python tracker.py --source encombo --dry-run --limit 10`
- [x] 5.3 Full Anónima dry-run (all 7 categories): `python tracker.py --source anonima --dry-run` — confirm a complete run passes; if blocked mid-run, confirm it aborts immediately with a single BLOCKED log line
