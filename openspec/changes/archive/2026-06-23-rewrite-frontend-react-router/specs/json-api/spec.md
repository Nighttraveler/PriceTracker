## ADDED Requirements

### Requirement: Versioned JSON API namespace

The system SHALL expose page data under a versioned `/api/v1/*` namespace returning `application/json`. These endpoints SHALL wrap existing `db.py` query methods and SHALL NOT introduce new schema, DDL, or modifications to latest-price (`max_por_fuente` CTE) logic.

#### Scenario: API responds with JSON

- **WHEN** a client requests any `/api/v1/*` endpoint
- **THEN** the response Content-Type is `application/json` and the body matches the documented shape for that endpoint

#### Scenario: HTML routes remain available during migration

- **WHEN** the JSON API is deployed
- **THEN** the existing Jinja HTML routes (`/`, `/precios`, `/producto/<id>`, `/ahorro`, `/buscar`, `/carrito`) continue to function unchanged

### Requirement: Dashboard endpoint

The system SHALL provide `GET /api/v1/dashboard?dias=<int>` returning database stats, top-cheapest products, and price highlights grouped per source into subas (increases) and bajas (decreases).

#### Scenario: Dashboard data returned

- **WHEN** a client requests `/api/v1/dashboard?dias=7`
- **THEN** the response contains `stats`, `top_baratos`, and a per-source `highlights` list each with `subas` and `bajas` arrays

#### Scenario: Default day window

- **WHEN** `dias` is omitted
- **THEN** the endpoint defaults to a 7-day window

### Requirement: Prices endpoint

The system SHALL provide `GET /api/v1/precios?dias=<int>&page=<int>&cat=<string>` returning the paginated product × source price matrix with per-source current price, variation percentage, cheapest-source marker, available categories, and pagination metadata.

#### Scenario: Paginated price matrix

- **WHEN** a client requests `/api/v1/precios?page=1`
- **THEN** the response contains the page rows, `categorias_list`, `fuentes`, and `page`/`total_pages`/`total`

#### Scenario: Category filter

- **WHEN** a client requests `/api/v1/precios?cat=<valid category>`
- **THEN** only rows in that category are returned

### Requirement: Product detail endpoint

The system SHALL provide `GET /api/v1/producto/<id>?dias=<int>` returning the product, per-source price-history time series suitable for charting, and product variants. It SHALL return 404 when the product does not exist.

#### Scenario: Product history returned

- **WHEN** a client requests `/api/v1/producto/<existing id>`
- **THEN** the response contains the product, sorted `fechas`, and per-source `datasets` with aligned price arrays

#### Scenario: Unknown product

- **WHEN** a client requests `/api/v1/producto/<nonexistent id>`
- **THEN** the response status is 404

### Requirement: Savings endpoint

The system SHALL provide `GET /api/v1/ahorro` returning average/min/max price per category × source with the cheapest source flagged, plus the computed optimal cart.

#### Scenario: Savings data returned

- **WHEN** a client requests `/api/v1/ahorro`
- **THEN** the response contains a per-category table with each source's avg/min/max and a `mas_barata` marker, plus `carrito` and `fuentes`

### Requirement: Search endpoint

The system SHALL provide `GET /api/v1/buscar?q=&fuente=&cat=&page=` returning products matching the query and filters, available sources/categories, and pagination metadata.

#### Scenario: Search results returned

- **WHEN** a client requests `/api/v1/buscar?q=leche`
- **THEN** the response contains matching `resultados`, `all_fuentes`, `all_cats`, and pagination metadata

#### Scenario: Empty query returns no results

- **WHEN** a client requests `/api/v1/buscar` with no query or filters
- **THEN** `resultados` is empty and `buscado` is false

### Requirement: Cart endpoints

The system SHALL provide `GET /api/v1/buscar_carrito?q=&page=&per_page=` for the cart quick-add search and `POST /api/v1/carrito` that accepts a list of numeric product IDs and returns the optimal cart grouped by cheapest source, plus any IDs not found. Cart endpoints SHALL NOT be cached.

#### Scenario: Optimal cart computed

- **WHEN** a client POSTs `{"ids": [1, 2, 3]}` to `/api/v1/carrito`
- **THEN** the response contains `productos`, `carrito` (grouped by source with totals and savings), `fuentes`, and `no_encontrados`

#### Scenario: Invalid IDs ignored

- **WHEN** the posted `ids` contain non-numeric or non-positive values
- **THEN** those values are ignored and only valid positive integer IDs are processed

### Requirement: API cache policy mirrors HTML routes

The system SHALL apply the existing cache policy to the new endpoints: 4h TTL for dashboard, precios, and ahorro; 2h for buscar; no caching for cart endpoints.

#### Scenario: Cart endpoints serve live data

- **WHEN** the cart endpoints are requested
- **THEN** responses are not served from cache

### Requirement: Cross-origin access for the frontend dev server

The system SHALL permit cross-origin requests from the React frontend dev origin to the `/api/v1/*` namespace.

#### Scenario: Frontend dev origin allowed

- **WHEN** the React dev server requests an `/api/v1/*` endpoint
- **THEN** the response includes the CORS headers permitting that origin
