## Why

The codebase was written primarily in Spanish — comments, docstrings, log messages, UI strings, and many function/variable names. Now that the project is moving to English as the working language (reflected in `openspec/config.yaml`), the code itself needs to catch up. This is a pure translation pass: no new features, no DB schema changes, no behavioral changes.

## What Changes

- All UI strings in `templates/` remain in Spanish — the app serves Spanish-speaking users (Argentine market). Templates are out of scope for this change.
- All Python comments and docstrings translated to English across `app.py`, `db.py`, `tracker.py`, `normalizer.py`, `reporter.py`, `scheduler.py`, `top_productos.py`, all files under `scrapers/`, and all files under `scripts/`.
- Log messages and `print()` statements translated to English.
- Spanish function and variable names renamed to English equivalents where safe (not tied to DB column values or external API contracts).
- Test docstrings and inline comments translated to English.

**Explicit non-goals / out of scope:**
- Flask URL routes (`/ahorro`, `/buscar`, `/carrito`) — changing them breaks bookmarks and external links. **Not changed.**
- `CATEGORIAS` dictionary keys in `normalizer.py` — these values are stored in the `categoria` DB column. Renaming requires a migration. **Not changed.**
- Spanish keyword lists inside `CATEGORIAS` (e.g., `"pollo"`, `"carne"`, `"leche"`) — these match against Spanish product names scraped from Argentine supermarkets. They **must stay in Spanish**.
- Product labels in `top_productos.py` (e.g., `"Fideos 500g"`, `"Leche 1L"`) — these are Argentine market category names. **Not changed.**
- DB column names — no Alembic migration is included in this change.
- **`templates/`** — UI copy stays in Spanish for the Argentine user base.

## Capabilities

### New Capabilities
<!-- None — this is a translation refactor, no new system behavior is introduced. -->

### Modified Capabilities
<!-- No spec-level behavior changes. -->

## Impact

- **All Python source files** (`app.py`, `db.py`, `tracker.py`, `normalizer.py`, `reporter.py`, `scheduler.py`, `top_productos.py`, `scrapers/*.py`, `scripts/*.py`, `tests/*.py`)
- **All Jinja2 templates** (`templates/*.html`)
- No changes to `alembic/`, schema DDL, or any data files.
