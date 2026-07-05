"""api.py — /api/v1/* JSON endpoints for the React frontend."""

import os
from collections import defaultdict

from flask import Blueprint, jsonify, request, abort

from db import Database
from top_productos import TOP_ITEMS
from cache_ext import cache

CACHE_TTL = int(os.environ.get("CACHE_TTL", 4 * 3600))

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")

PER_PAGE = 50
CARRITO_MODAL_PER_PAGE = 10
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "precios.db")


def _get_db() -> Database:
    return Database(DB_PATH)


# ── Shared serializers ────────────────────────────────────────────────────────

def build_precios_matrix(filas, all_productos_map):
    """Build the product × source price matrix used by /precios and /api/v1/precios."""
    by_cat: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"registros": [], "url": ""})))
    for fila in filas:
        cat = fila["categoria"] or "Sin Categoría"
        by_cat[cat][fila["nombre_normalizado"]][fila["fuente"]]["registros"].append(
            {"precio": fila["precio"], "fecha": fila["fecha"]}
        )
        by_cat[cat][fila["nombre_normalizado"]][fila["fuente"]]["url"] = fila["url_producto"]

    all_rows = []
    for cat in sorted(by_cat):
        for producto, sources_data in sorted(by_cat[cat].items()):
            row: dict = {"producto": producto, "cat": cat, "fuentes": {}}
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
            row["fuente_mas_barata"] = (
                min(row["fuentes"], key=lambda f: row["fuentes"][f]["precio_actual"])
                if row["num_fuentes"] >= 2
                else None
            )
            all_rows.append(row)

    all_rows.sort(key=lambda r: (-r["num_fuentes"], r["cat"], r["producto"]))
    return all_rows, by_cat


def build_producto_datasets(historial):
    """Build chart datasets for /producto/<id> and /api/v1/producto/<id>."""
    by_source: dict = defaultdict(list)
    fechas_set: set = set()
    for row in historial:
        by_source[row["fuente"]].append({"fecha": row["fecha"], "precio": row["precio"]})
        fechas_set.add(row["fecha"])

    fechas = sorted(fechas_set)
    colores = {"dia": "#e67e22", "anonima": "#dc3545", "encombo": "#0d6efd", "carrefour": "#004A96"}
    datasets = []
    for fuente, datos in sorted(by_source.items()):
        precio_por_fecha = {d["fecha"]: d["precio"] for d in datos}
        datasets.append({
            "label": fuente.title(),
            "color": colores.get(fuente, "#7f8c8d"),
            "data": [precio_por_fecha.get(f) for f in fechas],
        })
    return fechas, datasets


def compute_optimal_cart(rows):
    """Compute optimal cart from raw price rows. Shared with app.py."""
    by_product: dict = {}
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
    by_source: dict = defaultdict(list)
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


# ── Endpoints ─────────────────────────────────────────────────────────────────

@api_bp.get("/health")
def api_health():
    try:
        db = _get_db()
        db._scalar("SELECT 1")
        return jsonify({"status": "ok"})
    except Exception:
        return jsonify({"status": "error"}), 503


@api_bp.get("/dashboard")
@cache.cached(timeout=CACHE_TTL, query_string=True)
def api_dashboard():
    db = _get_db()
    dias = int(request.args.get("dias", 7))
    stats = db.stats()
    top_baratos = db.get_top_baratos(TOP_ITEMS)
    all_highlights = db.get_highlights(dias=dias, min_variacion=5.0)

    by_fuente: dict = defaultdict(lambda: {"subas": [], "bajas": []})
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

    return jsonify({
        "stats": stats,
        "top_baratos": top_baratos,
        "highlights": highlights_por_fuente,
        "dias": dias,
    })


@api_bp.get("/precios")
@cache.cached(timeout=CACHE_TTL, query_string=True)
def api_precios():
    db = _get_db()
    dias = int(request.args.get("dias", 7))
    page = max(1, int(request.args.get("page", 1)))
    cat_filter = request.args.get("cat", "")

    filas = db.get_precios_rango(dias)
    all_productos_map = {p["nombre_normalizado"]: p["id"] for p in db.get_all_productos()}
    all_rows, by_cat = build_precios_matrix(filas, all_productos_map)

    categorias_list = sorted(by_cat.keys())
    fuentes_all = sorted({f for r in all_rows for f in r["fuentes"]})

    if cat_filter and cat_filter in by_cat:
        filtered_rows = [r for r in all_rows if r["cat"] == cat_filter]
    else:
        cat_filter = ""
        filtered_rows = all_rows

    total = len(filtered_rows)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = min(page, total_pages)
    page_rows = filtered_rows[(page - 1) * PER_PAGE: page * PER_PAGE]

    return jsonify({
        "filas": page_rows,
        "fuentes": fuentes_all,
        "categorias_list": categorias_list,
        "cat_filter": cat_filter,
        "dias": dias,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    })


@api_bp.get("/producto/<int:producto_id>")
def api_producto(producto_id: int):
    db = _get_db()
    prod = db.get_producto_by_id(producto_id)
    if not prod:
        abort(404)
    dias = int(request.args.get("dias", 30))
    historial = db.get_historial_producto(producto_id, dias=dias)
    fechas, datasets = build_producto_datasets(historial)
    variantes = db.get_variantes_producto(producto_id)

    return jsonify({
        "prod": prod,
        "fechas": fechas,
        "datasets": datasets,
        "variantes": variantes,
        "dias": dias,
    })


@api_bp.get("/ahorro")
@cache.cached(timeout=CACHE_TTL)
def api_ahorro():
    db = _get_db()
    filas_cat = db.savings_by_category()
    productos_multi, carrito = db.optimal_cart(top_n=20)

    by_cat: dict = defaultdict(dict)
    fuentes_set: set = set()
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

    return jsonify({
        "tabla_cat": tabla_cat,
        "fuentes": fuentes,
        "carrito": carrito,
        "n_productos_multi": len(productos_multi),
    })


@api_bp.get("/buscar")
@cache.cached(timeout=CACHE_TTL // 2, query_string=True)
def api_buscar():
    db = _get_db()
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

    return jsonify({
        "q": q,
        "fuentes_sel": fuentes_sel,
        "cats_sel": cats_sel,
        "all_fuentes": all_fuentes,
        "all_cats": all_cats,
        "resultados": resultados,
        "fuentes_cols": fuentes_cols,
        "buscado": buscado,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "per_page": PER_PAGE,
    })


@api_bp.get("/buscar_carrito")
def api_buscar_carrito():
    q = request.args.get("q", "").strip()
    page = max(1, int(request.args.get("page", 1)))
    per_page = max(1, min(50, int(request.args.get("per_page", CARRITO_MODAL_PER_PAGE))))

    db = _get_db()
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


@api_bp.post("/carrito")
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
    ids = list(dict.fromkeys(ids))

    if not ids:
        return jsonify({"productos": [], "carrito": [], "fuentes": [], "no_encontrados": []})

    db = _get_db()
    rows = db.get_precios_carrito(ids)
    products, carrito = compute_optimal_cart(rows)
    fuentes = sorted({f for p in products for f in p["fuentes"]})
    found_ids = {p["id"] for p in products}
    no_encontrados = [i for i in ids if i not in found_ids]

    return jsonify({
        "productos": products,
        "carrito": carrito,
        "fuentes": fuentes,
        "no_encontrados": no_encontrados,
    })
