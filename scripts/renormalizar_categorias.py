#!/usr/bin/env python3
"""Recalcula categorías y es_combo de todos los productos según normalizer.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import Database
from normalizer import detectar_categoria, es_combo

def main():
    db = Database(str(Path(__file__).parent.parent / "data" / "precios.db"))
    productos = db.conn.execute(
        "SELECT id, nombre_normalizado, categoria, es_combo FROM productos"
    ).fetchall()

    print(f"Total productos: {len(productos)}")
    actualizados = 0

    for p in productos:
        nueva_cat   = detectar_categoria(p["nombre_normalizado"])
        nuevo_combo = int(es_combo(p["nombre_normalizado"]))

        if nueva_cat != p["categoria"] or nuevo_combo != p["es_combo"]:
            db.conn.execute(
                "UPDATE productos SET categoria = ?, es_combo = ? WHERE id = ?",
                (nueva_cat, nuevo_combo, p["id"])
            )
            actualizados += 1

    db.conn.commit()
    print(f"Actualizados: {actualizados}")
    print(f"Sin cambios:  {len(productos) - actualizados}")

if __name__ == "__main__":
    main()
