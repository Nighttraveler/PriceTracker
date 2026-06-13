## 1. `normalizer.py`

- [x] 1.1 Translate module docstring.
- [x] 1.2 Translate all inline comments (category order rationale, matching rules, stopwords explanation). Leave Spanish keyword lists and CATEGORIAS keys untouched.
- [x] 1.3 Rename functions: `limpiar()` → `clean_name()`, `_normalizar_para_match()` → `_normalize_for_match()`, `es_combo()` → `is_combo()`, `detectar_categoria()` → `detect_category()`, `normalizar_unidad()` → `normalize_unit()`, `extraer_numeros()` → `extract_numbers()`.
- [x] 1.4 Rename constant: `UMBRAL_SIMILITUD` → `SIMILARITY_THRESHOLD`. Rename `STOPWORDS_MATCH` → `MATCH_STOPWORDS`.
- [x] 1.5 Rename `Normalizer` method: `obtener_o_crear_producto()` → `get_or_create_product()`.
- [x] 1.6 Update all callers of renamed symbols in `tracker.py`, `app.py`, `db.py`, `reporter.py`, and `scripts/`.
- [x] 1.7 Run `pytest tests/test_normalizer.py` — all tests must pass.

## 2. `app.py`

- [x] 2.1 Translate module docstring and all inline comments.
- [x] 2.2 Translate log messages and the `"message": "Caché limpiado"` JSON response string.
- [x] 2.3 Rename local variables in functions: `fuente_mas_barata` → `cheapest_source`, `por_producto` → `by_product`, `por_fuente` → `by_source`, `ahorro` → `savings`, `precio_min`/`precio_max` → `min_price`/`max_price`, `todas_fuentes` → `all_sources`, `filas_filtradas` → `filtered_rows`, `filas_pagina` → `page_rows`, `categorias_list` → `categories_list`. Leave `variacion_pct` as-is (SQL alias referenced in templates).
- [x] 2.4 Rename internal function `_compute_carrito_optimo()` → `_compute_optimal_cart()`.

## 3. `db.py`

- [x] 3.1 Translate module docstring and all inline comments (including CTE explanation comments and the "append-only" rationale).
- [x] 3.2 Translate docstrings on all methods (`_reconnect`, `_sql`, `_exec`, `_commit`, `_scalar`, `_write`, `reset_sequences`, etc.).
- [x] 3.3 Rename functions: `ahorro_por_categoria()` → `savings_by_category()`, `carrito_optimo()` → `optimal_cart()`.
- [x] 3.4 Translate the `print` output in the `__main__` block (`"Última fecha:"` etc.).
- [x] 3.5 Update callers of renamed db functions in `app.py` and `reporter.py`.

## 4. `tracker.py`, `reporter.py`, `scheduler.py`

- [x] 4.1 `tracker.py`: translate docstring, all log messages, argparse `help=` strings. Rename variables: `fuente_nombre` → `source_name`, `productos` → `products`, `insertados` → `inserted`, `fuentes` → `sources`.
- [x] 4.2 `reporter.py`: translate docstring and all inline comments. Rename functions: `_build_tabla_precios()` → `_build_price_table()`, `generar_reporte()` → `generate_report()`. Rename local variables: `por_cat` → `by_category`, `fuentes_data` → `sources_data`, `variacion` → `variation`, `fuente_mas_barata` → `cheapest_source`.
- [x] 4.3 `scheduler.py`: translate docstring, all log messages, argparse `help=` strings. Translate `DIAS_ES` mapping keys/values. Rename functions: `run_reporte()` → `run_report()`, `run_chequeo_urls()` → `run_url_check()`.
- [x] 4.4 Run `pytest tests/ -m "not integration"` — all tests must pass.

## 5. `scrapers/`

- [x] 5.1 `scrapers/base.py`: translate any Spanish comments. Rename `limpiar_precio()` → `parse_price()`.
- [x] 5.2 `scrapers/vtex_base.py`: translate module docstring, all log messages, inline comments.
- [x] 5.3 `scrapers/dia.py`: translate module docstring, category slug comments, all log messages. Keep slug strings and category names as-is (they're VTEX API values).
- [x] 5.4 `scrapers/carrefour.py`, `scrapers/anonima.py`, `scrapers/encombo.py`: translate any remaining Spanish comments or log messages.
- [x] 5.5 Update all callers of `parse_price()` (was `limpiar_precio()`) within scraper files and tests.
- [x] 5.6 Run `pytest tests/test_scrapers_unit.py tests/test_scrapers_filtering.py` — all tests must pass.

## 6. `scripts/`

- [x] 6.1 `scripts/renormalizar_db.py`: translate docstring, all print messages. Rename function: `re_normalizar_db()` → `renormalize_db()`. Rename variables: `actualizadas` → `updated`, `huerfanos` → `orphans`.
- [x] 6.2 `scripts/renormalizar_categorias.py`: translate docstring and print messages. Rename variables: `nueva_cat` → `new_cat`, `nuevo_combo` → `new_combo`, `actualizados` → `updated`.
- [x] 6.3 `scripts/chequear_urls.py`: translate docstring, all log/print messages, argparse `help=` strings. Rename: `chequear_url()` → `check_url()`, `chequear_dominio()` → `check_domain()`, `ESTADOS_DESCATALOGADO` → `DISCONTINUED_STATUSES`, `errores_red` → `network_errors`, `por_dominio` → `by_domain`.
- [x] 6.4 `scripts/corregir_timestamps.py`: translate docstring and print messages. Rename `corregir_timestamps()` → `fix_timestamps()`.
- [x] 6.5 `scripts/migrar_fechas.py`: translate print messages. Rename `migrar_fecha_timestamp()` → `migrate_fecha_to_timestamp()`.

## 7. `tests/`

- [x] 7.1 `tests/test_normalizer.py`: translate all inline comments and test docstrings. Update all calls to renamed normalizer functions (`clean_name`, `is_combo`, `detect_category`, `normalize_unit`, `_normalize_for_match`, `SIMILARITY_THRESHOLD`). Update test method names to English (e.g., `test_detectar_categoria_*` → `test_detect_category_*`).
- [x] 7.2 `tests/test_limpiar_precio.py`: translate all inline comments. Rename test methods (e.g., `test_limpiar_precio_*` → `test_parse_price_*`). Update calls to `parse_price()`.
- [x] 7.3 `tests/test_scrapers_unit.py`: translate all docstrings and inline comments. Update calls to `parse_price()`.
- [x] 7.4 Run full test suite: `pytest tests/ -m "not integration"` — all tests must pass.

## 8. Final verification

- [x] 8.1 Rebuild Docker image and restart app container.
- [x] 8.2 Load every page and confirm Spanish UI is intact and functional: `/`, `/precios`, `/buscar`, `/ahorro`, `/carrito`, `/producto/<id>`.
- [x] 8.3 Add an item to the cart from the dashboard; confirm it appears in `/carrito` and the optimal cart renders correctly.
- [x] 8.4 Run `python tracker.py --source dia --dry-run --limit 5` and confirm log output is in English.
- [x] 8.5 Run full test suite one final time: `pytest tests/ -m "not integration"`.
