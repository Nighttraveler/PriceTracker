# Spec: react-frontend

## Purpose

Defines the React Router v7 SSR frontend application — its pages, routing, data-fetching strategy, state management, and user interactions.

## Requirements

### Requirement: React Router v7 SSR application

The system SHALL provide a React Router v7 (framework mode, SSR) application under `frontend/`, built with React 19, TypeScript 5.9, and Vite 8, served as the primary user interface and consuming the `/api/v1/*` JSON API.

#### Scenario: Server-rendered first paint

- **WHEN** a user requests a page route
- **THEN** the server returns HTML containing the page's initial data (rendered via the route loader), not an empty loading shell

#### Scenario: App shell with navigation

- **WHEN** any page renders
- **THEN** a shared layout shows navigation to Dashboard, Precios, Ahorro, Buscar, and Carrito, with a cart item count badge

### Requirement: Loader + TanStack Query hybrid data fetching

Each page SHALL fetch its initial data in a React Router loader (server-side, via the shared Axios client) and hydrate it into TanStack Query so subsequent client interactions (filtering, pagination, refetch, mutations) are handled client-side without a full server round-trip.

#### Scenario: Loader provides initial data

- **WHEN** a page route is entered
- **THEN** its loader has fetched the corresponding `/api/v1/*` data before the component renders

#### Scenario: Client interaction refetches without server navigation

- **WHEN** the user changes a filter or page on a loaded page
- **THEN** the data updates via a client-side TanStack Query fetch rather than a full-page server reload

### Requirement: Dashboard page

The frontend SHALL provide a Dashboard page at `/` showing database stats, top-cheapest products, and per-source price highlights with a day-window selector.

#### Scenario: Dashboard renders highlights

- **WHEN** the user opens `/`
- **THEN** stats, top-cheapest products, and per-source subas/bajas highlights are displayed

### Requirement: Prices page

The frontend SHALL provide a Prices page at `/precios` showing the paginated product × source price matrix with variation indicators, a category filter, a day-window selector, and the cheapest source highlighted per row.

#### Scenario: Prices grid with cheapest highlight

- **WHEN** the user opens `/precios`
- **THEN** products are listed with each source's price and variation, and the cheapest source per multi-source row is visually marked

#### Scenario: Filter and paginate

- **WHEN** the user selects a category or changes page
- **THEN** the grid updates to the filtered/paged results

### Requirement: Product detail page

The frontend SHALL provide a Product detail page at `/producto/:id` rendering a multi-source price-history line chart using Recharts and listing product variants.

#### Scenario: Price history chart

- **WHEN** the user opens a product detail page
- **THEN** a Recharts line chart shows one series per source over the selected day window, and variants are listed

### Requirement: Savings page

The frontend SHALL provide a Savings page at `/ahorro` showing average/min/max price per category × source with the cheapest source highlighted, and the computed optimal cart.

#### Scenario: Savings table renders

- **WHEN** the user opens `/ahorro`
- **THEN** the per-category source comparison and the optimal cart are displayed

### Requirement: Search page

The frontend SHALL provide a Search page at `/buscar` supporting query, source, and category filters with debounced search-as-you-type and server-backed pagination; deep-linked query params SHALL be honored on initial load.

#### Scenario: Debounced search

- **WHEN** the user types a query
- **THEN** results refresh after a short debounce via the search endpoint

#### Scenario: Deep link restores filters

- **WHEN** the user opens `/buscar` with query params in the URL
- **THEN** the loader returns results matching those params on first render

### Requirement: Cart page and cart state

The frontend SHALL provide a Cart page at `/carrito` backed by a Zustand store that persists numeric product IDs to localStorage under the key `pt_carrito`, preserving the existing cart key and ID semantics. The page SHALL compute the optimal cart via `POST /api/v1/carrito` and SHALL show toast feedback on add/remove.

#### Scenario: Cart persists across reload

- **WHEN** the user adds products to the cart and reloads the app
- **THEN** the cart contents persist via localStorage under `pt_carrito`

#### Scenario: Add from other pages

- **WHEN** the user adds a product from the Prices, Search, or Product pages
- **THEN** the item is added to the cart, the nav badge count updates, and a toast confirms the action

#### Scenario: Optimal cart computed

- **WHEN** the user views the cart with items
- **THEN** the cart is grouped by cheapest source with per-source totals and savings, computed via the cart API
