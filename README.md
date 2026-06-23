# Price Tracker

Scraper de precios de supermercados argentinos con dashboard web. Rastrea productos de La Anónima, Día, Encombo y Carrefour, normaliza nombres entre fuentes, persiste en PostgreSQL (o SQLite) y expone un dashboard para comparar precios y detectar variaciones.

## Fuentes soportadas

| Fuente | Tecnología | Categorías scrapeadas |
|---|---|---|
| La Anónima | HTML + data-attributes | Almacén, bebidas, lácteos, limpieza, perfumería, congelados, carnicería |
| Día | VTEX Catalog API REST | Almacén, desayuno, bebidas, frescos, congelados, limpieza, perfumería, mascotas |
| Encombo | HTML | Múltiples categorías |
| Carrefour | VTEX Catalog API REST | Almacén, bebidas, lácteos, carnes, frutas/verduras, panadería, congelados, limpieza, perfumería, mascotas |

> **Diarco** — descartado: es un mayorista B2B, los precios requieren cuenta registrada.

---

## Stack

- **Python 3.11+**
- **PostgreSQL 16** (producción) / **SQLite** (desarrollo local)
- **Flask 3** — JSON API backend (`/api/v1/*`)
- **React Router v8 (SSR)** + **React 19** — frontend SPA (`frontend/`)
- **psycopg2** — driver PostgreSQL
- **rapidfuzz** — fuzzy matching para normalizar nombres entre fuentes
- **BeautifulSoup4 + lxml** — parsing HTML
- **Docker + Docker Compose** — contenedores para db, API, frontend y scraper
- **pytest** — suite de tests Python · **Vitest + Playwright** — tests frontend

---

## Inicio rápido con Docker

```bash
git clone <repo>
cd price-tracker
docker compose up -d
```

Esto levanta cuatro servicios:
- **db** — PostgreSQL 16 en `localhost:5432`
- **app** — Flask JSON API en `http://localhost:5000`
- **frontend** — React SSR app en **http://localhost:3000**
- **scraper** — Scheduler que corre el scraping automático lun/mié/vie a las 7:00

> Para producción con Traefik, pasá el build arg `VITE_API_URL` con el hostname público de la API:
> ```bash
> VITE_API_URL=https://pricetracker.home.arpa docker compose up -d --build
> ```

### Migrar datos existentes de SQLite a PostgreSQL

Si ya tenés un `data/precios.db`, migralo con:

```bash
docker compose up -d db
DATABASE_URL=postgresql://user:password@localhost:5432/price_tracker \
  python scripts/migrate_sqlite_to_postgres.py
```

---

## Setup local (sin Docker)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Por default usa SQLite en `data/precios.db`. Para usar PostgreSQL, setear:

```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/price_tracker
```

---

## Comandos

```bash
# Activar virtualenv (desarrollo local)
source venv/bin/activate

# Scraping
python tracker.py --source all           # todas las fuentes
python tracker.py --source dia           # fuente individual
python tracker.py --source dia --dry-run --limit 20  # sin guardar, útil para debug

# Dashboard web
python app.py                            # → http://0.0.0.0:5000

# Reporte HTML estático
python reporter.py --output reporte.html --days 7

# Stats de la DB
python db.py --stats

# Tests (unitarios, sin red)
pytest tests/ -m "not integration"

# Tests de integración (hacen requests HTTP reales)
pytest tests/ -m integration
```

---

## Automatización (scheduler)

El servicio `scraper` de Docker corre `scheduler.py` que programa scraping automático:

- **Lunes, miércoles y viernes a las 7:00** — scraping de todas las fuentes
- **Lunes a las 7:00** — generación de reporte HTML semanal
- Corre un scrape inmediato al arrancar

```bash
# Correr el scheduler manualmente (configura la hora)
python scheduler.py --hour 7 --report-day lunes

# Ver logs del scraper en Docker
docker compose logs scraper -f
```

