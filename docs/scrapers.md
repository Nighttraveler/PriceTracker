# Scrapers

Each scraper implements `fetch_all(limit=None) -> list[dict]` and returns
`[{"nombre": str, "precio": float, "url": str}]`.

| Source | Method |
|--------|--------|
| **Anónima** | HTML via BeautifulSoup, `data-product-*` attributes |
| **Día** | VTEX Catalog API REST (`/api/catalog_system/pub/products/search?fq=C:{id}`) |
| **Carrefour** | VTEX Catalog API REST, same API as Día |
| **Encombo** | HTML via BeautifulSoup |

## VTEX (Día and Carrefour)

- The API only returns products for **level-1 parent** category IDs. Subcategory IDs return
  0 results.
- The category tree is fetched dynamically from `/api/catalog_system/pub/category/tree/3`.
- The `resources: 0-49/809` header reports the total for pagination.
- VTEX limit: max offset 2500 (`VTEX_MAX_OFFSET`).

## Scraper pitfalls

- **HTML changes**: Anónima and Encombo can break on CSS selector changes. Día and Carrefour use
  the REST API and are more stable.
- **Encombo** has high anti-ban delays; use `--limit` during development.
- **First scrape of a large source** (Anónima ~7500 products) is slow: the normalizer fuzzy-matches
  against every product in the DB. The in-memory cache mitigates this for later runs in the same
  session (see [normalization.md](normalization.md)).
- **Running `--source <source>` alone** inserts prices only for that source with today's date;
  see implications in [maintenance.md](maintenance.md).
