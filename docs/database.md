# Database

## PostgreSQL is the active DB

**Always use PostgreSQL for queries and tests**, not the local SQLite file.
The Docker stack exposes PostgreSQL on `localhost:5432`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/price_tracker
```

For Python scripts that use `db.py`, pass it as an environment variable:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/price_tracker python <script>.py
```

`db.py` supports SQLite as a dev default, but PostgreSQL is the system of record.
For maintenance scripts, prefer running them inside the container to use Docker's internal network
(see [maintenance.md](maintenance.md)).

## Critical queries (latest price per source)

The `/ahorro`, optimal-cart, and search queries use a `max_por_fuente` CTE to get the latest price
of **each source independently**:

```sql
WITH max_por_fuente AS (
    SELECT v.fuente_id, MAX(date(pr.fecha)) AS max_fecha
    FROM precios pr JOIN variantes v ON pr.variante_id = v.id
    GROUP BY v.fuente_id
),
latest AS (
    SELECT ... FROM precios pr
    JOIN variantes v ON pr.variante_id = v.id
    JOIN max_por_fuente m ON v.fuente_id = m.fuente_id AND date(pr.fecha) = m.max_fecha
)
```

**Do not use** `WHERE date(pr.fecha) = (SELECT MAX(date(fecha)) FROM precios)` — that global MAX
makes sources that weren't scraped on the same day disappear.

## Indexes

Indexes are created in `db.init_schema()` (idempotent via `IF NOT EXISTS`), so fresh installs
include them. The most important ones for the `latest` queries:

- `idx_variantes_producto` on `variantes(producto_id)` — reverse JOIN productos→variantes
- `idx_variantes_fuente` on `variantes(fuente_id)` — GROUP BY of the `max_por_fuente` CTE
- `idx_precios_variante_fecha` on `precios(variante_id, fecha)` — covering index

> Note: adding a new index to the live schema is a schema modification and goes through an **Alembic
> migration** (below). The `_DDL` / `init_schema()` is updated in parallel only so fresh installs
> start with the index already present.

## Schema migrations — Alembic

The project uses **Alembic** for incremental migrations. Migrations live in `alembic/versions/`.

```bash
# Show current state
DATABASE_URL=postgresql://... alembic current

# Apply all pending migrations
DATABASE_URL=postgresql://... alembic upgrade head

# Create a new migration (always manual, no autogenerate — there are no ORM models)
DATABASE_URL=postgresql://... alembic revision -m "change_description"
# Then edit alembic/versions/<hash>_change.py with upgrade() and downgrade()

# Revert the last migration
DATABASE_URL=postgresql://... alembic downgrade -1
```

**Rule:** every schema modification (ADD COLUMN, CREATE INDEX, DROP COLUMN, etc.) must be done as an
Alembic migration, not manually. The `_DDL` in `db.py` is updated in parallel so fresh installs
already include the change.
