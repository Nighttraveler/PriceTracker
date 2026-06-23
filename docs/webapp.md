# Web app

The UI is a **React Router v8 SSR SPA** (`frontend/`) backed by a **Flask JSON API** (`api.py`).
The legacy Jinja2 HTML routes remain in `app.py` as a fallback during transition.

## Architecture

```
Browser
  │
  ├── GET /*, /precios, /producto/:id, etc.
  │     → React frontend (Node SSR, port 3000)
  │          └── loaders call Flask API server-side → hydrated HTML
  │
  └── XHR /api/v1/*
        → Flask API (port 5000)
```

The React app uses **React Router loaders** for SSR (initial page HTML contains data) and
**TanStack Query** for client-side refetches (filters, pagination, chart period changes).

## Flask JSON API (`api.py`)

Blueprint registered at `/api/v1/`. All routes return JSON.

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/dashboard` | GET | Stats, top products, highlights per source |
| `/api/v1/precios` | GET | Paginated price matrix (`?dias`, `?page`, `?cat`) |
| `/api/v1/producto/<id>` | GET | Product detail + Recharts datasets (`?dias`) |
| `/api/v1/ahorro` | GET | Avg price by category×source + optimal cart |
| `/api/v1/buscar` | GET | Search with source/category filters + pagination |
| `/api/v1/buscar_carrito` | GET | Modal search for cart (sorted by cheapest price) |
| `/api/v1/carrito` | POST | Optimal cart for a list of product IDs |

Cache: `flask-caching` with 5-minute TTL (10 min for dashboard/ahorro).
CORS: `flask-cors` scoped to `/api/v1/*`.

## React frontend (`frontend/`)

**Stack:** React Router v8 (SSR) · React 19 · TypeScript 5.9 · Tailwind v4 · shadcn/ui (radix-nova) ·
TanStack Query v5 · Zustand v5 · Recharts · Sonner · Lucide

**Routes:**

| Route | File | Description |
|---|---|---|
| `/` | `routes/home.tsx` | Dashboard: stats, top products, highlights |
| `/precios` | `routes/precios.tsx` | Paginated price matrix with source columns |
| `/producto/:id` | `routes/producto.$id.tsx` | Price history chart (Recharts) + period summary |
| `/ahorro` | `routes/ahorro.tsx` | Avg by category×source + optimal cart |
| `/buscar` | `routes/buscar.tsx` | Search with source/category filters |
| `/carrito` | `routes/carrito.tsx` | Cart: add via modal, optimal cart grouped by source |

**Cart state:** Zustand `persist` middleware, localStorage key `pt_carrito`, stores `number[]` IDs.
Same key as the previous vanilla-JS implementation — no migration needed.

**SSR QueryClient:** `getQueryClient()` returns a per-request instance on the server and a
module-level singleton in the browser (guarded by `typeof window`), preventing cross-request
state leakage.

## Legacy HTML routes (`app.py` / `templates/`)

`/`, `/precios`, `/ahorro`, `/buscar`, `/producto/<id>` still render Jinja2 templates.
These remain until the React frontend reaches full parity and the `app` service is retired
or repurposed as API-only. See [architecture.md](architecture.md) for the transition plan.
