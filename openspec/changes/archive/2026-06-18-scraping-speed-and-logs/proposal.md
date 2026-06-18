## Why

The daily scraping run takes ~11.5 hours, almost entirely spent in the save/normalize phase (not in actual HTTP scraping). The root cause is `Normalizer.get_or_create_product()` calling `db.get_all_productos()` on every cache miss, producing thousands of round trips to PostgreSQL and O(N×M) fuzzy comparisons. Additionally, there is zero logging during the save phase — multi-hour gaps with no visibility into progress or bottlenecks.

## What Changes

- `normalizer.py`: Load the full product catalog once at `Normalizer.__init__` instead of fetching it on every cache miss. Maintain the in-memory list when new products are created. Add hit/miss/new-product counters exposed via a `stats()` method.
- `tracker.py`: Add progress logs every 1000 products during the save loop (rate, ETA). Log normalizer stats (hits, misses, new products) and total save duration per source.

## Capabilities

### New Capabilities

- `scraping-progress-logs`: Progress logging during the price-save phase — periodic rate/ETA updates and per-source summary stats (normalizer cache hits/misses, new products created, total save time).

### Modified Capabilities

- none

## Impact

- `normalizer.py`: `Normalizer.__init__` and `get_or_create_product()` — no behavior change, pure performance improvement.
- `tracker.py`: save loop — added logging only, no logic change.
- No Alembic migration required (no schema changes).
- No effect on cached routes or latest-price queries.
