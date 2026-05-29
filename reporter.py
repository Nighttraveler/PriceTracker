#!/usr/bin/env python3
"""reporter.py — Genera reporte HTML estático de precios."""

import argparse
from collections import defaultdict
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from db import Database

TEMPLATES_DIR = Path(__file__).parent / "templates"


def generar_reporte(db: Database, dias: int, output: str):
    stats = db.stats()
    highlights = db.get_highlights(dias=dias, min_variacion=15.0)
    productos_multi, carrito = db.get_carrito_optimo(top_n=20)

    filas_cat = db.get_ahorro_por_categoria()
    por_cat = defaultdict(dict)
    fuentes_set = set()
    for row in filas_cat:
        cat = row["categoria"] or "otros"
        fuente = row["fuente"]
        por_cat[cat][fuente] = {"avg": row["avg_precio"], "n": row["n_productos"]}
        fuentes_set.add(fuente)

    fuentes = sorted(fuentes_set)
    tabla_cat = []
    for cat, fuentes_data in sorted(por_cat.items()):
        mas_barata = min(fuentes_data, key=lambda f: fuentes_data[f]["avg"])
        tabla_cat.append({"categoria": cat, "fuentes": fuentes_data, "mas_barata": mas_barata})

    n_subas = sum(1 for h in highlights if h["variacion_pct"] > 0)
    n_bajas = sum(1 for h in highlights if h["variacion_pct"] < 0)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    template = env.get_template("reporte.html")
    html = template.render(
        fecha=date.today().strftime("%d/%m/%Y"),
        dias=dias,
        stats=stats,
        highlights=highlights,
        carrito=carrito,
        n_productos_multi=len(productos_multi),
        tabla_cat=tabla_cat,
        fuentes=fuentes,
        n_subas=n_subas,
        n_bajas=n_bajas,
    )

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(html, encoding="utf-8")
    print(f"Reporte generado: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/reportes/reporte.html")
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()
    db = Database()
    generar_reporte(db, args.days, args.output)