---

## Base de datos

`db.py` soporta SQLite y PostgreSQL de forma transparente mediante `DATABASE_URL`:

| Variable | Valor | Comportamiento |
|---|---|---|
| `DATABASE_URL` | `postgresql://user:pass@host/db` | Conecta a PostgreSQL con psycopg2 |
| `DATABASE_URL` | `sqlite:///ruta/archivo.db` | SQLite en la ruta especificada |
| `DATABASE_PATH` | `ruta/archivo.db` | SQLite (fallback si no hay DATABASE_URL) |
| *(ninguna)* | — | SQLite en `data/precios.db` |

> **Importante tras migrar datos a PostgreSQL**: las secuencias se sincronizan automáticamente en cada arranque (`init_schema()` llama `_sync_pg_sequences()`), por lo que no hay conflictos de `id` aunque la migración haya insertado filas con IDs explícitos.

---

## Arquitectura

El flujo es: **scraper → normalizer → db → api → frontend/reporter**

```
price-tracker/
├── app.py              # Flask — API JSON (/api/v1/*) + rutas HTML legacy
├── api.py              # Blueprint /api/v1/* (dashboard, precios, producto, etc.)
├── cache_ext.py        # flask-caching singleton (evita import circular)
├── tracker.py          # CLI de scraping, orquesta todas las fuentes
├── db.py               # Capa de acceso: SQLite + PostgreSQL via DATABASE_URL
├── normalizer.py       # Fuzzy matching, categorías, caché in-memory
├── reporter.py         # Generación de reportes HTML estáticos
├── scheduler.py        # Cron lun/mié/vie 7am via librería schedule
│
├── frontend/           # React Router v8 SSR SPA
│   ├── app/
│   │   ├── routes/     # home, precios, producto.$id, ahorro, buscar, carrito
│   │   ├── shared/     # ui/, stores/, lib/
│   │   └── root.tsx
│   ├── tests/          # Vitest unit tests
│   ├── e2e/            # Playwright end-to-end tests
│   └── Dockerfile
│
├── scrapers/
│   ├── base.py         # BaseScraper: requests con delay, limpiar_precio()
│   ├── anonima.py      # La Anónima — HTML + data-attributes
│   ├── dia.py          # Día — VTEX Catalog API REST con paginación
│   ├── encombo.py      # Encombo — HTML
│   └── carrefour.py    # Carrefour — VTEX Catalog API REST
│
├── templates/          # Jinja2 legacy (en transición)
│
├── scripts/
│   ├── migrate_sqlite_to_postgres.py
│   ├── renormalizar_db.py
│   ├── renormalizar_categorias.py
│   ├── migrar_fechas.py
│   └── corregir_timestamps.py
│
├── tests/              # pytest (Python)
├── Dockerfile          # imagen Flask
├── docker-compose.yml  # Servicios: db, app, frontend, scraper
├── Makefile
└── data/
    └── precios.db      # SQLite local (no versionado)
```

---

## Schema

```sql
CREATE TABLE fuentes (
    id       INTEGER PRIMARY KEY,
    nombre   TEXT NOT NULL UNIQUE,   -- 'anonima', 'dia', 'encombo', 'carrefour'
    url_base TEXT NOT NULL
);

CREATE TABLE productos (
    id                 INTEGER PRIMARY KEY,
    nombre_normalizado TEXT NOT NULL UNIQUE,
    categoria          TEXT,
    unidad             TEXT,
    es_combo           INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE variantes (
    id              INTEGER PRIMARY KEY,
    producto_id     INTEGER REFERENCES productos(id),
    fuente_id       INTEGER REFERENCES fuentes(id),
    nombre_original TEXT NOT NULL,
    url_producto    TEXT,
    UNIQUE(fuente_id, nombre_original)
);

CREATE TABLE precios (
    id          INTEGER PRIMARY KEY,
    variante_id INTEGER REFERENCES variantes(id),
    precio      REAL NOT NULL,
    fecha       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    moneda      TEXT DEFAULT 'ARS'
);
```

