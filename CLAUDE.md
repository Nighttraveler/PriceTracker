# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate virtualenv (always required)
source .venv/bin/activate

# Run web dashboard
python app.py                          # → http://0.0.0.0:5000

# Scraping
python tracker.py --source all         # todas las fuentes
python tracker.py --source dia         # fuente individual
python tracker.py --source dia --dry-run --limit 20  # sin guardar, útil para debug

# Reporte HTML estático
python reporter.py --output reporte.html --days 7

# Tests (unitarios, sin red)
pytest tests/ -m "not integration"

# Tests de integración (hacen requests HTTP reales a los supermercados)
pytest tests/ -m integration

# Un test específico
pytest tests/test_normalizer.py::test_detectar_categoria_lacteos

# Stats de la DB
python db.py --stats
```

## Arquitectura central

El flujo es: **scraper → normalizer → db → app/reporter**

**`tracker.py`** orquesta el scraping: instancia el scraper de la fuente, llama `fetch_all()`, y para cada producto llama `normalizer.obtener_o_crear_producto()` + `db.get_or_create_variante()` + `db.insertar_precio()`.

**`db.py`** es la única capa de acceso a SQLite. Todos los métodos de consulta viven acá; `app.py` y `reporter.py` solo llaman métodos de `Database`. La DB es **append-only**: `precios` nunca se actualiza ni borra.

**Schema:** `fuentes` → `variantes` ← `productos`, `variantes` ← `precios`. Un mismo producto (p.ej. "leche entera la serenísima 1 lt") tiene una sola fila en `productos` con su `nombre_normalizado`, y una `variante` por cada fuente donde aparece (con el nombre original de esa fuente y su URL). Los precios se acumulan en `precios` con fecha.

**`normalizer.py`** hace fuzzy matching (`rapidfuzz.fuzz.token_sort_ratio`, umbral 98) para decidir si un nombre nuevo corresponde a un producto existente o hay que crear uno nuevo. Regla clave: si los números en los nombres difieren, el score se fuerza a 0 (evita fusionar "leche 1L" con "leche 200ml"). Tiene caché in-memory por sesión.

## Scrapers

Cada scraper implementa `fetch_all(limit=None) -> list[dict]` y devuelve `[{"nombre": str, "precio": float, "url": str}]`.

| Fuente | Método |
|--------|--------|
| **Anónima** | HTML con BeautifulSoup, `data-product-*` attributes |
| **Día** | VTEX Catalog API REST (`/api/catalog_system/pub/products/search?fq=C:{id}`) |
| **Carrefour** | VTEX Catalog API REST, misma API que Día |
| **Encombo** | HTML con BeautifulSoup |

**VTEX importante**: la API solo devuelve productos con IDs de categorías **padre de nivel 1**. Los IDs de subcategorías devuelven 0 resultados. El árbol de categorías se obtiene dinámicamente desde `/api/catalog_system/pub/category/tree/3`. El header `resources: 0-49/809` informa el total para la paginación. Límite VTEX: offset máximo 2500 (`VTEX_MAX_OFFSET`).

## Queries críticas en db.py

Las queries de `/ahorro`, carrito óptimo y búsqueda usan un CTE `max_por_fuente` para obtener el último precio de **cada fuente independientemente**:

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

**No usar** `WHERE date(pr.fecha) = (SELECT MAX(date(fecha)) FROM precios)` — ese MAX global hace desaparecer fuentes que no se scrapearon el mismo día.

## Web app (app.py / templates/)

Flask con Jinja2 + Bootstrap 5. Rutas: `/`, `/precios`, `/ahorro`, `/buscar`, `/producto/<id>`.

`/buscar` acepta `q` (texto), `fuente` (multi-value), `cat` (multi-value) como GET params. El template usa chips con `onchange="this.form.submit()"` para auto-submit al seleccionar filtros.

`/ahorro` muestra el carrito óptimo: los 20 productos presentes en 2+ fuentes con mayor diferencia de precio, agrupados por la fuente más barata.

## Índices en la DB

Los índices se crean en `db.init_schema()` (idempotentes con `IF NOT EXISTS`). Los más importantes para las queries de `latest`:
- `idx_variantes_producto` en `variantes(producto_id)` — JOIN inverso productos→variantes
- `idx_variantes_fuente` en `variantes(fuente_id)` — GROUP BY del CTE `max_por_fuente`
- `idx_precios_variante_fecha` en `precios(variante_id, fecha)` — covering index

## Normalización de categorías

`detectar_categoria()` en `normalizer.py` aplica reglas distintas según longitud del keyword:
- Multi-palabra: substring match en el nombre completo
- Palabra ≥5 chars: prefix match (cubre plurales: "galletita" matchea "galletitas")
- Palabra <5 chars: match exacto (evita "te" → "detergente")

El orden en `CATEGORIAS` importa: las más específicas van primero. `higiene` va antes de `condimentos` (evita que "romero"/"jengibre" en nombres de shampoos gane). `mascotas` va antes de `carnes` (evita que "alimento para perro sabor carne" quede en carnes). `panificados` va antes de `carnes` (evita que "baguetin con jamón" quede en carnes).

## Fuzzy matching — `_normalizar_para_match()`

El matching usa `fuzz.token_sort_ratio` con umbral 98. Antes de comparar, ambos nombres pasan por `_normalizar_para_match()` (no afecta los nombres guardados en DB):
- `cc` → `ml` (1 cc = 1 ml; distintas fuentes usan ambas notaciones)
- `grs` → `g`
- `"400 ml"` → `"400ml"` (une número+unidad en un solo token para que no difieran)
- Quita conectores puros: `{"con", "y", "x"}` (ruido en descripciones de productos)

Sin esto, "Acondicionador Dove Vitamina A+E 400ml" y "Acondicionador con Vitamina A y E Dove x 400 cc" obtenían score 88 (< umbral 98) y se guardaban como productos distintos.

## Scripts de mantenimiento

Todos deben correrse desde la raíz del proyecto con el virtualenv activo.

```bash
# Después de cambiar reglas de categorías en normalizer.py:
python scripts/renormalizar_categorias.py

# Después de cambiar lógica de fuzzy matching (UMBRAL, _normalizar_para_match):
# Re-corre el matching para todas las variantes; fusiona duplicados y limpia huérfanos.
python scripts/renormalizar_db.py

# Migraciones one-time (ya aplicadas):
python scripts/migrar_fechas.py          # TEXT → TIMESTAMP en columna fecha
python scripts/corregir_timestamps.py    # corrige timestamps inconsistentes
```

`renormalizar_db.py` puede tardar varios minutos (26k variantes × fuzzy match contra ~25k productos). El caché del Normalizer ayuda para nombres repetidos.

## Pitfalls conocidos

- **Correr `--source <fuente>` solo** inserta precios solo para esa fuente con la fecha de hoy. Si el resto tiene datos de ayer, las queries de `latest` siguen funcionando (usan max por fuente, no max global). Sin embargo el **carrito óptimo y comparaciones cruzadas solo muestran productos presentes en el último día de CADA fuente** — si dos fuentes tienen fechas distintas, sus productos sí se comparan entre sí.
- **Encombo** tiene delays anti-ban altos; usar `--limit` en desarrollo.
- **Cambio de HTML en scrapers**: La Anónima y Encombo pueden romper por cambios de selectores CSS. Día y Carrefour usan API REST y son más estables.
- **Fuzzy matching lento** en el primer scrape de una fuente grande (Anónima ~7500 productos): el normalizer hace fuzzy contra todos los productos en DB. El caché in-memory lo mitiga para runs posteriores en la misma sesión.
