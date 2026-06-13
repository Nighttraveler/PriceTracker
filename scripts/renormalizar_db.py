#!/usr/bin/env python3
"""Re-runs fuzzy matching for all variants using the current normalizer.

Useful after changing SIMILARITY_THRESHOLD, _normalize_for_match, or any
matching logic in normalizer.py. Redirects variants that now match an existing
product and cleans up orphan products that were left without variants.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import Database
from normalizer import Normalizer


def renormalize_db():
    db = Database()
    norm = Normalizer(db)

    variantes = db._fetchall(
        "SELECT id, nombre_original, fuente_id, producto_id FROM variantes"
    )

    print(f"Total variants to process: {len(variantes)}")
    updated = 0

    for v in variantes:
        new_id = norm.get_or_create_product(v["nombre_original"], v["fuente_id"])
        if new_id != v["producto_id"]:
            print(f"  Redirecting '{v['nombre_original']}': product {v['producto_id']} → {new_id}")
            db._execute(
                "UPDATE variantes SET producto_id = ? WHERE id = ?",
                (new_id, v["id"])
            )
            updated += 1

    db.commit()
    print(f"\nVariants redirected: {updated}")

    # Remove orphan products (no variants left after merges)
    orphans = db._fetchall("""
        SELECT id, nombre_normalizado FROM productos
        WHERE id NOT IN (SELECT DISTINCT producto_id FROM variantes)
    """)

    if orphans:
        print(f"Orphan products to delete: {len(orphans)}")
        for p in orphans:
            print(f"  Deleting: {p['nombre_normalizado']}")
        ids = tuple(p["id"] for p in orphans)
        placeholders = ",".join(["?"] * len(ids))
        db._execute(f"DELETE FROM productos WHERE id IN ({placeholders})", ids)
        db.commit()
    else:
        print("No orphan products.")

    print("Re-normalization complete.")


if __name__ == "__main__":
    renormalize_db()
