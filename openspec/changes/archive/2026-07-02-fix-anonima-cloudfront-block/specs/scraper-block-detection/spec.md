# Spec delta: scraper-block-detection

## ADDED Requirements

### Requirement: Exhausted 429/5xx retries raise ScraperBlockedError
When `BaseScraper.get()` exhausts all retries on 429 or 5xx responses, it SHALL raise `ScraperBlockedError` (not a generic retry error). The exception message SHALL include the URL.

#### Scenario: Persistent 503 surfaces as a block
- **WHEN** `BaseScraper.get()` receives 503 on all MAX_RETRIES attempts
- **THEN** `ScraperBlockedError` is raised, and `tracker.py` logs it as BLOCKED

### Requirement: Anónima aborts the run on a block
`AnonimaScraper.fetch_all()` SHALL re-raise `ScraperBlockedError` instead of swallowing it in the per-category error handler, so a blocked run stops immediately rather than requesting the remaining categories against an already-blocking WAF.

#### Scenario: Block on second category aborts remaining categories
- **WHEN** the second category page raises `ScraperBlockedError`
- **THEN** `fetch_all()` propagates the exception without requesting categories 3–7

#### Scenario: Non-block errors still skip only the failing category
- **WHEN** a category page raises a parse error or a non-block HTTP error
- **THEN** `fetch_all()` logs a warning and continues with the next category
