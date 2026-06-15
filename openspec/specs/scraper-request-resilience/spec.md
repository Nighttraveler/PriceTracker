# Spec: scraper-request-resilience

## Purpose

Define how the scraper base class maintains persistent HTTP sessions across requests and retries transient failures (rate limits and server errors) with exponential backoff.

## Requirements

### Requirement: Session persists across requests within a scrape run
`BaseScraper` SHALL create one `requests.Session` per instance in `__init__()` and reuse it for all `get()` calls. Headers SHALL be set on the session, not per-request.

#### Scenario: Cookies set by first request are sent in subsequent requests
- **WHEN** a source sets a cookie on the first category page response
- **THEN** that cookie is included in all subsequent `get()` calls within the same `fetch_all()` run

#### Scenario: Each scraper instance has its own session
- **WHEN** two scraper instances are created (e.g., Anónima and Encombo in the same run)
- **THEN** their sessions are independent — cookies from one do not leak to the other

### Requirement: 429 and 5xx responses retry with exponential backoff
`BaseScraper.get()` SHALL retry on 429 (rate limited) and 5xx (server error) responses up to MAX_RETRIES=3 times, waiting RETRY_BASE_WAIT * 2^attempt seconds between attempts (5s, 10s, 20s). After exhausting retries, it SHALL raise `requests.exceptions.RetryError`.

#### Scenario: 429 triggers retry and eventually succeeds
- **WHEN** `BaseScraper.get()` receives a 429 and then a 200 on the next attempt
- **THEN** the method returns the BeautifulSoup of the 200 response without raising

#### Scenario: Persistent 429 raises RetryError after MAX_RETRIES
- **WHEN** `BaseScraper.get()` receives 429 on all 3 attempts
- **THEN** `requests.exceptions.RetryError` is raised

#### Scenario: 5xx triggers retry
- **WHEN** `BaseScraper.get()` receives a 503 response
- **THEN** it waits and retries, same as 429 behavior

#### Scenario: 4xx other than 403/429 raises immediately without retry
- **WHEN** `BaseScraper.get()` receives a 404 or 401 response
- **THEN** it raises `requests.exceptions.HTTPError` immediately, no retry
