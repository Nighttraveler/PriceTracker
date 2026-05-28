#!/usr/bin/env python3
"""reporter.py — Genera reporte HTML semanal de precios."""

import argparse
from collections import defaultdict
from datetime import date
from db import Database

def generar_reporte(db: Database, dias: int, output: str):
    filas = db.get_precios_rango(dias)

    # Agrupar por categoria -> producto -> fuente
    por_cat = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"registros": [], "url": ""})))

    for fila in filas:
        cat = fila["categoria"] or "Sin Categoría"
        prod = fila["nombre_normalizado"]
        fuente = fila["fuente"]
        
        entry = por_cat[cat][prod][fuente]
        entry["registros"].append({"precio": fila["precio"], "fecha": fila["fecha"]})
        entry["url"] = fila["url_producto"] # Se actualiza con la última url encontrada

    # Calcular highlights y estructura de tablas
    highlights = []
    categorias_data = {}

    for cat, productos in sorted(por_cat.items()):
        tabla_data = []
        for producto, fuentes in sorted(productos.items()):
            fila = {"producto": producto, "fuentes": {}}
            precios_todos = []

            for fuente, data in fuentes.items():
                registros = data["registros"]
                url = data["url"]
                
                registros_sorted = sorted(registros, key=lambda r: r["fecha"])
                precio_actual = registros_sorted[-1]["precio"]
                precio_anterior = registros_sorted[0]["precio"] if len(registros_sorted) > 1 else None

                variacion_pct = None
                if precio_anterior and precio_anterior > 0:
                    variacion_pct = ((precio_actual - precio_anterior) / precio_anterior) * 100

                fila["fuentes"][fuente] = {
                    "precio_actual": precio_actual,
                    "variacion_pct": variacion_pct,
                    "url": url
                }
                precios_todos.append(precio_actual)

                if variacion_pct and abs(variacion_pct) >= 15:
                    highlights.append({
                        "producto": producto,
                        "fuente": fuente,
                        "variacion": variacion_pct,
                        "precio": precio_actual,
                    })

            if precios_todos:
                fila["num_fuentes"] = len(fila["fuentes"])
                tabla_data.append(fila)
        
        # Ordenar productos por cantidad de fuentes (desc) y nombre (asc)
        tabla_data.sort(key=lambda x: (-x["num_fuentes"], x["producto"]))
        categorias_data[cat] = tabla_data

    highlights.sort(key=lambda h: abs(h["variacion"]), reverse=True)
    html = _render_html(categorias_data, highlights, dias)

    with open(output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Reporte generado: {output}")

def _render_html(categorias_data, highlights, dias):
    hoy = date.today().strftime("%d/%m/%Y")
    n_productos = sum(len(cat) for cat in categorias_data.values())
    n_subas = sum(1 for h in highlights if h["variacion"] > 0)
    n_bajas = sum(1 for h in highlights if h["variacion"] < 0)

    # Filas de highlights
    rows_hl = ""
    for h in highlights[:20]:
        color = "#e74c3c" if h["variacion"] > 0 else "#27ae60"
        signo = "▲" if h["variacion"] > 0 else "▼"
        rows_hl += f"""<tr><td>{h['producto']}</td><td>{h['fuente']}</td><td>$ {h['precio']:,.2f}</td><td style="color:{color};font-weight:bold">{signo} {abs(h['variacion']):.1f}%</td></tr>"""

    # Data para grafico de torta (fuente mas barata por categoria)
    stats_baratas = defaultdict(lambda: defaultdict(int))
    # Categorias con productos en 2+ fuentes
    categorias_comparables = set()

    for cat, tabla_data in categorias_data.items():
        for row in tabla_data:
            if row["num_fuentes"] >= 2:
                categorias_comparables.add(cat)
            
            # Encontrar fuente con precio minimo
            min_precio = float('inf')
            mejor_fuente = None
            for fuente, d in row["fuentes"].items():
                if d["precio_actual"] < min_precio:
                    min_precio = d["precio_actual"]
                    mejor_fuente = fuente
            if mejor_fuente:
                stats_baratas[cat][mejor_fuente] += 1

    def _render_tab(cat, tabla_data, stats_baratas):
        stats = stats_baratas[cat]
        total = sum(stats.values())
        grafico = ""
        if total > 0:
            grafico = '<div style="display:flex; height:20px; border-radius:10px; overflow:hidden; margin:10px 0;">'
            colores = {"dia": "#fbc531", "anonima": "#e84118", "encombo": "#00a8ff"}
            for f, count in stats.items():
                pct = (count / total) * 100
                color = colores.get(f, "#7f8c8d")
                grafico += f'<div style="width:{pct}%; background:{color};" title="{f}: {count}"></div>'
            grafico += '</div>'
        
        fuentes_set = sorted({f for row in tabla_data for f in row["fuentes"]})
        headers = "".join(f"<th>{f.title()}</th>" for f in fuentes_set)
        rows_tabla = ""
        for row in tabla_data:
            opacity = "1.0" if row["num_fuentes"] > 1 else "0.7"
            celdas = ""
            for fuente in fuentes_set:
                if fuente in row["fuentes"]:
                    d = row["fuentes"][fuente]
                    v = d["variacion_pct"]
                    url = d["url"]
                    badge = f' <span style="color:{"#e74c3c" if v>0 else "#27ae60"};font-size:0.8em">{"▲" if v>0 else "▼"}{abs(v):.0f}%</span>' if v else ""
                    celdas += f'<td><a href="{url}" target="_blank">$ {d["precio_actual"]:,.2f}</a>{badge}</td>'
                else:
                    celdas += "<td>—</td>"
            rows_tabla += f'<tr style="opacity:{opacity}"><td>{row["producto"]}</td>{celdas}</tr>'
        
        return f"""
        <section>
            <h2>{cat}</h2>
            {grafico}
            <table>
                <thead><tr><th>Producto</th>{headers}</tr></thead>
                <tbody>{rows_tabla}</tbody>
            </table>
        </section>"""

    html_secciones_comparables = ""
    html_secciones_full = ""
    
    for cat, tabla_data in sorted(categorias_data.items()):
        # Tab Full
        html_secciones_full += _render_tab(cat, tabla_data, stats_baratas)
        
        # Tab Comparables
        if cat in categorias_comparables:
            data_filtrada = [r for r in tabla_data if r["num_fuentes"] >= 2]
            html_secciones_comparables += _render_tab(cat, data_filtrada, stats_baratas)


    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hermes — Reporte de Precios {hoy}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: #f5f6fa; color: #2d3436; }}
  header {{ background: #2d3436; color: white; padding: 1.5rem 2rem; }}
  .container {{ max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
  .card {{ background: white; border-radius: 8px; padding: 1.2rem; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
  .card .num {{ font-size: 2rem; font-weight: bold; }}
  .card .label {{ font-size: 0.85rem; color: #636e72; }}
  section {{ background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
  h2 {{ font-size: 1.1rem; margin-bottom: 1rem; border-bottom: 2px solid #f5f6fa; padding-bottom: 0.5rem; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th {{ background: #f5f6fa; padding: 0.6rem 0.8rem; text-align: left; font-size: 0.8rem; text-transform: uppercase; color: #636e72; }}
  td {{ padding: 0.5rem 0.8rem; border-bottom: 1px solid #f5f6fa; }}
  a {{ color: #0984e3; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .tabs {{ margin-bottom: 2rem; }}
  .tab-btn {{ padding: 0.8rem 1.5rem; cursor: pointer; border: none; background: #dfe6e9; border-radius: 4px; font-weight: bold; }}
  .tab-btn.active {{ background: #2d3436; color: white; }}
</style>
</head>
<body>
<header>
  <h1>🐍 Hermes — Reporte de Precios</h1>
  <p>Período: últimos {dias} días · Generado el {hoy}</p>
</header>
<div class="container">
  <div class="cards">
    <div class="card"><div class="num">{n_productos}</div><div class="label">Productos</div></div>
    <div class="card"><div class="num">{n_subas}</div><div class="label">Subas >15%</div></div>
    <div class="card"><div class="num">{n_bajas}</div><div class="label">Bajas >15%</div></div>
  </div>
  <section>
    <h2>🔥 Highlights</h2>
    <table><thead><tr><th>Producto</th><th>Fuente</th><th>Precio</th><th>Variación</th></tr></thead><tbody>{rows_hl}</tbody></table>
  </section>
  
  <div class="tabs">
    <button class="tab-btn active" onclick="showTab('comparables')">Solo Comparables</button>
    <button class="tab-btn" onclick="showTab('full')">Reporte Completo</button>
  </div>
  
  <div id="comparables" class="tab-content">{html_secciones_comparables}</div>
  <div id="full" class="tab-content" style="display:none">{html_secciones_full}</div>
</div>

<script>
function showTab(tabId) {{
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById(tabId).style.display = 'block';
    event.currentTarget.classList.add('active');
}}
</script>
</body>
</html>"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/reportes/reporte.html")
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()
    db = Database()
    generar_reporte(db, args.days, args.output)
