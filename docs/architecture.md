# Core architecture

The flow is: **scraper → normalizer → db → app/reporter**

## Modules

**`tracker.py`** orchestrates scraping: it instantiates the source's scraper, calls `fetch_all()`,
and for each product calls `normalizer.obtener_o_crear_producto()` + `db.get_or_create_variante()`
+ `db.insertar_precio()`.

**`db.py`** is the single data-access layer. All query methods live here; `app.py` and `reporter.py`
only call `Database` methods. The DB is **append-only**: `precios` is never updated or deleted.
It supports SQLite (dev default) and PostgreSQL (the active DB, via `DATABASE_URL`);
see [database.md](database.md).

**`normalizer.py`** does fuzzy matching to decide whether a new name corresponds to an existing
product or a new one must be created. Full details in [normalization.md](normalization.md).

## Schema

`fuentes` → `variantes` ← `productos`, `variantes` ← `precios`.

A given product (e.g. "leche entera la serenísima 1 lt") has a single row in `productos` with its
`nombre_normalizado`, and one `variante` per source where it appears (with that source's original
name and URL). Prices accumulate in `precios` with a date.
