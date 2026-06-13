## Context

The codebase has ~160+ Spanish text items across Python files and templates, accumulated over the project's lifetime. This pass translates them to English without touching behavior, DB schema, or URL routes.

Three categories of Spanish text require different handling:

1. **Safe to translate freely**: comments, docstrings, log messages, print statements, local variable names, function names not tied to DB or external contracts.
2. **Translate identifiers carefully**: function/variable names that are passed to templates as Jinja2 context variables must be renamed consistently across `app.py` and every template that references them.
3. **Must stay in Spanish**: CATEGORIAS keyword lists (match against Spanish product names), product labels in `top_productos.py` (Argentine market names), URL routes (breaking change), CATEGORIAS dict keys (stored in DB `categoria` column).

## Goals / Non-Goals

**Goals:**
- All comments, docstrings, log/print messages in English.
- All static UI strings in templates in English.
- Function and variable names in English where safe to rename.

**Non-Goals:**
- `templates/` UI strings — the app is for Spanish-speaking users; all user-facing copy stays in Spanish.
- URL routes (`/ahorro`, `/buscar`, `/carrito`) — not renamed.
- `CATEGORIAS` keys and Spanish keyword lists — not translated.
- Product category labels in `top_productos.py` — not translated.
- DB column names — no migration.
- Any behavioral change whatsoever.

## Decisions

**Rename Jinja2 context variables passed from `app.py` to templates** — but only where the rename can be done atomically (same variable updated in `app.py` render call and in every template that uses it). If a variable name maps directly to a DB column alias in a SQL query result dict, leave it alone to avoid aliasing gymnastics. Example: `variacion_pct` comes directly from SQL; renaming it means aliasing in every query — not worth it for this pass.

**Rename Python functions and local variables** — straightforward, no cross-file contract. `_build_tabla_precios` → `_build_price_table`, `generar_reporte` → `generate_report`, `fuente_nombre` → `source_name`, etc.

**Do not rename `CATEGORIAS`** — its keys (`"lacteos"`, `"carnes"`, etc.) are the values stored in the `productos.categoria` DB column. A rename requires a data migration (UPDATE on ~25k rows). Deferred to a future migration change.

**`top_productos.py` labels stay in Spanish** — they're user-facing names for Argentine product categories used in the "TOP canasta básica" section. Translating to "Noodles 500g" / "Milk 1L" would be jarring for an Argentine audience.

## Risks / Trade-offs

- **Jinja2 variable mismatch**: if a template variable is renamed in `app.py` but missed in a template (or vice versa), Flask renders a blank or throws `UndefinedError`. Mitigation: run the app and load every page after each group of template changes.
- **Test references to renamed functions**: tests that call `limpiar_precio`, `detectar_categoria`, etc. by name must be updated in lockstep with the rename. Mitigation: run `pytest tests/ -m "not integration"` after each file group.
- **Scope creep**: it's tempting to also fix URL routes or rename CATEGORIAS. Explicitly out of scope — flag and defer.
