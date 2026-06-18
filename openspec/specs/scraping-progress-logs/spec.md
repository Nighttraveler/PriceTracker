# Spec: scraping-progress-logs

## Purpose

Improve scraping observability and performance by preloading the product catalog once per session and emitting structured progress logs during the save loop, so operators can monitor throughput and diagnose slow runs.

## Requirements

### Requirement: Normalizer preloads product catalog once
The Normalizer SHALL load the full product catalog from the database exactly once, at construction time, and reuse it for all fuzzy matching during the session. When a new product is created, the Normalizer SHALL append it to the in-memory catalog so subsequent lookups reflect it.

#### Scenario: Cold cache, product already in DB
- **WHEN** `get_or_create_product` is called with a name whose cleaned form is not in `_cache`
- **THEN** the system performs fuzzy matching against `self._productos` without issuing a DB query

#### Scenario: New product created during session
- **WHEN** `get_or_create_product` creates a new product row in the DB
- **THEN** the new product is appended to `self._productos` before the method returns
- **THEN** a subsequent call with a similar name can match against the newly added product

### Requirement: Normalizer exposes per-session stats
The Normalizer SHALL track cache hits, cache misses, and new products created, and expose them via a `stats()` method returning a dict with keys `cache_hits`, `cache_misses`, and `new_products`.

#### Scenario: Stats after processing a batch
- **WHEN** `get_or_create_product` is called N times in a session
- **THEN** `stats()["cache_hits"] + stats()["cache_misses"]` equals N
- **THEN** `stats()["new_products"]` equals the number of INSERT operations performed

### Requirement: Save loop emits progress logs every 1000 products
During the per-source save loop in `tracker.py`, the system SHALL log a progress line every 1000 products containing: products processed so far, elapsed seconds, rate in products/sec, and estimated seconds remaining.

#### Scenario: Progress log mid-run
- **WHEN** the save loop has processed 1000 products
- **THEN** a log line at INFO level is emitted with count, elapsed time, rate, and ETA

#### Scenario: No extra log at end of batch (non-multiple of 1000)
- **WHEN** the total product count is not a multiple of 1000
- **THEN** no duplicate progress log is emitted at completion beyond the final summary

### Requirement: Per-source save summary log
After completing the save loop for each source, the system SHALL log: total products saved, total save duration in seconds, normalizer cache hits, cache misses, and new products created for that source.

#### Scenario: Summary after anonima save
- **WHEN** the save loop for a source completes
- **THEN** a single INFO log line is emitted with total saved count, duration, and normalizer stats for that source
