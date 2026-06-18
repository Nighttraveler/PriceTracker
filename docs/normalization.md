# Normalization

`normalizer.py` decides whether a new name corresponds to an existing product or creates a new one,
and assigns it a category.

## Fuzzy matching — `_normalizar_para_match()`

Matching uses `rapidfuzz.fuzz.token_sort_ratio` with a **threshold of 98**. Key rule: if the numbers
in the names differ, the score is forced to 0 (prevents merging "leche 1L" with "leche 200ml").
It has an in-memory per-session cache.

Before comparing, both names pass through `_normalizar_para_match()` (this does not affect the names
stored in the DB):

- `cc` → `ml` (1 cc = 1 ml; different sources use both notations)
- `grs` → `g`
- `"400 ml"` → `"400ml"` (joins number+unit into a single token so they don't differ)
- Strips pure connectors: `{"con", "y", "x"}` (noise in product descriptions)

Without this, "Acondicionador Dove Vitamina A+E 400ml" and "Acondicionador con Vitamina A y E Dove x
400 cc" scored 88 (< threshold 98) and were stored as distinct products.

> If you change `UMBRAL` or `_normalizar_para_match`, re-run matching with
> `scripts/renormalizar_db.py` (see [maintenance.md](maintenance.md)).

## Categories — `detectar_categoria()`

Applies different rules based on the keyword's length:

- **Multi-word**: substring match against the full name
- **Word ≥5 chars**: prefix match (covers plurals: "galletita" matches "galletitas")
- **Word <5 chars**: exact match (prevents "te" → "detergente")

Order in `CATEGORIAS` matters: the most specific ones go first.

- `higiene` before `condimentos` (prevents "romero"/"jengibre" in shampoos from winning)
- `mascotas` before `carnes` (prevents "alimento para perro sabor carne" → carnes)
- `panificados` before `carnes` (prevents "baguetin con jamón" → carnes)

> If you change category rules, re-run `scripts/renormalizar_categorias.py`
> (see [maintenance.md](maintenance.md)).
