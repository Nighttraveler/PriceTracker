# Design: fix-anonima-cloudfront-block

## Context

La Anónima sits behind CloudFront with AWS WAF bot control. A scrape run is only 7 sequential category GETs (~7500 products), yet the IP gets blocked with 503s. Plain `requests` has a distinctive non-browser TLS/JA3 fingerprint that the WAF detects independently of request rate or headers — which is why the interim mitigations (delays bumped globally to 2–15.5s in `scrapers/base.py:27-28`, scraper disabled at `tracker.py:30`) didn't solve it. Current retry behavior (5/10/20s on 5xx, `base.py:42-45`) re-hits a blocking WAF quickly, and `AnonimaScraper.fetch_all()` (`scrapers/anonima.py:62-63`) swallows all exceptions per category, so a blocked run keeps requesting.

Deployment target is a Raspberry Pi (aarch64) running the Docker stack; the scheduler scrapes Mon/Wed/Fri 07:00.

## Goals / Non-Goals

**Goals:**
- Get past the CloudFront/WAF fingerprint check with `curl_cffi` Chrome impersonation.
- Stop hammering the WAF when blocked: gentler backoff, block detection on sustained 5xx/429, fail-fast in Anónima.
- Keep pacing tuned per source instead of globally.
- Re-enable Anónima in the scheduled runs.

**Non-Goals:**
- Proxy/IP rotation — escalation path only if blocks persist after the fingerprint fix.
- Headless browser (Playwright) — too heavy for the Raspberry Pi; not needed unless WAF starts requiring JS challenges.
- Changes to VTEX scrapers (`vtex_base.py`, Día, Carrefour) — they hit different platforms and are unaffected.
- Circumventing anything other than automated bot fingerprinting for this project's existing, low-volume price collection.

## Decisions

1. **curl_cffi over Playwright or requests-with-better-headers.** curl_cffi impersonates Chrome's exact TLS/JA3/HTTP2 fingerprint, ships prebuilt aarch64 wheels, and its `requests`-compatible API means `base.py:get()` barely changes. Playwright is ~400MB + heavy CPU/RAM on a Pi; header-only tweaks don't change the TLS fingerprint, which is the detected signal.
2. **Drop the manual User-Agent and fake Google Referer** (`base.py:13-18`). Impersonation supplies UA + sec-ch-ua consistent with the TLS fingerprint; a hardcoded UA that mismatches the fingerprint is itself a bot signal. Keep only `Accept-Language: es-AR,es;q=0.9`.
3. **Sustained 429/5xx ⇒ `ScraperBlockedError`, not `RetryError`.** For a WAF-fronted site, three consecutive 503s is a block, not noise. This routes into `tracker.py`'s existing BLOCKED handling (`tracker.py:100-101`) and keeps other sources scraping. `RETRY_BASE_WAIT` goes 5 → 15 (15/30/60s) so retries stop feeding the WAF's rate signal. Since `requests` is no longer imported in `base.py`, the old `requests.exceptions.RetryError` goes away naturally.
4. **Per-scraper delays.** Restore `BaseScraper` to 1.5–3.5s (committed defaults) and set `delay_min=8` / `delay_max=20` as class attributes on `AnonimaScraper`. Encombo stops paying Anónima's penalty; an Anónima run stays under ~3 minutes.
5. **Homepage warm-up in `fetch_all()`.** One GET to `url_base` before category pages picks up CloudFront/session cookies like a real visit — cheap, and category-page-first navigation is an unnatural pattern.
6. **Fail fast on block in Anónima.** Add `except ScraperBlockedError: raise` before the generic `except` in `fetch_all()` so a block aborts the run; non-block errors keep the current skip-category behavior.

## Risks / Trade-offs

- [WAF may still block after fingerprint fix (e.g., IP reputation from prior blocks)] → warm-up + slow pacing + fail-fast reduce further reputation damage; wait hours before retrying; proxy rotation is the documented escalation path (docs/maintenance.md note).
- [curl_cffi behavior differs subtly from requests (encoding, exceptions)] → `resp.status_code` / `resp.text` / `raise_for_status()` are API-compatible; Encombo regression dry-run covers the shared path.
- [Impersonated fingerprint ages as Chrome versions move] → `impersonate="chrome"` tracks curl_cffi's latest supported Chrome; keep the dependency reasonably updated.
- [Blocked run yields zero Anónima prices for that day] → acceptable: DB is append-only and `max_por_fuente` queries tolerate missing days per source by design.

## Migration Plan

1. Add `curl_cffi>=0.7.0` to `requirements.txt`; `pip install` in the venv; Docker image picks it up on next build.
2. Code changes land together (base.py, anonima.py, tracker.py re-enable).
3. Rollback: revert the commit; Anónima can be re-disabled by commenting out its `SCRAPERS` entry as today.

## Open Questions

- None blocking. If blocks persist after this lands, decide between residential proxy rotation and reducing Anónima scrape frequency (e.g., weekly).
