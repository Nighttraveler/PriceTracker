#!/usr/bin/env python3
"""Re-corre el fuzzy matching para todas las variantes con el normalizer actual.

Útil después de cambiar UMBRAL_SIMILITUD, _normalizar_para_match o cualquier
lógica de matching en normalizer.py. Redirige variantes que ahora matchean a
un producto existente y limpia productos huérfanos que quedaron sin variantes.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import Database
from normalizer import Normalizer


def re_normalizar_db():
    db = Database(str(Path(__file__).parent.parent / "data" / "precios.db"))
    norm = Normalizer(db)

    variantes = db.conn.execute(
        "SELECT id, nombre_original, fuente_id, producto_id FROM variantes"
    ).fetchall()

    print(f"Total variantes a procesar: {len(variantes)}")
    actualizadas = 0

    for v in variantes:
        nuevo_id = norm.obtener_o_crear_producto(v["nombre_original"], v["fuente_id"])
        if nuevo_id != v["producto_id"]:
            print(f"  Redirigiendo '{v['nombre_original']}': producto {v['producto_id']} → {nuevo_id}")
            db.conn.execute(
                "UPDATE variantes SET producto_id = ? WHERE id = ?",
                (nuevo_id, v["id"])
            )
            actualizadas += 1

    db.conn.commit()
    print(f"\nVariantes redirigidas: {actualizadas}")

    # Limpiar productos huérfanos (sin variantes tras las fusiones)
    huerfanos = db.conn.execute("""
        SELECT id, nombre_normalizado FROM productos
        WHERE id NOT IN (SELECT DISTINCT producto_id FROM variantes)
    """).fetchall()

    if huerfanos:
        print(f"Productos huérfanos a eliminar: {len(huerfanos)}")
        for p in huerfanos:
            print(f"  Eliminando: {p['nombre_normalizado']}")
        ids = [p["id"] for p in huerfanos]
        db.conn.execute(f"DELETE FROM productos WHERE id IN ({','.join('?'*len(ids))})", ids)
        db.conn.commit()
    else:
        print("Sin productos huérfanos.")

    print("Re-normalización completada.")


if __name__ == "__main__":
    re_normalizar_db()
