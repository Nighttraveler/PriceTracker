import sqlite3
import sqlalchemy as sa
from sqlalchemy.schema import CreateTable
import os

# Source (SQLite)
SQLITE_DB = "data/precios.db"
sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_conn.row_factory = sqlite3.Row

# Target (PostgreSQL)
# Assume DATABASE_URL is available in the environment
TARGET_DB_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/price_tracker")
engine = sa.create_engine(TARGET_DB_URL)

def migrate():
    # 1. Create tables in Postgres
    # Use reflection to map SQLite schema or manually define? 
    # Manual definition is safer given SQLite's relaxed types.
    
    metadata = sa.MetaData()
    
    fuentes = sa.Table('fuentes', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('nombre', sa.String, unique=True, nullable=False),
        sa.Column('url_base', sa.String, nullable=False)
    )

    productos = sa.Table('productos', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('nombre_normalizado', sa.String, unique=True, nullable=False),
        sa.Column('categoria', sa.String),
        sa.Column('unidad', sa.String),
        sa.Column('es_combo', sa.Integer, nullable=False, default=0)
    )

    variantes = sa.Table('variantes', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('producto_id', sa.Integer, sa.ForeignKey('productos.id')),
        sa.Column('fuente_id', sa.Integer, sa.ForeignKey('fuentes.id')),
        sa.Column('nombre_original', sa.String, nullable=False),
        sa.Column('url_producto', sa.String)
    )

    precios = sa.Table('precios', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('variante_id', sa.Integer, sa.ForeignKey('variantes.id')),
        sa.Column('precio', sa.Float, nullable=False),
        sa.Column('fecha', sa.DateTime, nullable=False),
        sa.Column('moneda', sa.String, default='ARS')
    )

    metadata.create_all(engine)

    # 2. Migrate Data
    with engine.begin() as conn:
        for table in ['fuentes', 'productos', 'variantes', 'precios']:
            print(f"Migrating {table}...")
            # Check if data exists
            existing_count = conn.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar()
            if existing_count > 0:
                print(f"Skipping {table}, data already exists.")
                continue
                
            rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
            if rows:
                conn.execute(metadata.tables[table].insert(), [dict(r) for r in rows])
    
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
