# Spec delta: scraper-browser-impersonation

## ADDED Requirements

### Requirement: Base scrapers use a browser-impersonated TLS session
`BaseScraper` SHALL create its persistent session with `curl_cffi.requests.Session(impersonate="chrome")` so every request presents a Chrome-consistent TLS/JA3 fingerprint. Plain `requests` SHALL NOT be used for scraper HTTP traffic in `scrapers/base.py`.

#### Scenario: La Anónima category pages return 200 through CloudFront
- **WHEN** `AnonimaScraper.fetch_all()` requests the 7 category pages through the impersonated session
- **THEN** the requests complete without 403/503 WAF blocks under normal conditions

#### Scenario: Encombo works unchanged on the impersonated session
- **WHEN** `EncomboScraper.fetch_all()` runs on the shared `BaseScraper` session
- **THEN** it fetches and parses products exactly as before

### Requirement: Headers are consistent with the impersonated fingerprint
`BaseScraper` SHALL NOT set a manual `User-Agent` or `Referer` header — impersonation supplies a User-Agent and sec-ch-ua headers matching the TLS fingerprint. The only header override SHALL be `Accept-Language: es-AR,es;q=0.9`.

#### Scenario: No mismatched User-Agent is sent
- **WHEN** a `BaseScraper` request is made
- **THEN** the User-Agent is the one supplied by curl_cffi impersonation, not a hardcoded string

### Requirement: Request pacing is configured per scraper
`BaseScraper` SHALL default to `delay_min = 1.5` / `delay_max = 3.5` seconds between requests. `AnonimaScraper` SHALL override these with `delay_min = 8` / `delay_max = 20`. Delay tuning for one source SHALL NOT change the pacing of other sources.

#### Scenario: Anónima requests are slow-paced
- **WHEN** `AnonimaScraper.get()` is called
- **THEN** it sleeps a uniform random 8–20 seconds before the request

#### Scenario: Encombo keeps fast base pacing
- **WHEN** `EncomboScraper.get()` is called
- **THEN** it sleeps a uniform random 1.5–3.5 seconds before the request

### Requirement: Anónima warms up the session before scraping categories
`AnonimaScraper.fetch_all()` SHALL issue a GET to the site homepage (`url_base`) before requesting any category page, so category requests carry the cookies a real visit would have.

#### Scenario: Homepage is fetched first
- **WHEN** `AnonimaScraper.fetch_all()` starts
- **THEN** the first HTTP request of the run is to `https://www.laanonima.com.ar` and its cookies are reused on subsequent category requests
