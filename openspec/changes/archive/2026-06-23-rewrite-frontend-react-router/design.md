## Context

`price-tracker` is a Python/Flask app with 8 server-rendered Jinja2 pages (Bootstrap 5 CDN,
Chart.js) and no dedicated JavaScript framework. All page data is shaped in Python view functions
and injected into templates; only two endpoints (`/api/buscar_carrito`, `/api/carrito`) return JSON.

This rewrite separates presentation from data by turning Flask into a JSON API backend and
introducing a React Router v7 SPA under `frontend/`. The Python backend is untouched structurally —
the `db.py` query layer already contains all necessary query logic; the only backend additions are
serializer/blueprint wrappers. Jinja HTML routes are preserved throughout the migration.

Constraints relevant to implementation:
- Latest-price queries must use the `max_por_fuente` CTE pattern (max date per source
  independently) — never a global `MAX(fecha)`.
- Flask cache policy: 4h TTL for dashboard/precios/ahorro, 2h for buscar, uncached for cart/api.
- Cart: `localStorage` key `pt_carrito`, numeric product IDs.
- No schema changes → no Alembic migration needed.

## Goals / Non-Goals

**Goals:**
- Expose all page data as a versioned JSON API (`/api/v1/*`) backed by existing `db.py` methods.
- Scaffold a fully typed, tested React Router v7 SSR SPA under `frontend/` with the specified stack.
- Port all 6 pages using React Router loaders (server-side initial fetch) + TanStack Query hybrid (client refetch/mutations).
- Implement the cart as a Zustand store persisted to `localStorage`, preserving existing key and ID semantics.
- Keep the Jinja HTML routes alive throughout — only retire them as a separate follow-up after parity is confirmed.

**Non-Goals:**
- Authentication, authorization, or user accounts.
- Retiring Jinja templates (this is a follow-up, not in scope here).
- Changing the database schema, scraper logic, normalizer, or reporter.
- Migrating to a different API framework (FastAPI, etc.) — Flask stays.

## Decisions

### 1. Monorepo subfolder (`frontend/`) vs separate repo

**Chosen:** `frontend/` subfolder in the same repo.

Rationale: shared git history and single `docker-compose.yml` simplify the dev loop during migration.
The Flask API and the SPA evolve together; a separate repo would require cross-repo coordination for
every API contract change.

Alternative considered: separate repo — more isolation but adds deployment complexity and slows
early iteration when API shape is still being discovered.

### 2. Data fetching: React Router loaders (SSR) + TanStack Query hybrid

**Chosen:** Route loaders call the Flask API server-side for the first render; the loader result is
passed as `initialData` (or via dehydrated state) into TanStack Query so client-side interactions
(pagination, filters, search debounce, mutations) work without full server round-trips.

Rationale: meets the stated requirement of real SSR (fast first paint, data in `view-source`) while
keeping the DX benefits of TanStack Query for mutations and cache invalidation. Pure CSR would lose
SSR; pure loaders would lose the client-side cache / mutation ergonomics.

**Critical implementation note:** The TanStack `QueryClient` MUST be created per request on the
server (not as a module-global). A module-global on the Node SSR server leaks state across
concurrent requests. Pattern:

```ts
// app/lib/queryClient.ts
import { QueryClient } from "@tanstack/react-query";
export const createQueryClient = () => new QueryClient({ ... });
// Use React Router's getLoadContext / singleton pattern on the browser only
```

### 3. Charts: Recharts via shadcn/ui chart primitives

**Chosen:** Recharts wrapped by the shadcn/ui `<Chart>` components (CSS variable theming built in).

Rationale: consistent with the chosen UI kit; source-color mapping (dia/anonima/encombo/carrefour)
maps to CSS variables; no additional charting bundle outside what shadcn scaffolds.

Alternative considered: `react-chartjs-2` — closer visual parity with the current Chart.js charts,
but outside the shadcn/Tailwind theming system.

### 4. Cart state: Zustand + localStorage (no migration)

**Chosen:** Zustand store with `persist` middleware using `localStorage` key `pt_carrito`, storing
`number[]`. This exactly preserves the existing cart behavior (including cross-page badge counts)
and is compatible with any products already in a user's `localStorage`.

Rationale: the vanilla JS cart implementation in `base.html` uses this exact key and type. Users
with items in their cart will see them retained after the SPA ships.

### 5. API blueprint: `api.py` + shared serializer functions

