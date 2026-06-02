# Price Tracker Migration Guide

## Containerization

This application is now dockerized.

### Prerequisites
- Docker and Docker Compose installed.

### Setup
1.  **Build and run**:
    ```bash
    docker-compose up --build
    ```
2.  The application uses `DATABASE_URL` for the database connection. By default, it connects to the PostgreSQL container defined in `docker-compose.yml`.

## Migrating SQLite Data to PostgreSQL

If you have an existing `data/precios.db` file, you can migrate it to the PostgreSQL database:

1.  Ensure the PostgreSQL container is running:
    ```bash
    docker-compose up -d db
    ```
2.  Run the migration script:
    ```bash
    export DATABASE_URL=postgresql://user:password@localhost:5432/price_tracker
    export DATABASE_PATH=data/precios.db
    python3 scripts/migrate_sqlite_to_postgres.py
    ```
    *Note: You may need to install the dependencies locally: `pip install sqlalchemy psycopg2-binary`.*
