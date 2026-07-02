# Spec: scraper-block-detection

## Purpose

Define how the scraper base class detects and surfaces HTTP 403 (blocked) responses as a distinct exception, allowing callers to identify and handle anti-scraping blocks explicitly.

## Requirements

### Requirement: 403 responses raise ScraperBlockedError
When `BaseScraper.get()` receives a 403 HTTP response, it SHALL raise `ScraperBlockedError` instead of the generic `requests.exceptions.HTTPError`. The exception message SHALL include the URL and status code. No retry SHALL be attempted for 403.

#### Scenario: 403 on first category raises immediately
- **WHEN** `BaseScraper.get()` receives a 403 response
- **THEN** `ScraperBlockedError` is raised with the URL in the message

#### Scenario: tracker.py logs BLOCKED and continues with other sources
- **WHEN** a scraper's `fetch_all()` propagates `ScraperBlockedError`
- **THEN** `tracker.py` logs an ERROR-level message containing "BLOCKED" and the source name, and proceeds to scrape the remaining sources

#### Scenario: other sources are not affected by one blocked source
- **WHEN** source A raises `ScraperBlockedError`
- **THEN** sources B, C, D continue to scrape normally in the same run

### Requirement: ScraperBlockedError is defined in scrapers/base.py
`ScraperBlockedError` SHALL be a top-level exception class in `scrapers/base.py`, importable by `tracker.py` and any other caller that needs to handle it specifically.

#### Scenario: ScraperBlockedError is importable from base
- **WHEN** `from scrapers.base import ScraperBlockedError` is executed
- **THEN** the import succeeds without error

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
