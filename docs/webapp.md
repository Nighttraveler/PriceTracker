# Web app (`app.py` / `templates/`)

Flask with Jinja2 + Bootstrap 5.

## Routes

`/`, `/precios`, `/ahorro`, `/buscar`, `/producto/<id>`

- **`/buscar`** accepts `q` (text), `fuente` (multi-value), `cat` (multi-value) as GET params.
  The template uses chips with `onchange="this.form.submit()"` to auto-submit when filters change.
- **`/ahorro`** shows the optimal cart: the 20 products present in 2+ sources with the largest
  price difference, grouped by the cheapest source.

The queries behind these routes live in `db.py`; see the critical queries in
[database.md](database.md).
