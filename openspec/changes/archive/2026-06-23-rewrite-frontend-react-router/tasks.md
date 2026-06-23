## 1. Scaffold React Router v7 app

- [x] 1.1 Run `pnpm dlx create-react-router@latest frontend` with TypeScript + framework mode; verify React 19, React Router 7.15, TypeScript 5.9, Vite 8
- [x] 1.2 Set up `~/` path alias (`~/*` → `app/*`) in `tsconfig.json` and `vite.config.ts`
- [x] 1.3 Configure Tailwind v4: install `@tailwindcss/vite`, add plugin to `vite.config.ts`, replace default CSS with `@import "tailwindcss";` + `@theme {}` block in `app/app.css`
- [x] 1.4 Run `pnpm dlx shadcn@latest init` with `radix-nova` style, `neutral` base, CSS variables enabled, and the required aliases; commit `components.json`
- [x] 1.5 Add shadcn primitives needed by the pages: button, card, table, input, select, badge, dialog, pagination, chart (Recharts-backed)

## 2. Install runtime dependencies

- [x] 2.1 Install `@tanstack/react-query@^5`, `zustand@^5`, `axios`, `sonner`, `lucide-react`, `recharts`
- [x] 2.2 Install dev deps: `vitest@^4`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`, `@playwright/test`, `oxlint`, `oxfmt`
- [x] 2.3 Install and init Husky: `pnpm add -D husky lint-staged`

## 3. App shell and providers

- [x] 3.1 Create `app/shared/lib/api.ts`: Axios instance with `baseURL` from `process.env.API_URL` (server) / `import.meta.env.VITE_API_URL` (browser)
- [x] 3.2 Create `app/shared/lib/queryClient.ts` with a per-request factory (`createQueryClient()`) and a browser-only singleton; wrap root layout with `QueryClientProvider`
- [x] 3.3 Create Zustand cart store at `app/shared/stores/cart.ts`: `number[]` state, persisted to `localStorage` key `pt_carrito`, with `add`, `remove`, `has`, `clear` actions and a `count` selector
- [x] 3.4 Update `app/root.tsx`: mount `<Sonner />` toaster; remove Bootstrap/CDN references from the scaffold template
- [x] 3.5 Build the nav component matching `base.html` layout (Dashboard / Precios / Ahorro / Buscar / Carrito + cart badge driven by the Zustand count selector)
- [x] 3.6 Add one placeholder route (`/`) and a Vitest health-check test asserting the root renders and nav is present

## 4. Test, lint, and hook infrastructure

- [x] 4.1 Create `vitest.config.ts` with `environment: "jsdom"`, `setupFiles: ["./tests/setup.ts"]` (imports `@testing-library/jest-dom`), and `globals: true`; add `test` script
- [x] 4.2 Create `playwright.config.ts` with `webServer` running `pnpm dev`; add one smoke e2e test (loads `/`, nav visible); add `test:e2e` script
- [x] 4.3 Create `.oxlintrc.json` with `recommended` + `react` + `react-hooks` plugins; add `lint` (`oxlint`) and `format` (`oxfmt`) scripts
- [x] 4.4 Run `husky init` from the repo root (not `frontend/`); update `.husky/pre-commit` to `cd frontend && pnpm lint-staged`
- [x] 4.5 Add `lint-staged` config in `frontend/package.json`: `"frontend/**/*.{ts,tsx,js,jsx}": ["oxlint --fix", "oxfmt"]`
- [x] 4.6 Verify: stage a `.tsx` file from repo root and confirm the pre-commit hook runs lint-staged

## 5. Flask JSON API blueprint

- [x] 5.1 Add `flask-cors` to `requirements.txt`; install in the virtualenv
- [x] 5.2 Extract shared data-shaping functions from `app.py` into module-level helpers: the precios matrix builder, the producto chart grouper, `_compute_optimal_cart`
- [x] 5.3 Create `api.py` Flask blueprint (`/api/v1`) with `GET /dashboard`, `GET /precios`, `GET /producto/<int:id>`, `GET /ahorro`, `GET /buscar`, `GET /buscar_carrito`, `POST /carrito`
- [x] 5.4 Register blueprint and `flask-cors` (dev origin from env var `CORS_ORIGIN`) in `app.py`; apply same cache decorators as the HTML routes
- [x] 5.5 Write pytest tests under `tests/` for each new endpoint: status 200, key fields present; test 404 for unknown product
- [x] 5.6 Smoke-test all endpoints with curl: `curl localhost:5000/api/v1/dashboard`, `/precios`, `/producto/1`, `/ahorro`, `/buscar?q=leche`, `POST /carrito {"ids":[1]}`

## 6. Port read-only pages (Dashboard, Precios, Producto)

- [x] 6.1 Create route `app/routes/_index.tsx`: loader calls `GET /api/v1/dashboard`, passes data as TanStack Query `initialData`; render stats, top-cheapest, per-source highlights with day-window selector
- [x] 6.2 Create route `app/routes/precios.tsx`: loader calls `GET /api/v1/precios`, passes data as TanStack Query `initialData`; render paginated table with cheapest-source highlight, category filter, day-window selector
- [x] 6.3 Create route `app/routes/producto.$id.tsx`: loader calls `GET /api/v1/producto/<id>` (404 → error boundary); render Recharts `<LineChart>` with one series per source using the existing source color mapping (dia/#e67e22, anonima/#dc3545, encombo/#0d6efd, carrefour/#004A96); render variants list
- [x] 6.4 Verify: `view-source` on each page contains data (SSR confirms initial HTML); client-side filter/pagination works without a page reload

## 7. Port Search page

- [x] 7.1 Create route `app/routes/buscar.tsx`: loader reads query params and calls `GET /api/v1/buscar` server-side for deep-linked first render
- [x] 7.2 Add debounced search-as-you-type (client-side TanStack Query) that triggers on query/filter changes without loader navigation
- [x] 7.3 Implement source and category filter checkboxes; add "Add to cart" button per result row (updates Zustand store, shows Sonner toast)
- [x] 7.4 Verify: open `/buscar?q=leche` directly — results are present in `view-source`; typing new query updates results without full navigation

## 8. Port Cart page

- [x] 8.1 Create route `app/routes/carrito.tsx`: reads IDs from Zustand store, POSTs to `POST /api/v1/carrito` via TanStack mutation, renders optimal cart grouped by cheapest source with per-source totals and savings
- [x] 8.2 Add cart-search modal: calls `GET /api/v1/buscar_carrito` with TanStack Query; add/remove items from Zustand store
- [x] 8.3 Add "Add to cart" / "Remove from cart" buttons to Precios and Producto pages; cart badge in nav updates reactively
- [x] 8.4 Verify: add products from Precios/Buscar/Producto; reload — cart persists; open `/carrito` — optimal cart computed and grouped correctly

## 9. Docker and docs

- [x] 9.1 Add `frontend` service to `docker-compose.yml` (Node image, runs `pnpm start` / `react-router-serve`; `API_URL` points to Flask service)
- [x] 9.2 Set `VITE_API_URL` for browser client in compose env or `.env.example`
- [x] 9.3 Update README / `docs/` with: how to run both servers locally, how to run frontend tests, compose command for full stack
- [x] 9.4 Full parity walkthrough: run both servers, visit all 6 pages, confirm visual and functional parity with the current Jinja UI (pagination, filters, chart, cart math)
