#!/usr/bin/env python3
"""
db.py — Capa de acceso a la base de datos SQLite para Hermes Price Tracker.
"""

import sqlite3
import argparse
from pathlib import Path


class Database:
    def __init__(self, path: str = "data/precios.db"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")

    def init_schema(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS fuentes (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL UNIQUE,
            url_base TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY,
            nombre_normalizado TEXT NOT NULL UNIQUE,
            categoria TEXT,
            unidad TEXT,
            es_combo INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS variantes (
            id INTEGER PRIMARY KEY,
            producto_id INTEGER REFERENCES productos(id),
            fuente_id INTEGER REFERENCES fuentes(id),
            nombre_original TEXT NOT NULL,
            url_producto TEXT,
            UNIQUE(fuente_id, nombre_original)
        );

        CREATE TABLE IF NOT EXISTS precios (
            id INTEGER PRIMARY KEY,
            variante_id INTEGER REFERENCES variantes(id),
            precio REAL NOT NULL,
            fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            moneda TEXT DEFAULT 'ARS'
        );

        CREATE INDEX IF NOT EXISTS idx_precios_fecha     ON precios(fecha);
        CREATE INDEX IF NOT EXISTS idx_precios_variante  ON precios(variante_id);

        -- Composite: cubre JOIN por variante_id + filtro/orden por fecha en un solo índice
        CREATE INDEX IF NOT EXISTS idx_precios_variante_fecha ON precios(variante_id, fecha);

        -- Permite JOIN inverso productos→variantes sin full-scan de variantes
        CREATE INDEX IF NOT EXISTS idx_variantes_producto ON variantes(producto_id);

        -- Cubre GROUP BY fuente_id en el CTE max_por_fuente (ya existe via UNIQUE,
        -- pero este índice parcial es más angosto y rápido para esa query)
        CREATE INDEX IF NOT EXISTS idx_variantes_fuente  ON variantes(fuente_id);

        -- Acelera WHERE p.es_combo = 0 y el filtro de categoría en búsquedas
        CREATE INDEX IF NOT EXISTS idx_productos_combo_cat ON productos(es_combo, categoria);

        -- Permite LIKE 'término%' (starts-with) en buscar_productos
        CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre_normalizado);
        """)
        self.conn.commit()
        # Migración: agregar es_combo si la tabla existía sin esa columna
        try:
            self.conn.execute("ALTER TABLE productos ADD COLUMN es_combo INTEGER NOT NULL DEFAULT 0")
            self.conn.commit()
        except Exception:
            pass  # columna ya existe

    def get_or_create_fuente(self, nombre: str, url_base: str) -> int:
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO fuentes (nombre, url_base) VALUES (?, ?)",
            (nombre, url_base)
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id FROM fuentes WHERE nombre = ?", (nombre,)
        ).fetchone()
        return row["id"]

    def get_or_create_variante(self, producto_id: int, fuente_id: int,
                                nombre_original: str, url: str = "") -> int:
        self.conn.execute(
            """INSERT OR IGNORE INTO variantes
               (producto_id, fuente_id, nombre_original, url_producto)
               VALUES (?, ?, ?, ?)""",
            (producto_id, fuente_id, nombre_original, url)
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id FROM variantes WHERE fuente_id = ? AND nombre_original = ?",
            (fuente_id, nombre_original)
        ).fetchone()
        return row["id"]

    def insert_producto(self, nombre_normalizado: str,
                        categoria: str = None, unidad: str = None,
                        es_combo: bool = False) -> int:
        self.conn.execute(
            """INSERT OR IGNORE INTO productos
               (nombre_normalizado, categoria, unidad, es_combo) VALUES (?, ?, ?, ?)""",
            (nombre_normalizado, categoria, unidad, int(es_combo))
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id FROM productos WHERE nombre_normalizado = ?",
            (nombre_normalizado,)
        ).fetchone()
        return row["id"]

    def insertar_precio(self, variante_id: int, precio: float, fecha: str):
        self.conn.execute(
            "INSERT INTO precios (variante_id, precio, fecha) VALUES (?, ?, ?)",
            (variante_id, precio, fecha)
        )
        self.conn.commit()

    def get_all_productos(self):
        return self.conn.execute(
            "SELECT id, nombre_normalizado FROM productos"
        ).fetchall()

    def get_precios_rango(self, dias: int = 7, incluir_combos: bool = False):
        combo_filter = "" if incluir_combos else "AND p.es_combo = 0"
        return self.conn.execute(f"""
            SELECT p.nombre_normalizado, p.categoria, f.nombre as fuente,
                   pr.precio, pr.fecha, v.nombre_original, v.url_producto
            FROM precios pr
            JOIN variantes v ON pr.variante_id = v.id
            JOIN productos p ON v.producto_id = p.id
            JOIN fuentes f ON v.fuente_id = f.id
            WHERE pr.fecha >= date('now', ? || ' days')
            {combo_filter}
            ORDER BY p.nombre_normalizado, pr.fecha DESC
        """, (f"-{dias}",)).fetchall()

    def stats(self):
        stats = {
            "productos": self.conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0],
            "variantes": self.conn.execute("SELECT COUNT(*) FROM variantes").fetchone()[0],
            "precios":   self.conn.execute("SELECT COUNT(*) FROM precios").fetchone()[0],
            "fuentes":   self.conn.execute("SELECT nombre FROM fuentes").fetchall(),
            "ultima_fecha": self.conn.execute(
                "SELECT MAX(fecha) FROM precios").fetchone()[0],
        }
        return stats

    def get_variantes_producto(self, producto_id: int):
        """Devuelve una fila por fuente con la URL y nombre original de la variante."""
        return self.conn.execute("""
            SELECT f.nombre as fuente, v.url_producto, v.nombre_original
            FROM variantes v
            JOIN fuentes f ON v.fuente_id = f.id
            WHERE v.producto_id = ?
            ORDER BY f.nombre
        """, (producto_id,)).fetchall()

    def get_historial_producto(self, producto_id: int, dias: int = 90):
        return self.conn.execute("""
            SELECT f.nombre as fuente, pr.precio, date(pr.fecha) as fecha
            FROM precios pr
            JOIN variantes v ON pr.variante_id = v.id
            JOIN fuentes f ON v.fuente_id = f.id
            WHERE v.producto_id = ?
              AND pr.fecha >= date('now', ? || ' days')
            ORDER BY pr.fecha ASC
        """, (producto_id, f"-{dias}")).fetchall()

    def get_producto_by_id(self, producto_id: int):
        return self.conn.execute(
            "SELECT id, nombre_normalizado, categoria FROM productos WHERE id = ?",
            (producto_id,)
        ).fetchone()

    def get_ahorro_por_categoria(self):
        """Precio promedio por categoría y fuente (últimos precios disponibles)."""
        return self.conn.execute("""
            WITH max_por_fuente AS (
                SELECT v.fuente_id, MAX(date(pr.fecha)) AS max_fecha
                FROM precios pr JOIN variantes v ON pr.variante_id = v.id
                GROUP BY v.fuente_id
            ),
            latest AS (
                SELECT v.producto_id, v.fuente_id, pr.precio
                FROM precios pr
                JOIN variantes v ON pr.variante_id = v.id
                JOIN max_por_fuente m ON v.fuente_id = m.fuente_id
                    AND date(pr.fecha) = m.max_fecha
            )
            SELECT p.categoria, f.nombre as fuente,
                   ROUND(AVG(l.precio), 2) as avg_precio,
                   ROUND(MIN(l.precio), 2) as min_precio,
                   ROUND(MAX(l.precio), 2) as max_precio,
                   COUNT(DISTINCT l.producto_id) as n_productos
            FROM latest l
            JOIN productos p ON l.producto_id = p.id
            JOIN fuentes f ON l.fuente_id = f.id
            WHERE p.es_combo = 0
            GROUP BY p.categoria, f.nombre
            ORDER BY p.categoria, avg_precio
        """).fetchall()

    def get_carrito_optimo(self, top_n: int = 20):
        """Top N productos en 2+ fuentes. Devuelve (productos_list, carrito_list).

        carrito_list: lista ordenada por fuente, cada item tiene los productos
        que conviene comprar ahí (los más baratos vs las otras fuentes).
        """
        from collections import defaultdict

        rows = self.conn.execute("""
            WITH max_por_fuente AS (
                SELECT v.fuente_id, MAX(date(pr.fecha)) AS max_fecha
                FROM precios pr JOIN variantes v ON pr.variante_id = v.id
                GROUP BY v.fuente_id
            ),
            latest AS (
                SELECT v.producto_id, v.fuente_id, f.nombre AS fuente,
                       pr.precio, v.url_producto
                FROM precios pr
                JOIN variantes v ON pr.variante_id = v.id
                JOIN fuentes f ON v.fuente_id = f.id
                JOIN max_por_fuente m ON v.fuente_id = m.fuente_id
                    AND date(pr.fecha) = m.max_fecha
            ),
            multi AS (
                SELECT producto_id FROM latest
                GROUP BY producto_id HAVING COUNT(DISTINCT fuente_id) >= 2
            ),
            topn AS (
                SELECT l.producto_id,
                       ROUND((MAX(l.precio) - MIN(l.precio)) * 100.0 / MIN(l.precio), 1) AS diff_pct
                FROM latest l
                JOIN multi m ON l.producto_id = m.producto_id
                JOIN productos p ON l.producto_id = p.id
                WHERE p.es_combo = 0
                GROUP BY l.producto_id
                ORDER BY diff_pct DESC
                LIMIT ?
            )
            SELECT p.id, p.nombre_normalizado, p.categoria,
                   l.fuente, l.precio, l.url_producto, t.diff_pct
            FROM latest l
            JOIN topn t ON l.producto_id = t.producto_id
            JOIN productos p ON l.producto_id = p.id
            ORDER BY t.diff_pct DESC, p.nombre_normalizado, l.fuente
        """, (top_n,)).fetchall()

        productos = {}
        for r in rows:
            pid = r["id"]
            if pid not in productos:
                productos[pid] = {
                    "id": pid,
                    "nombre": r["nombre_normalizado"],
                    "categoria": r["categoria"],
                    "diff_pct": r["diff_pct"],
                    "fuentes": {},
                }
            productos[pid]["fuentes"][r["fuente"]] = {
                "precio": r["precio"],
                "url": r["url_producto"] or "",
            }

        carrito_por_fuente = defaultdict(list)
        for prod in productos.values():
            fuente_min = min(prod["fuentes"], key=lambda f: prod["fuentes"][f]["precio"])
            precio_min = prod["fuentes"][fuente_min]["precio"]
            precio_max = max(v["precio"] for v in prod["fuentes"].values())
            carrito_por_fuente[fuente_min].append({
                "id": prod["id"],
                "nombre": prod["nombre"],
                "categoria": prod["categoria"],
                "precio": precio_min,
                "url": prod["fuentes"][fuente_min]["url"],
                "precio_max": precio_max,
                "ahorro": round(precio_max - precio_min, 2),
                "todas_fuentes": {f: v["precio"] for f, v in prod["fuentes"].items()},
            })

        carrito = []
        for fuente in sorted(carrito_por_fuente):
            prods = sorted(carrito_por_fuente[fuente], key=lambda x: x["nombre"])
            total = round(sum(i["precio"] for i in prods), 2)
            ahorro_total = round(sum(i["ahorro"] for i in prods), 2)
            carrito.append({
                "fuente": fuente,
                "productos": prods,
                "total": total,
                "ahorro_total": ahorro_total,
            })

        return list(productos.values()), carrito

    def get_all_fuentes(self):
        return [r["nombre"] for r in self.conn.execute(
            "SELECT nombre FROM fuentes ORDER BY nombre"
        ).fetchall()]

    def get_all_categorias(self):
        return [r["categoria"] for r in self.conn.execute(
            "SELECT DISTINCT categoria FROM productos WHERE categoria IS NOT NULL AND es_combo = 0 ORDER BY categoria"
        ).fetchall()]

    def buscar_productos(self, q: str = "", fuentes: list = None, categorias: list = None,
                         max_productos: int = 200):
        """Búsqueda de productos con filtros opcionales de fuente y categoría.

        Ordena por relevancia: productos cuyo nombre empieza con el primer
        token del query aparecen primero; luego el resto alfabéticamente.
        """
        tokens = q.strip().lower().split() if q.strip() else []
        where = ["p.es_combo = 0"]
        params = []

        for token in tokens:
            where.append("p.nombre_normalizado LIKE ?")
            params.append(f"%{token}%")

        if fuentes:
            ph = ",".join("?" * len(fuentes))
            where.append(f"l.fuente IN ({ph})")
            params.extend(fuentes)

        if categorias:
            ph = ",".join("?" * len(categorias))
            where.append(f"p.categoria IN ({ph})")
            params.extend(categorias)

        # Columna de relevancia: 0 si empieza con el primer token, 1 si no
        if tokens:
            relevancia_sql = "CASE WHEN p.nombre_normalizado LIKE ? THEN 0 ELSE 1 END"
            # El param de starts-with va antes de los demás (se inyecta al final de la query)
            starts_param = f"{tokens[0]}%"
        else:
            relevancia_sql = "0"
            starts_param = None

        sql = f"""
            WITH max_por_fuente AS (
                SELECT v.fuente_id, MAX(date(pr.fecha)) AS max_fecha
                FROM precios pr JOIN variantes v ON pr.variante_id = v.id
                GROUP BY v.fuente_id
            ),
            latest AS (
                SELECT v.producto_id, v.fuente_id, f.nombre AS fuente,
                       pr.precio, v.url_producto
                FROM precios pr
                JOIN variantes v ON pr.variante_id = v.id
                JOIN fuentes f ON v.fuente_id = f.id
                JOIN max_por_fuente m ON v.fuente_id = m.fuente_id
                    AND date(pr.fecha) = m.max_fecha
            )
            SELECT p.id, p.nombre_normalizado, p.categoria,
                   l.fuente, l.precio, l.url_producto,
                   {relevancia_sql} AS relevancia
            FROM productos p
            JOIN latest l ON p.id = l.producto_id
            WHERE {" AND ".join(where)}
            ORDER BY relevancia, p.nombre_normalizado, l.fuente
            LIMIT {max_productos * 6}
        """
        # El param de relevancia (CASE en SELECT) va PRIMERO porque precede al WHERE en el SQL
        all_params = ([starts_param] if starts_param else []) + params
        rows = self.conn.execute(sql, all_params).fetchall()

        productos = {}
        orden = []  # preserva el orden de primera aparición (= orden de relevancia del SQL)
        for r in rows:
            pid = r["id"]
            if pid not in productos:
                productos[pid] = {
                    "id": pid,
                    "nombre": r["nombre_normalizado"],
                    "categoria": r["categoria"] or "—",
                    "fuentes": {},
                    "relevancia": r["relevancia"],
                }
                orden.append(pid)
            productos[pid]["fuentes"][r["fuente"]] = {
                "precio": r["precio"],
                "url": r["url_producto"] or "",
            }

        result = []
        for pid in orden[:max_productos]:
            prod = productos[pid]
            if len(prod["fuentes"]) > 1:
                prod["fuente_mas_barata"] = min(
                    prod["fuentes"], key=lambda f: prod["fuentes"][f]["precio"]
                )
            else:
                prod["fuente_mas_barata"] = None
            result.append(prod)

        return result

    def get_highlights(self, dias: int = 7, min_variacion: float = 5.0):
        """Productos con mayor variación de precio en el período."""
        return self.conn.execute("""
            WITH precios_rango AS (
                SELECT v.producto_id, f.nombre as fuente,
                       pr.precio, date(pr.fecha) as fecha,
                       ROW_NUMBER() OVER (PARTITION BY v.producto_id, f.nombre ORDER BY pr.fecha ASC)  as rn_asc,
                       ROW_NUMBER() OVER (PARTITION BY v.producto_id, f.nombre ORDER BY pr.fecha DESC) as rn_desc
                FROM precios pr
                JOIN variantes v ON pr.variante_id = v.id
                JOIN fuentes f ON v.fuente_id = f.id
                WHERE pr.fecha >= date('now', ? || ' days')
            ),
            primero AS (SELECT producto_id, fuente, precio FROM precios_rango WHERE rn_asc = 1),
            ultimo  AS (SELECT producto_id, fuente, precio FROM precios_rango WHERE rn_desc = 1)
            SELECT p.id, p.nombre_normalizado, u.fuente,
                   pr_p.precio as precio_anterior, u.precio as precio_actual,
                   ROUND((u.precio - pr_p.precio) * 100.0 / pr_p.precio, 1) as variacion_pct
            FROM ultimo u
            JOIN primero pr_p ON u.producto_id = pr_p.producto_id AND u.fuente = pr_p.fuente
            JOIN productos p ON u.producto_id = p.id
            WHERE pr_p.precio > 0
              AND ABS((u.precio - pr_p.precio) * 100.0 / pr_p.precio) >= ?
            ORDER BY ABS(variacion_pct) DESC
            LIMIT 20
        """, (f"-{dias}", min_variacion)).fetchall()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args()

    if args.stats:
        db = Database()
        s = db.stats()
        print(f"Productos:    {s['productos']}")
        print(f"Variantes:    {s['variantes']}")
        print(f"Registros:    {s['precios']}")
        print(f"Última fecha: {s['ultima_fecha']}")
        print(f"Fuentes:      {[f['nombre'] for f in s['fuentes']]}")
