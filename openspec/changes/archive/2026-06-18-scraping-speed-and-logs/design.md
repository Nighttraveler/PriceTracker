## Context

The daily scraping run processes ~26k products across four sources. The bottleneck is `Normalizer.get_or_create_product()`, which calls `db.get_all_productos()` on every in-session cache miss. Because the cache starts empty on each run and the product list is never re-used between calls, this results in N round trips to PostgreSQL (each fetching ~26k rows) plus N O(M) fuzzy comparisons — where M grows as the catalog expands. Today's run showed ~1.6 s/product, totaling ~11.5 hours.

There is no logging during the save loop, making it impossible to diagnose slowdowns or estimate how long the run will take.

## Goals / Non-Goals

**Goals:**
- Eliminate redundant `get_all_productos()` calls: load the catalog once per Normalizer instance.
- Keep the in-memory catalog up to date as new products are inserted.
- Add progress logs during the save loop (rate, ETA, per-source summary).
- Expose normalizer stats (cache hits/misses, new products) per source.

**Non-Goals:**
- Parallelizing scraping across sources (separate, larger change).
- Batching DB inserts (follow-up optimization if needed).
- Persisting the normalizer cache across runs.

## Decisions

### Decision: Preload product catalog in `Normalizer.__init__`

Load `db.get_all_productos()` once at construction time and store as `self._productos` (a plain list of dicts). On each `get_or_create_product` cache miss, iterate `self._productos` instead of querying the DB. When a new product is inserted, append it to `self._productos` immediately.

**Why not keep the per-call fetch?** Each call returns the full catalog over a network connection to PostgreSQL. With a cold cache and 7–12k products per source, this produces thousands of round trips — the dominant cost.

**Why not use a dict keyed by normalized name?** The fuzzy match compares against *all* names, not just exact lookups. A list is the right structure for linear scan + rapidfuzz.

**Alternative considered: reload catalog between sources.** Rejected — the in-memory list is already kept up to date via `append`, so a reload would be redundant and reintroduce the latency.

### Decision: Add hit/miss/new counters to `Normalizer`

Three integer counters (`_cache_hits`, `_cache_misses`, `_new_products`) incremented in `get_or_create_product`. Exposed via a `stats()` method returning a dict. Counters are **not** reset between sources; `tracker.py` calls `stats()` after each source and logs the deltas.

**Why deltas?** The Normalizer is shared across all sources in a single `run()` call. Logging cumulative stats after each source is less useful than per-source deltas.

### Decision: Progress logs every 1000 products in `tracker.py`

Inside the save loop, log at every 1000th product: count, elapsed time, rate (products/sec), and ETA. Log normalizer stats + total save duration at end of each source.

**Why 1000?** Fine enough to detect stalls, coarse enough to not flood the log. For a 12k-product source this means ~12 progress lines.

## Risks / Trade-offs

- **Memory**: `self._productos` holds ~26k dicts in RAM. At ~100 bytes each that's ~2.6 MB — negligible.
- **Staleness**: If another process inserts products concurrently, the in-memory list won't reflect them. In practice the scraper is a single sequential process, so this is not a real risk.
- **First run after catalog growth**: The preload query itself takes a few seconds for 26k rows. This is a one-time cost per run vs. the current per-product cost.

## Migration Plan

Drop-in replacement. No schema changes, no API changes, no Alembic migration. The Normalizer interface is unchanged — `get_or_create_product(nombre, fuente_id)` still returns an int. The new `stats()` method is additive.
