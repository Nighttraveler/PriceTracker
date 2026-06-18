# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

**price-tracker** scrapes prices from Argentine supermarkets (Anónima, Día, Carrefour, Encombo),
normalizes/deduplicates them, and serves them via a Flask dashboard and static HTML reports.

## Essentials for any task

- **Always activate the virtualenv first:** `source .venv/bin/activate`
- **The active DB is PostgreSQL**, not the local SQLite file. The Docker stack exposes it on
  `localhost:5432`. Pass it as an environment variable to any script that uses `db.py`:
  ```bash
  DATABASE_URL=postgresql://user:password@localhost:5432/price_tracker python <script>.py
  ```
  (`db.py` supports SQLite as a dev default, but PostgreSQL is the system of record.)
- **Core flow:** scraper → normalizer → db → app/reporter
- **The DB is append-only:** `precios` is never updated or deleted.

## Detailed documentation

| Topic | File |
|-------|------|
| Commands (run, scrape, report, tests, DB) | [docs/commands.md](docs/commands.md) |
| Architecture: flow, modules, schema | [docs/architecture.md](docs/architecture.md) |
| Database: PostgreSQL, critical queries, indexes, Alembic | [docs/database.md](docs/database.md) |
| Scrapers: interface, sources, VTEX | [docs/scrapers.md](docs/scrapers.md) |
| Normalization: fuzzy matching and categories | [docs/normalization.md](docs/normalization.md) |
| Web app: routes and templates | [docs/webapp.md](docs/webapp.md) |
| Maintenance scripts and pitfalls | [docs/maintenance.md](docs/maintenance.md) |
