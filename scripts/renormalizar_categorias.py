#!/usr/bin/env python3
"""Recalculates category and is_combo for all products using the current normalizer rules."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import Database
from normalizer import detect_category, is_combo


def main():
    db = Database()
    productos = db._fetchall(
        "SELECT id, nombre_normalizado, categoria, es_combo FROM productos"
    )

    print(f"Total products: {len(productos)}")
    updated = 0

    for p in productos:
        new_cat   = detect_category(p["nombre_normalizado"])
        new_combo = int(is_combo(p["nombre_normalizado"]))

        if new_cat != p["categoria"] or new_combo != p["es_combo"]:
            db._execute(
                "UPDATE productos SET categoria = ?, es_combo = ? WHERE id = ?",
                (new_cat, new_combo, p["id"])
            )
            updated += 1

    db.commit()
    print(f"Updated: {updated}")
    print(f"Unchanged: {len(productos) - updated}")


if __name__ == "__main__":
    main()
