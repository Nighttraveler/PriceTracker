from db import Database
from datetime import datetime

def migrate_fecha_to_timestamp():
    db = Database()

    # Create temporary table with TIMESTAMP column and migrate data
    db.conn.executescript("""
        CREATE TABLE IF NOT EXISTS precios_new (
            id INTEGER PRIMARY KEY,
            variante_id INTEGER REFERENCES variantes(id),
            precio REAL NOT NULL,
            fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            moneda TEXT DEFAULT 'ARS'
        );

        INSERT INTO precios_new (id, variante_id, precio, fecha, moneda)
        SELECT id, variante_id, precio, datetime(fecha || ' 00:00:00'), moneda
        FROM precios;

        DROP TABLE precios;
        ALTER TABLE precios_new RENAME TO precios;

        CREATE INDEX IF NOT EXISTS idx_precios_fecha ON precios(fecha);
        CREATE INDEX IF NOT EXISTS idx_precios_variante ON precios(variante_id);
    """)
    db.conn.commit()
    print("Migration of 'fecha' column to TIMESTAMP complete.")

if __name__ == "__main__":
    migrate_fecha_to_timestamp()
