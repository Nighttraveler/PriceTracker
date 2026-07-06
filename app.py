#!/usr/bin/env python3
"""app.py — Web dashboard for Price Tracker."""

import os
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode

from flask import Flask, render_template, request, abort, jsonify
from flask_cors import CORS

from db import Database
from top_productos import TOP_ITEMS
from cache_ext import cache
from api import api_bp

app = Flask(__name__)

CACHE_TTL = int(os.environ.get("CACHE_TTL", 4 * 3600))
cache.init_app(app, config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": CACHE_TTL})

_cors_origins = [
    o.strip()
    for o in os.environ.get("CORS_ORIGIN", "http://localhost:5173").split(",")
    if o.strip()
]
CORS(app, resources={r"/api/v1/*": {"origins": _cors_origins}})
app.register_blueprint(api_bp)


def _compute_optimal_cart(rows):
    by_product = {}
    for row in rows:
        pid = row["id"]
        if pid not in by_product:
            by_product[pid] = {
                "id": pid,
                "nombre": row["nombre_normalizado"],
                "categoria": row["categoria"],
                "fuentes": {},
            }
        by_product[pid]["fuentes"][row["fuente"]] = {
            "precio": row["precio"],
            "url": row["url_producto"],
        }

    products = list(by_product.values())

    by_source = defaultdict(list)
    for prod in products:
        if not prod["fuentes"]:
            continue
        cheapest_source = min(prod["fuentes"], key=lambda f: prod["fuentes"][f]["precio"])
        min_price = prod["fuentes"][cheapest_source]["precio"]
        max_price = max(prod["fuentes"][f]["precio"] for f in prod["fuentes"])
        by_source[cheapest_source].append({
            "id": prod["id"],
            "nombre": prod["nombre"],
            "precio": min_price,
            "url": prod["fuentes"][cheapest_source]["url"],
            "precio_max": max_price,
            "ahorro": round(max_price - min_price, 2),
            "todas_fuentes": {f: prod["fuentes"][f]["precio"] for f in prod["fuentes"]},
        })

    carrito = []
    for fuente, items in sorted(by_source.items()):
        items.sort(key=lambda i: i["precio"])
        carrito.append({
            "fuente": fuente,
            "productos": items,
            "total": round(sum(i["precio"] for i in items), 2),
            "ahorro_total": round(sum(i["ahorro"] for i in items), 2),
        })

    return products, carrito

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "precios.db")


def get_db() -> Database:
    return Database(DB_PATH)


@app.route("/")
@cache.cached(timeout=CACHE_TTL, query_string=True)
def index():
    db = get_db()
    stats = db.stats()
    dias = int(request.args.get("dias", 7))
    top_baratos = db.get_top_baratos(TOP_ITEMS)
    all_highlights = db.get_highlights(dias=dias, min_variacion=5.0)
    by_fuente = defaultdict(lambda: {"subas": [], "bajas": []})
    for h in all_highlights:
        key = "subas" if h["variacion_pct"] > 0 else "bajas"
        by_fuente[h["fuente"]][key].append(h)
    fuentes = [f["nombre"] for f in stats["fuentes"]]
    highlights_por_fuente = [
        {
            "fuente": f,
            "subas": sorted(by_fuente[f]["subas"], key=lambda x: x["variacion_pct"], reverse=True)[:50],
            "bajas": sorted(by_fuente[f]["bajas"], key=lambda x: x["variacion_pct"])[:50],
        }
        for f in fuentes
    ]
    return render_template(
        "index.html",
        stats=stats,
        top_baratos=top_baratos,
        highlights_por_fuente=highlights_por_fuente,
        dias=dias,
    )


PER_PAGE = 50

