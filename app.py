#!/usr/bin/env python3
"""app.py — Dashboard web para Price Tracker."""

import os
from collections import defaultdict
from pathlib import Path

from flask import Flask, render_template, request, abort

from db import Database

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "precios.db")


def get_db() -> Database:
    return Database(DB_PATH)


@app.route("/")
def index():
    db = get_db()
    stats = db.stats()
    dias = int(request.args.get("dias", 7))
    highlights = db.get_highlights(dias=dias, min_variacion=5.0)
    return render_template("index.html", stats=stats, highlights=highlights, dias=dias)


PER_PAGE = 50

@app.route("/precios")
def precios():
    db = get_db()
    dias = int(request.args.get("dias", 7))
    page = max(1, int(request.args.get("page", 1)))
    cat_filter = request.args.get("cat", "")

    filas = db.get_precios_rango(dias)
    all_productos_map = {p["nombre_normalizado"]: p["id"] for p in db.get_all_productos()}

    por_cat = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"registros": [], "url": ""})))
    for fila in filas:
        cat = fila["categoria"] or "Sin Categoría"
        por_cat[cat][fila["nombre_normalizado"]][fila["fuente"]]["registros"].append(
            {"precio": fila["precio"], "fecha": fila["fecha"]}
        )
        por_cat[cat][fila["nombre_normalizado"]][fila["fuente"]]["url"] = fila["url_producto"]

    # Build flat sorted list: multi-source products first, then alpha
    todas_las_filas = []
    for cat in sorted(por_cat):
        for producto, fuentes_data in sorted(por_cat[cat].items()):
            row = {"producto": producto, "cat": cat, "fuentes": {}}
            for fuente, data in fuentes_data.items():
                regs = sorted(data["registros"], key=lambda r: r["fecha"])
                precio_actual = regs[-1]["precio"]
                precio_anterior = regs[0]["precio"] if len(regs) > 1 else None
                variacion = None
                if precio_anterior and precio_anterior > 0:
                    variacion = round((precio_actual - precio_anterior) / precio_anterior * 100, 1)
                row["fuentes"][fuente] = {
                    "precio_actual": precio_actual,
                    "variacion_pct": variacion,
                    "url": data["url"],
                }
            row["num_fuentes"] = len(row["fuentes"])
            row["producto_id"] = all_productos_map.get(producto)
            # Pre-compute cheapest fuente (only meaningful with 2+ fuentes)
            if row["num_fuentes"] >= 2:
                row["fuente_mas_barata"] = min(
                    row["fuentes"], key=lambda f: row["fuentes"][f]["precio_actual"]
                )
            else:
                row["fuente_mas_barata"] = None
            todas_las_filas.append(row)

    todas_las_filas.sort(key=lambda r: (-r["num_fuentes"], r["cat"], r["producto"]))

    categorias_list = sorted(por_cat.keys())
    fuentes_all = sorted({f for r in todas_las_filas for f in r["fuentes"]})

    # Category filter
    if cat_filter and cat_filter in por_cat:
        filas_filtradas = [r for r in todas_las_filas if r["cat"] == cat_filter]
    else:
        cat_filter = ""
        filas_filtradas = todas_las_filas

    total = len(filas_filtradas)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = min(page, total_pages)
    filas_pagina = filas_filtradas[(page - 1) * PER_PAGE: page * PER_PAGE]

    return render_template(
        "precios.html",
        filas=filas_pagina,
        fuentes=fuentes_all,
        categorias_list=categorias_list,
        cat_filter=cat_filter,
        dias=dias,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@app.route("/producto/<int:producto_id>")
def producto(producto_id):
    db = get_db()
    prod = db.get_producto_by_id(producto_id)
    if not prod:
        abort(404)
    dias = int(request.args.get("dias", 30))
    historial = db.get_historial_producto(producto_id, dias=dias)

    # Organizar por fuente para Chart.js
    por_fuente = defaultdict(list)
    fechas_set = set()
    for row in historial:
        por_fuente[row["fuente"]].append({"fecha": row["fecha"], "precio": row["precio"]})
        fechas_set.add(row["fecha"])

    fechas = sorted(fechas_set)
    datasets = []
    colores = {"dia": "#fbc531", "anonima": "#e84118", "encombo": "#00a8ff", "carrefour": "#004A96"}
    for fuente, datos in sorted(por_fuente.items()):
        precio_por_fecha = {d["fecha"]: d["precio"] for d in datos}
        dataset = {
            "label": fuente.title(),
            "color": colores.get(fuente, "#7f8c8d"),
            "data": [precio_por_fecha.get(f) for f in fechas],
        }
        datasets.append(dataset)

    variantes = db.get_variantes_producto(producto_id)

    return render_template(
        "producto.html",
        prod=prod,
        fechas=fechas,
        datasets=datasets,
        dias=dias,
        variantes=variantes,
    )


@app.route("/ahorro")
def ahorro():
    db = get_db()
    filas_cat = db.get_ahorro_por_categoria()
    comparacion = db.get_comparacion_cruzada()

    # Organizar por categoría → fuente
    por_cat = defaultdict(dict)
    fuentes_set = set()
    for row in filas_cat:
        cat = row["categoria"] or "otros"
        fuente = row["fuente"]
        por_cat[cat][fuente] = {
            "avg": row["avg_precio"],
            "min": row["min_precio"],
            "max": row["max_precio"],
            "n": row["n_productos"],
        }
        fuentes_set.add(fuente)

    # Para cada categoría, encontrar la fuente más barata por promedio
    fuentes = sorted(fuentes_set)
    tabla_cat = []
    for cat, fuentes_data in sorted(por_cat.items()):
        if not fuentes_data:
            continue
        mas_barata = min(fuentes_data, key=lambda f: fuentes_data[f]["avg"])
        tabla_cat.append({
            "categoria": cat,
            "fuentes": fuentes_data,
            "mas_barata": mas_barata,
        })

    return render_template(
        "ahorro.html",
        tabla_cat=tabla_cat,
        fuentes=fuentes,
        comparacion=comparacion,
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Price Tracker Web Dashboard")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=args.debug)
