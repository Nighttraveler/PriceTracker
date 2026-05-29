# Price Tracker

Scraper de precios de supermercados argentinos con dashboard web. Rastrea productos de La Anónima, Día, Encombo y Carrefour, normaliza los nombres, persiste en SQLite y expone un dashboard para comparar precios y detectar variaciones.

## Fuentes soportadas

| Fuente | Tecnología | Categorías scrapeadas |
|---|---|---|
| La Anónima | HTML + data-attributes | Almacén, bebidas, lácteos, limpieza, perfumería, congelados, carnicería |
| Día | VTEX (HTML) | Almacén, lácteos, bebidas, carnes, limpieza, higiene, congelados |
| Encombo | HTML | Múltiples categorías |
| Carrefour | VTEX Catalog API REST | Almacén, bebidas, lácteos, carnes, frutas/verduras, panadería, congelados, limpieza, perfumería, mascotas |

> **Diarco** — descartado: es un mayorista B2B, los precios requieren cuenta registrada.

---

## Stack

- **Python 3.11+** con [uv](https://github.com/astral-sh/uv) para gestión de dependencias
- **SQLite** — append-only, nunca se borran registros históricos de precios
- **Flask 3** — dashboard web
- **rapidfuzz** — fuzzy matching para normalizar nombres de productos entre fuentes
- **BeautifulSoup4 + lxml** — parsing HTML
- **pytest** — suite de tests unitarios e integración

---

## Instalación

```bash
git clone <repo>
cd price-tracker
uv venv
uv pip install -r requirements.txt
```

Inicializar la base de datos:

```bash
uv run python db.py
```

---

## Uso

### Scraping

```bash
# Todas las fuentes
uv run python tracker.py --source all

# Una fuente específica
uv run python tracker.py --source carrefour

# Sin guardar en DB (dry-run)
uv run python tracker.py --source dia --dry-run

# Limitar productos por fuente (útil para pruebas)
uv run python tracker.py --source anonima --limit 50
```

Fuentes disponibles: `all`, `anonima`, `dia`, `encombo`, `carrefour`

### Dashboard web

```bash
uv run python app.py
# → http://<ip>:5000
```

El servidor escucha en `0.0.0.0:5000` por defecto — accesible desde cualquier dispositivo en la misma red.

| Ruta | Descripción |
|---|---|
| `/` | Stats generales + highlights de variaciones |
| `/precios` | Tabla comparativa paginada por fuente, con filtro por categoría |
| `/ahorro` | Precio promedio por categoría/fuente y diferencias entre fuentes |
| `/producto/<id>` | Historial de precios con gráfico Chart.js |

### Reporte HTML estático

```bash
uv run python reporter.py --output reporte.html --days 7
```

### Scheduler (daemon)

```bash
# Scraping cada 24h, reporte los lunes a las 6:00
uv run python scheduler.py --day lunes --hour 6 --scrape-interval 24
```

### Stats de la DB

```bash
uv run python db.py --stats
```

---

## Arquitectura

```
price-tracker/
├── app.py              # Flask — dashboard web
├── tracker.py          # CLI principal de scraping
├── db.py               # Capa de acceso a SQLite
├── normalizer.py       # Normalización y categorización de productos
├── reporter.py         # Generación de reportes HTML estáticos
├── scheduler.py        # Daemon con schedule configurable
│
├── scrapers/
│   ├── base.py         # BaseScraper con limpiar_precio() y requests con delay
│   ├── anonima.py      # La Anónima (HTML + data-attributes)
│   ├── dia.py          # Día (VTEX HTML con paginación)
│   ├── encombo.py      # Encombo (HTML)
│   └── carrefour.py    # Carrefour (VTEX Catalog API REST, paginado con header resources)
│
├── templates/          # Jinja2 + Bootstrap 5
│   ├── base.html
│   ├── index.html
│   ├── precios.html
│   ├── ahorro.html
│   └── producto.html
│
├── scripts/
│   ├── renormalizar_db.py           # Actualiza IDs de variantes
│   ├── renormalizar_categorias.py   # Recalcula categorías de todos los productos
│   ├── migrar_fechas.py             # Migra columna fecha de TEXT a TIMESTAMP
│   └── corregir_timestamps.py       # Corrige timestamps inconsistentes
│
├── tests/
│   ├── conftest.py                  # Marker "integration"
│   ├── test_normalizer.py           # 53 tests unitarios
│   ├── test_limpiar_precio.py       # 8 tests de parsing de precios
│   └── test_scrapers_integration.py # 4 tests con requests reales
│
├── data/
│   └── precios.db      # SQLite (no versionado)
├── logs/               # Logs de scraping (no versionados)
└── requirements.txt
```

---

## Schema de la base de datos

```sql
CREATE TABLE fuentes (
    id      INTEGER PRIMARY KEY,
    nombre  TEXT NOT NULL UNIQUE,   -- 'anonima', 'dia', 'encombo', 'carrefour'
    url_base TEXT NOT NULL
);

CREATE TABLE productos (
    id                  INTEGER PRIMARY KEY,
    nombre_normalizado  TEXT NOT NULL UNIQUE,
    categoria           TEXT,       -- ver categorías más abajo
    unidad              TEXT,       -- '1000ml', '500g', etc.
    es_combo            INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE variantes (
    id              INTEGER PRIMARY KEY,
    producto_id     INTEGER REFERENCES productos(id),
    fuente_id       INTEGER REFERENCES fuentes(id),
    nombre_original TEXT NOT NULL,  -- nombre exacto en el sitio
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

Los registros de `precios` son **append-only** — nunca se actualizan ni borran.

---

## Normalización de productos

El módulo `normalizer.py` unifica nombres de productos entre fuentes distintas usando fuzzy matching (`rapidfuzz`).

### Flujo

1. `limpiar(nombre)` — lowercase, elimina acentos y caracteres especiales, normaliza espacios
2. Fuzzy matching contra productos existentes con `fuzz.token_sort_ratio`
3. Si el score ≥ 98 → mismo producto. Si no → nuevo producto
4. Al crear: detecta categoría y unidad, marca `es_combo` si aplica

### Umbrales y reglas

- **UMBRAL_SIMILITUD = 98** — alto para evitar fusiones incorrectas
- Si dos nombres tienen números distintos, el score se fuerza a 0 (evita unir "Vino X 750cc" con "Vino X 1L")
- Un producto se marca `es_combo = 1` si su primera palabra es `combo`

### Matching de categorías

`detectar_categoria()` aplica tres estrategias según el keyword:

| Tipo | Criterio | Ejemplo |
|---|---|---|
| Multi-palabra | Substring en nombre completo | `"agua mineral"` en `"agua mineral sin gas..."` |
| Palabra larga (≥5 chars) | Prefix match — cubre plurales | `"galletita"` matchea `"galletitas"` |
| Palabra corta (<5 chars) | Match exacto — evita falsos positivos | `"te"` no matchea `"detergente"` |

### Categorías disponibles

`combos`, `conservas`, `fiambreria`, `galletitas`, `confiteria`, `snacks`, `condimentos`, `lacteos`, `almacen`, `congelados`, `carnes`, `panificados`, `bebidas`, `limpieza`, `higiene`, `verduleria`, `otros`

---

## Scraper de Carrefour — detalle técnico

Carrefour Argentina usa VTEX. El scraper consume la API de catálogo directamente:

```
GET /api/catalog_system/pub/products/search?fq=C:{cat_id}&_from={n}&_to={n+49}
```

- Responde hasta 50 productos por llamada
- El header `resources: 0-49/6016` informa el total — se usa para terminar la paginación
- Sin autenticación requerida

Categorías scrapeadas por ID VTEX: 161 (Almacén), 222 (Desayuno), 255 (Bebidas), 292 (Lácteos), 321 (Carnes), 330 (Frutas y verduras), 336 (Panadería), 347 (Congelados), 359 (Limpieza), 402 (Perfumería), 471 (Mascotas).

---

## Tests

```bash
# Tests unitarios (sin red, rápidos)
uv run pytest tests/ -m "not integration"

# Tests de integración (hacen requests HTTP reales)
uv run pytest tests/ -m integration

# Todo
uv run pytest tests/
```

| Archivo | Tests | Qué cubre |
|---|---|---|
| `test_normalizer.py` | 53 | `limpiar`, `es_combo`, `detectar_categoria` (todas las categorías, falsos positivos, plurales, multi-word), clase `Normalizer` con mock DB |
| `test_limpiar_precio.py` | 8 | Parsing de precios: separadores de miles/decimal, bug Magento 5 dígitos, símbolos de moneda |
| `test_scrapers_integration.py` | 4 | Fetch real de cada fuente, valida estructura y tipos |

---

## Scripts de mantenimiento

```bash
# Recalcular categorías de todos los productos con las reglas actuales
uv run python scripts/renormalizar_categorias.py

# Actualizar IDs de variantes tras cambios en el normalizador
uv run python scripts/renormalizar_db.py

# Migrar columna fecha de TEXT a TIMESTAMP (migración one-time)
uv run python scripts/migrar_fechas.py
```

---

## Pitfalls conocidos

- **Scraper rompe por cambio de HTML**: revisar los selectores CSS en `scrapers/<fuente>.py`. La Anónima usa `data-attributes`; Día usa clases VTEX (`vtex-product-summary-*`).
- **Fuzzy matching excesivo**: si productos distintos se fusionan, aumentar `UMBRAL_SIMILITUD` en `normalizer.py`.
- **Encombo timeout**: scraper lento por anti-ban delays. Usar `--limit` en desarrollo.
- **Carrefour**: si la API empieza a requerir auth, revisar los headers en `scrapers/carrefour.py`.
- **DB bloqueada**: SQLite en WAL mode. Si hay lock, esperar y reintentar; revisar procesos activos con `fuser data/precios.db`.
