# Commands

> Always activate the virtualenv before any command: `source .venv/bin/activate`

## Full stack (Docker)

```bash
docker compose up -d            # starts db, app (Flask API), frontend (React), scraper
docker compose up -d db app     # API-only (no frontend)
```

The React frontend is at **http://localhost:3000**.
The Flask API is at **http://localhost:5000** (also available for direct access/debugging).

## Frontend (React Router)

Run from `frontend/`:

```bash
pnpm dev                # dev server → http://localhost:5173 (HMR, proxies API to localhost:5000)
pnpm build              # production SSR build → build/
pnpm start              # serve the production build → http://localhost:3000
pnpm typecheck          # tsc + React Router type generation
pnpm lint               # oxlint
pnpm format             # oxfmt (auto-fix)
pnpm format:check       # oxfmt (CI check)
pnpm test               # Vitest unit tests (run once)
pnpm test:watch         # Vitest in watch mode
pnpm test:e2e           # Playwright end-to-end (requires pnpm dev running)
```

## Backend (Flask API + legacy HTML)

```bash
# Web dashboard
python app.py                          # → http://0.0.0.0:5000

# Scraping
python tracker.py --source all                       # all sources
python tracker.py --source dia                       # single source
python tracker.py --source dia --dry-run --limit 20  # no save, useful for debugging

# Static HTML report
python reporter.py --output reporte.html --days 7

# Unit tests (no network)
pytest tests/ -m "not integration"

# Integration tests (make real HTTP requests to the supermarkets)
pytest tests/ -m integration

# A specific test
pytest tests/test_normalizer.py::test_detectar_categoria_lacteos

# DB stats
python db.py --stats
```

## Querying PostgreSQL (the active DB)

```bash
make psql                                       # interactive shell
make psql Q="SELECT COUNT(*) FROM productos;"   # one-shot query

# Or directly via DATABASE_URL:
DATABASE_URL=postgresql://user:password@localhost:5432/price_tracker python db.py --stats
```

See [database.md](database.md) for the PostgreSQL policy and [maintenance.md](maintenance.md)
for maintenance scripts.
