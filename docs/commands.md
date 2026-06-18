# Commands

> Always activate the virtualenv before any command: `source .venv/bin/activate`

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