@app.route("/precios")
@cache.cached(timeout=CACHE_TTL, query_string=True)
def precios():
    db = get_db()
    dias = int(request.args.get("dias", 7))
    page = max(1, int(request.args.get("page", 1)))
    cat_filter = request.args.get("cat", "")

    filas = db.get_precios_rango(dias)
    all_productos_map = {p["nombre_normalizado"]: p["id"] for p in db.get_all_productos()}

    by_cat = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"registros": [], "url": ""})))
    for fila in filas:
        cat = fila["categoria"] or "Sin Categoría"
        by_cat[cat][fila["nombre_normalizado"]][fila["fuente"]]["registros"].append(
            {"precio": fila["precio"], "fecha": fila["fecha"]}
        )
        by_cat[cat][fila["nombre_normalizado"]][fila["fuente"]]["url"] = fila["url_producto"]

    # Build flat sorted list: multi-source products first, then alpha
    all_rows = []
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
            row["producto_id"] = all_productos_map.get(producto)
            # Pre-compute cheapest source (only meaningful with 2+ sources)
            if row["num_fuentes"] >= 2:
                row["fuente_mas_barata"] = min(
                    row["fuentes"], key=lambda f: row["fuentes"][f]["precio_actual"]
                )
            else:
                row["fuente_mas_barata"] = None
            all_rows.append(row)

    all_rows.sort(key=lambda r: (-r["num_fuentes"], r["cat"], r["producto"]))

    categorias_list = sorted(by_cat.keys())
    fuentes_all = sorted({f for r in all_rows for f in r["fuentes"]})

    # Category filter
    if cat_filter and cat_filter in by_cat:
        filtered_rows = [r for r in all_rows if r["cat"] == cat_filter]
    else:
        cat_filter = ""
        filtered_rows = all_rows

    total = len(filtered_rows)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = min(page, total_pages)
    page_rows = filtered_rows[(page - 1) * PER_PAGE: page * PER_PAGE]

    return render_template(
        "precios.html",
        filas=page_rows,
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

    # Group by source for Chart.js datasets
    by_source = defaultdict(list)
    fechas_set = set()
    for row in historial:
        by_source[row["fuente"]].append({"fecha": row["fecha"], "precio": row["precio"]})
        fechas_set.add(row["fecha"])

    fechas = sorted(fechas_set)
    datasets = []
    colores = {"dia": "#fbc531", "anonima": "#e84118", "encombo": "#00a8ff", "carrefour": "#004A96"}
    for fuente, datos in sorted(by_source.items()):
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
@cache.cached(timeout=CACHE_TTL)
def ahorro():
    db = get_db()
    filas_cat = db.savings_by_category()
    productos_multi, carrito = db.optimal_cart(top_n=20)

    # Group by category → source
    by_cat = defaultdict(dict)
    fuentes_set = set()
    for row in filas_cat:
        cat = row["categoria"] or "otros"
        fuente = row["fuente"]
        by_cat[cat][fuente] = {
            "avg": row["avg_precio"],
            "min": row["min_precio"],
            "max": row["max_precio"],
            "n": row["n_productos"],
        }
        fuentes_set.add(fuente)

    fuentes = sorted(fuentes_set)
    tabla_cat = []
    for cat, sources_data in sorted(by_cat.items()):
        if not sources_data:
            continue
        mas_barata = min(sources_data, key=lambda f: sources_data[f]["avg"])
        tabla_cat.append({
            "categoria": cat,
            "fuentes": sources_data,
            "mas_barata": mas_barata,
        })

    return render_template(
        "ahorro.html",
        tabla_cat=tabla_cat,
        fuentes=fuentes,
        carrito=carrito,
        n_productos_multi=len(productos_multi),
    )


@app.route("/buscar")
@cache.cached(timeout=CACHE_TTL // 2, query_string=True)
def buscar():
    db = get_db()
    q = request.args.get("q", "").strip()
    fuentes_sel = request.args.getlist("fuente")
    cats_sel = request.args.getlist("cat")
    page = max(1, int(request.args.get("page", 1)))

    all_fuentes = db.get_all_fuentes()
    all_cats = db.get_all_categorias()

    todos = []
    buscado = bool(q or fuentes_sel or cats_sel)
    if buscado:
        todos = db.buscar_productos(
            q=q,
            fuentes=fuentes_sel or None,
            categorias=cats_sel or None,
            max_productos=500,
        )

    total = len(todos)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = min(page, total_pages)
    resultados = todos[(page - 1) * PER_PAGE: page * PER_PAGE]

    fuentes_cols = sorted({f for p in todos for f in p["fuentes"]})
    params = [("q", q)] + [("fuente", f) for f in fuentes_sel] + [("cat", c) for c in cats_sel]
    base_url = "/buscar?" + urlencode(params) + "&page="

    return render_template(
        "buscar.html",
        q=q,
        fuentes_sel=fuentes_sel,
        cats_sel=cats_sel,
        all_fuentes=all_fuentes,
        all_cats=all_cats,
        resultados=resultados,
        fuentes_cols=fuentes_cols,
        buscado=buscado,
        page=page,
        total_pages=total_pages,
        total=total,
        per_page=PER_PAGE,
        base_url=base_url,
    )


@app.route("/carrito")
def carrito_page():
    return render_template("carrito.html")


CARRITO_MODAL_PER_PAGE = 10


@app.route("/api/buscar_carrito")
def api_buscar_carrito():
    q = request.args.get("q", "").strip()
    page = max(1, int(request.args.get("page", 1)))
    per_page = max(1, min(50, int(request.args.get("per_page", CARRITO_MODAL_PER_PAGE))))

    db = get_db()
    todos = db.buscar_productos(q=q, max_productos=200)
    todos.sort(key=lambda p: min(f["precio"] for f in p["fuentes"].values()) if p["fuentes"] else float("inf"))

    total = len(todos)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    items = todos[(page - 1) * per_page: page * per_page]

    return jsonify({
        "resultados": items,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "per_page": per_page,
    })


@app.route("/api/carrito", methods=["POST"])
def api_carrito():
    data = request.get_json() or {}
    raw_ids = data.get("ids", [])
    ids = []
    for i in raw_ids:
        try:
            n = int(i)
            if n > 0:
                ids.append(n)
        except (ValueError, TypeError):
            pass
    ids = list(dict.fromkeys(ids))  # deduplicate preserving order

    if not ids:
        return jsonify({"productos": [], "carrito": [], "fuentes": [], "no_encontrados": []})

    db = get_db()
    rows = db.get_precios_carrito(ids)
    products, carrito = _compute_optimal_cart(rows)
    fuentes = sorted({f for p in products for f in p["fuentes"]})
    found_ids = {p["id"] for p in products}
    no_encontrados = [i for i in ids if i not in found_ids]

    return jsonify({
        "productos": products,
        "carrito": carrito,
        "fuentes": fuentes,
        "no_encontrados": no_encontrados,
    })


@app.route("/admin/cache/clear", methods=["POST"])
def clear_cache():
    cache.clear()
    return jsonify({"ok": True, "message": "Cache cleared"})


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Price Tracker Web Dashboard")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=args.debug)
