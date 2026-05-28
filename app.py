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


@app.route("/precios")
def precios():
    db = get_db()
    dias = int(request.args.get("dias", 7))
    filas = db.get_precios_rango(dias)

    por_cat = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"registros": [], "url": ""})))
    for fila in filas:
        cat = fila["categoria"] or "Sin Categoría"
        prod = fila["nombre_normalizado"]
        fuente = fila["fuente"]
        entry = por_cat[cat][prod][fuente]
        entry["registros"].append({"precio": fila["precio"], "fecha": fila["fecha"]})
        entry["url"] = fila["url_producto"]

    categorias_data = {}
    for cat, productos in sorted(por_cat.items()):
        tabla = []
        for producto, fuentes in sorted(productos.items()):
            fila_out = {"producto": producto, "fuentes": {}, "producto_id": None}
            for fuente, data in fuentes.items():
                regs = sorted(data["registros"], key=lambda r: r["fecha"])
                precio_actual = regs[-1]["precio"]
                precio_anterior = regs[0]["precio"] if len(regs) > 1 else None
                variacion = None
                if precio_anterior and precio_anterior > 0:
                    variacion = round((precio_actual - precio_anterior) / precio_anterior * 100, 1)
                fila_out["fuentes"][fuente] = {
                    "precio_actual": precio_actual,
                    "variacion_pct": variacion,
                    "url": data["url"],
                }
            fila_out["num_fuentes"] = len(fila_out["fuentes"])
            tabla.append(fila_out)
        tabla.sort(key=lambda x: (-x["num_fuentes"], x["producto"]))
        categorias_data[cat] = tabla

    # Enrich with producto_id for history links
    all_productos = {p["nombre_normalizado"]: p["id"] for p in db.get_all_productos()}
    for tabla in categorias_data.values():
        for row in tabla:
            row["producto_id"] = all_productos.get(row["producto"])

    # Pre-compute fuentes present per category for template simplicity
    categorias_con_fuentes = {}
    for cat, tabla in categorias_data.items():
        fuentes_cat = sorted({f for r in tabla for f in r["fuentes"]})
        categorias_con_fuentes[cat] = {"tabla": tabla, "fuentes": fuentes_cat}

    return render_template("precios.html", categorias=categorias_con_fuentes, dias=dias)


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
    colores = {"dia": "#fbc531", "anonima": "#e84118", "encombo": "#00a8ff"}
    for fuente, datos in sorted(por_fuente.items()):
        precio_por_fecha = {d["fecha"]: d["precio"] for d in datos}
        dataset = {
            "label": fuente.title(),
            "color": colores.get(fuente, "#7f8c8d"),
            "data": [precio_por_fecha.get(f) for f in fechas],
        }
        datasets.append(dataset)

    return render_template(
        "producto.html",
        prod=prod,
        fechas=fechas,
        datasets=datasets,
        dias=dias,
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Price Tracker Web Dashboard")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=args.debug)
