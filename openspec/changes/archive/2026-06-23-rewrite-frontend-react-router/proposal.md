## Why

The dashboard is 8 server-rendered Jinja2 templates (~1,600 lines) styled with Bootstrap 5 over a CDN, with page logic split between Python view functions and inline `<script>` blocks in `base.html`. This couples data shaping to HTML rendering, makes interactive features (cart, search-as-you-type, charts) awkward, and offers no typed contract or component reuse. Moving to a React Router v7 SPA backed by a clean JSON API decouples presentation from data, enables a modern typed/tested frontend, and turns Flask into a reusable API backend.

## What Changes

- Add a versioned JSON API (`/api/v1/*`) on the Flask side exposing all page data, wrapping existing `db.py` methods. Shared data-shaping logic (e.g. `_compute_optimal_cart`, the `/precios` matrix builder, `/producto` chart grouping) is extracted into reusable functions so HTML and JSON share one source of truth.
- Scaffold a React Router v7 SPA under `frontend/` (monorepo) with the full stack: React 19 + TS 5.9, Vite 8, Tailwind v4 (CSS-first), shadcn/ui (radix-nova / neutral / CSS vars), TanStack Query v5, Zustand v5, Axios, Sonner, Lucide, Recharts.
- Port all 6 pages — Dashboard, Precios, Producto (Recharts price history), Ahorro, Buscar, Carrito — using React Router loaders (SSR) + TanStack Query hybrid fetching.
- Reimplement the localStorage cart (`pt_carrito`, numeric product IDs) as a Zustand store preserving the exact same key and ID semantics.
- Add frontend tooling: Vitest 4 + Testing Library, Playwright, oxlint + oxfmt, Husky + lint-staged.
- Wire `docker-compose.yml` with a Node frontend service alongside Flask + PostgreSQL; update docs.
- **Non-breaking during migration:** existing Jinja HTML routes stay live until the SPA reaches parity. Retiring them is a separate follow-up.

- **No Alembic migration** required — this change is read-only against the existing schema; no DDL or column changes.
- **Cached routes:** the new `/api/v1/*` endpoints will mirror the current cache policy (4h TTL for dashboard/precios/ahorro, 2h for buscar; carrito + cart endpoints uncached). Existing cached HTML routes (`/`, `/precios`, `/ahorro`, `/buscar`) are unchanged.
- **Latest-price queries** are reused as-is from `db.py` (the `max_por_fuente` CTE pattern in `/ahorro`, optimal cart, and search) — this change does not modify them.

## Capabilities

### New Capabilities
- `json-api`: Versioned `/api/v1/*` REST endpoints serializing dashboard, prices, product detail, savings, search, and cart data over existing `db.py` query logic.
- `react-frontend`: React Router v7 SSR SPA under `frontend/` — app shell, providers (TanStack Query, Sonner), routing, and the 6 ported pages consuming the JSON API via loaders + TanStack Query.
- `frontend-tooling`: Build/test/quality tooling for the SPA — Tailwind v4 + shadcn/ui setup, Vitest + Testing Library, Playwright, oxlint + oxfmt, Husky + lint-staged.

### Modified Capabilities
<!-- None: existing capabilities (cart-quick-add, cart-toggle-home, english-codebase, scraper-*) keep their current requirements. Cart behavior is reimplemented in React but preserves the same observable requirements. -->

## Impact

- **New code:** `frontend/` (entire React app); `api.py` Flask blueprint registered in `app.py`; extracted shared serializers.
- **Modified code:** `app.py` (register blueprint, extract shared shaping functions), `docker-compose.yml`, `requirements.txt` (add `flask-cors`), README/docs.
- **Dependencies:** new Node/pnpm toolchain under `frontend/`; one new Python dep (`flask-cors`).
- **Runtime/deploy:** introduces a Node SSR server as a second service; PostgreSQL remains the system of record. No schema or data changes.
