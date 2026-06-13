from db import Database
from datetime import timedelta

def fix_timestamps():
    db = Database()

    # Get all variants that have multiple prices with the same date.
    # Group by variante_id to sort their prices by id (auto-incremental, marks insertion order).
    variantes = db.conn.execute("SELECT DISTINCT variante_id FROM precios").fetchall()

    for v in variantes:
        variante_id = v["variante_id"]
        # Fetch prices for this variant ordered by ID (oldest first)
        precios = db.conn.execute(
            "SELECT id, fecha FROM precios WHERE variante_id = ? ORDER BY id ASC",
            (variante_id,)
        ).fetchall()

        # Increment timestamp by 1 second per entry to preserve insertion order
        base_time = None
        for i, p in enumerate(precios):
            if i == 0:
                base_time = datetime.strptime(p["fecha"], "%Y-%m-%d %H:%M:%S")
                continue

            new_time = base_time + timedelta(seconds=i)
            db.conn.execute(
                "UPDATE precios SET fecha = ? WHERE id = ?",
                (new_time.strftime("%Y-%m-%d %H:%M:%S"), p["id"])
            )

    db.conn.commit()
    print("Timestamp correction based on insertion order complete.")

if __name__ == "__main__":
    from datetime import datetime
    fix_timestamps()
