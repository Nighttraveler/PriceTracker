#!/usr/bin/env python3
"""reporter.py — Generates a static HTML price report."""

import argparse
from collections import defaultdict
from datetime import date
from pathlib import Path


def _build_price_table(db, dias):
    filas = db.get_precios_rango(dias)
    by_cat = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"registros": [], "url": ""})))
    for fila in filas:
        cat = fila["categoria"] or "Sin Categoría"
        by_cat[cat][fila["nombre_normalizado"]][fila["fuente"]]["registros"].append(
            {"precio": fila["precio"], "fecha": fila["fecha"]}
        )
        by_cat[cat][fila["nombre_normalizado"]][fila["fuente"]]["url"] = fila["url_producto"]

    rows = []
    for cat in sorted(by_cat):
        for producto, sources_data in sorted(by_cat[cat].items()):
            row = {"producto": producto, "cat": cat, "fuentes": {}}
            for fuente, data in sources_data.items():
                regs = sorted(data["registros"], key=lambda r: r["fecha"])
                precio_actual = regs[-1]["precio"]
                precio_anterior = regs[0]["precio"] if len(regs) > 1 else None
                variation = None
                if precio_anterior and precio_anterior > 0:
                    variation = round((precio_actual - precio_anterior) / precio_anterior * 100, 1)
                row["fuentes"][fuente] = {
                    "precio_actual": precio_actual,
                    "variacion_pct": variation,
                    "url": data["url"],
                }
            row["num_fuentes"] = len(row["fuentes"])
            if row["num_fuentes"] >= 2:
                row["fuente_mas_barata"] = min(row["fuentes"], key=lambda f: row["fuentes"][f]["precio_actual"])
                rows.append(row)

    rows.sort(key=lambda r: (-r["num_fuentes"], r["cat"], r["producto"]))
    fuentes = sorted({f for r in rows for f in r["fuentes"]})
    return rows, fuentes

from jinja2 import Environment, FileSystemLoader

from db import Database

TEMPLATES_DIR = Path(__file__).parent / "templates"


def generate_report(db: Database, dias: int, output: str):
    stats = db.stats()
    highlights = db.get_highlights(dias=dias, min_variacion=15.0)
    productos_multi, carrito = db.optimal_cart(top_n=20)

    filas_cat = db.savings_by_category()
    by_cat = defaultdict(dict)
    fuentes_set = set()
    for row in filas_cat:
        cat = row["categoria"] or "otros"
        fuente = row["fuente"]
        by_cat[cat][fuente] = {"avg": row["avg_precio"], "n": row["n_productos"]}
        fuentes_set.add(fuente)

    fuentes = sorted(fuentes_set)
    tabla_cat = []
    for cat, sources_data in sorted(by_cat.items()):
        cheapest_source = min(sources_data, key=lambda f: sources_data[f]["avg"])
        tabla_cat.append({"categoria": cat, "fuentes": sources_data, "mas_barata": cheapest_source})

    tabla_precios, fuentes_comparativa = _build_price_table(db, dias)

    highlights_subas = sorted(
        [h for h in highlights if h["variacion_pct"] > 0],
        key=lambda h: h["variacion_pct"],
        reverse=True,
    )
    highlights_bajas = sorted(
        [h for h in highlights if h["variacion_pct"] < 0],
        key=lambda h: h["variacion_pct"],
    )

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    template = env.get_template("reporte.html")
    html = template.render(
        fecha=date.today().strftime("%d/%m/%Y"),
        dias=dias,
        stats=stats,
        highlights_subas=highlights_subas,
        highlights_bajas=highlights_bajas,
        carrito=carrito,
        n_productos_multi=len(productos_multi),
        tabla_cat=tabla_cat,
        fuentes=fuentes,
        n_subas=len(highlights_subas),
        n_bajas=len(highlights_bajas),
        tabla_precios=tabla_precios,
        fuentes_comparativa=fuentes_comparativa,
    )

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(html, encoding="utf-8")
    print(f"Report generated: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/reportes/reporte.html")
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()
    db = Database()
    generate_report(db, args.days, args.output)