**Chosen:** A new Flask blueprint in `api.py` registered with the prefix `/api/v1`, containing thin
serializer functions. Per-route data-shaping logic currently inlined in `app.py` views (e.g.
`_compute_optimal_cart`, the precios matrix builder, the producto chart grouper) is extracted into
module-level functions shared by both the HTML view and the JSON endpoint.

Rationale: keeps HTML routes working during migration without duplicating business logic. If the
same function produces the data for both Jinja and JSON responses, behavioral divergence is
impossible.

### 6. CORS: `flask-cors` scoped to `/api/v1/*`, dev origin only in development

**Chosen:** Add `flask-cors` to `requirements.txt`. Allow the React dev server origin (e.g.
`http://localhost:5173`) via an environment variable; in production the frontend and API are
served from the same compose network so CORS headers are minimal.

### 7. Tailwind v4 CSS-first (no `tailwind.config.js`)

**Chosen:** `@tailwindcss/vite` plugin; `app/app.css` uses `@import "tailwindcss";` and an
`@theme {}` block for custom tokens. No `tailwind.config.js` exists in the repo.

Rationale: Tailwind v4 CSS-first is the canonical v4 setup and aligns with shadcn's v4 support.

### 8. Husky in a monorepo subfolder

**Chosen:** Husky is initialized at the **repo root** (`husky init` run from the root), since git
root is the repo root. The pre-commit hook calls `lint-staged` with globs scoped to
`frontend/**/*.{ts,tsx,js,jsx}` so only frontend files are processed. The `lint-staged` config
lives in `frontend/package.json` and husky's `pre-commit` script cds into `frontend/` before
running `pnpm lint-staged`.

### 9. `radix-nova` shadcn style

If `radix-nova` is not available in the installed `shadcn` CLI version, fall back to `default` style
with a custom `@theme {}` block in `app.css` that achieves equivalent neutral/CSS-variable semantics.
The key constraint is `cssVariables: true` in `components.json` so all color tokens are overridable.

## Risks / Trade-offs

- **SSR QueryClient cross-request leakage** → Mitigation: create a new `QueryClient` in each
  request; browser-only singleton via a module-level lazy init guarded by `typeof window !== "undefined"`.
- **Husky path complexity in monorepo** → Mitigation: Husky at repo root, `pre-commit` cds into
  `frontend/` before running lint-staged; glob scoped to `frontend/**`.
- **Long-running migration (Jinja templates stay alive)** → Mitigation: each phase is independently
  shippable; HTML routes are never broken; parity check before retiring templates.
- **API contract drift** → Mitigation: shared serializer functions used by both HTML and JSON routes;
  consider TypeScript `zod` schemas for response validation in the frontend (optional).
- **`radix-nova` availability** → Mitigation: documented fallback to `default` + custom `@theme {}`.
- **Two servers in docker-compose** → Mitigation: `API_URL` env var on the Node service points to
  the Flask container; `VITE_API_URL` env var on the browser client points to the exposed port.

## Migration Plan

1. **Phase 0** — scaffold `frontend/` with the full stack; no app logic, all tests pass.
2. **Phase 1** — app shell, providers, Zustand cart, nav with badge; health-check test passes.
3. **Phase 2** — test infra (Vitest, Playwright), lint/format (oxlint/oxfmt), pre-commit (Husky).
4. **Phase 3** — Flask `/api/v1/*` blueprint; curl each endpoint; pytest for status+shape.
5. **Phase 4** — port read-only pages: Dashboard, Precios, Producto (Recharts).
6. **Phase 5** — port Search page with debounced TanStack Query and deep-linked params.
7. **Phase 6** — port Cart page with Zustand mutations, Sonner toasts, optimal-cart API call.
8. **Phase 7** — docker-compose frontend service; docs update; parity walkthrough.

**Rollback:** Jinja HTML routes are never removed during this migration. If the SPA regresses, users
can fall back to the `/` → `/carrito` HTML routes. The SPA can be disabled simply by not starting
the Node service or by removing the reverse-proxy rule pointing to it.

## Open Questions

- Should the Flask API enforce type checking on query params (e.g. `dias` must be an integer)?
  Currently Flask view functions parse them with `int()` and would 500 on non-numeric input.
  Low priority for now — add input validation in a follow-up.
- Should the Node SSR server be a standalone `react-router-serve` process or embedded in the
  existing Flask server via a subprocess? Preferred answer: standalone (separate docker-compose
  service), which is simpler and keeps Python and Node processes independent.
