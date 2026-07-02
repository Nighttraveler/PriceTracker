# Maintenance and pitfalls

## Maintenance scripts

Run from the project root with the virtualenv active. To use Docker's internal network, prefer
running them inside the container:

```bash
docker-compose run --rm scraper python scripts/renormalizar_db.py
```

```bash
# After changing category rules in normalizer.py:
python scripts/renormalizar_categorias.py

# After changing fuzzy-matching logic (UMBRAL, _normalizar_para_match):
# Re-runs matching for all variants; merges duplicates and cleans up orphans.
python scripts/renormalizar_db.py

# Check delisted URLs (301/404/410) and flag them in the DB:
DATABASE_URL=postgresql://... python scripts/chequear_urls.py
DATABASE_URL=postgresql://... python scripts/chequear_urls.py --fuente anonima --limit 50 --dry-run
```

`renormalizar_db.py` can take several minutes (26k variants × fuzzy match against ~25k products).
The Normalizer cache helps for repeated names.

## Known pitfalls

- **Running `--source <source>` alone** inserts prices only for that source with today's date.
  If the rest have yesterday's data, the `latest` queries still work (they use max per source, not
  a global max). The optimal cart and cross-source comparisons compare products from the latest day
  of EACH source — if two sources have different dates, their products are still compared together.
- **La Anónima is behind CloudFront/AWS WAF**: plain `requests` gets the IP blocked (503s) by TLS
  fingerprinting, regardless of delays. The scraper must use the curl_cffi impersonated session
  (`BaseScraper`) plus Anónima's slow per-scraper delays (8–20s). If a run gets `BLOCKED`, wait
  several hours before retrying — do NOT tighten the retry loop, it feeds the WAF's rate signal.
  If blocks persist despite the impersonated fingerprint, the escalation path is proxy rotation.
- **Encombo** has high anti-ban delays; use `--limit` during development.
- **HTML changes in scrapers**: Anónima and Encombo can break on CSS selector changes. Día and
  Carrefour use the REST API and are more stable. (See [scrapers.md](scrapers.md).)
- **Slow fuzzy matching** on the first scrape of a large source (Anónima ~7500 products): the
  normalizer fuzzy-matches against every product in the DB. The in-memory cache mitigates this for
  later runs in the same session.