`precios` es **append-only** — nunca se actualizan ni borran registros. Un mismo producto tiene una fila en `productos`, una `variante` por fuente donde aparece, y sus precios acumulados en `precios`.

---

## Dashboard web (React, `http://localhost:3000`)

| Ruta | Descripción |
|---|---|
| `/` | Stats generales + highlights de variaciones de precio |
| `/precios` | Tabla comparativa paginada, filtrable por categoría |
| `/ahorro` | Precio promedio por categoría/fuente + carrito óptimo |
| `/buscar` | Búsqueda con filtros de fuente y categoría |
| `/producto/:id` | Historial de precios con gráfico Recharts |
| `/carrito` | Carrito personalizado con cálculo óptimo de compra |

---

## Normalización de productos

`normalizer.py` unifica nombres entre fuentes usando `fuzz.token_sort_ratio` (umbral 98). Antes de comparar, `_normalizar_para_match()` aplica equivalencias: `cc → ml`, `grs → g`, une número+unidad (`400 ml → 400ml`), y quita conectores (`con`, `y`, `x`).

**Regla clave**: si los números en dos nombres difieren, el score se fuerza a 0 — evita fusionar "Leche 1L" con "Leche 200ml".

### Categorías disponibles

`combos`, `conservas`, `fiambreria`, `galletitas`, `confiteria`, `snacks`, `condimentos`, `lacteos`, `almacen`, `congelados`, `carnes`, `panificados`, `bebidas`, `limpieza`, `higiene`, `verduleria`, `otros`

El orden en `CATEGORIAS` importa: las más específicas van primero para evitar falsos positivos (ej. `mascotas` antes de `carnes`).

---

## Scrapers VTEX (Día y Carrefour)

Usan la API de catálogo VTEX REST:

```
GET /api/catalog_system/pub/products/search?fq=C:{cat_id}&_from={n}&_to={n+49}
```

- 50 productos por llamada; el header `resources: 0-49/6016` informa el total
- Solo IDs de categorías padre de nivel 1 devuelven resultados
- El árbol de categorías se obtiene dinámicamente desde `/api/catalog_system/pub/category/tree/3`
- Límite VTEX: offset máximo 2500 (`VTEX_MAX_OFFSET`)
- Solo se incluyen productos con `AvailableQuantity > 0`

---

## Scripts de mantenimiento

```bash
# Después de cambiar reglas de categorías en normalizer.py
python scripts/renormalizar_categorias.py

# Después de cambiar lógica de fuzzy matching
# Re-corre el matching para todas las variantes; fusiona duplicados y limpia huérfanos.
python scripts/renormalizar_db.py

# Migración one-time SQLite → PostgreSQL (requiere DATABASE_URL seteado)
python scripts/migrate_sqlite_to_postgres.py
```

---

## Pitfalls conocidos

- **Datos incompletos en `/ahorro`**: si se corrió `tracker.py --limit N` en algún día, esa fecha queda como la "más reciente" con datos parciales. La solución es correr un scrape completo sin `--limit` para generar una fecha más reciente con datos completos.
- **Secuencias PostgreSQL**: al migrar datos con IDs explícitos desde SQLite, las secuencias quedan desincronizadas. `db.init_schema()` las sincroniza automáticamente en cada arranque.
- **Cambio de HTML en scrapers**: La Anónima y Encombo pueden romperse por cambios de selectores CSS. Día y Carrefour usan API REST y son más estables.
- **Encombo timeout**: delays anti-ban altos. Usar `--limit` en desarrollo.
- **Fuzzy matching lento**: el primer scrape de una fuente grande (~7500 productos para Anónima) puede tardar varios minutos. El caché in-memory lo mitiga para runs posteriores en la misma sesión.
