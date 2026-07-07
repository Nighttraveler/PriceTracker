## Why

The cart page (`/carrito`) computes the optimal per-supermarket shopping split, but the app is only reachable on the home LAN. Once at the store, the user has no access to the list. We need a way to take a snapshot of the cart to the phone that works fully offline, with no app dependencies, and supports checking items off while shopping.

## What Changes

- Add a **"Download list" button** to the cart page in the React frontend (`frontend/app/routes/carrito.tsx`).
- The button generates a **self-contained HTML checklist file** entirely client-side from the `/api/carrito` response already held in page state:
  - One section per supermarket (the optimal split), listing each item with its price.
  - Tap-anywhere-on-row checkboxes with strikethrough for purchased items.
  - Live per-store "remaining" subtotal and grand total that update as items are checked.
  - Date-stamped header so a stale list is recognizable.
  - Inline vanilla CSS/JS only — no external requests, works from `file://`/`content://` in any mobile browser.
- Delivery is a classic Blob + anchor download named `lista-YYYY-MM-DD.html`. Web Share API was considered and explicitly ruled out.
- Checkbox state persists best-effort via `localStorage` keyed by export timestamp, silently degrading to in-memory state when storage is unavailable (common when opened from a file manager).

## Capabilities

### New Capabilities
- `cart-export`: exporting the optimal cart as an offline, self-contained HTML shopping checklist downloaded from the cart page.

### Modified Capabilities

None — the cart computation, API, and persistence requirements are unchanged.

## Impact

- **Frontend only**: `frontend/app/routes/carrito.tsx` plus a new module that builds the export HTML string (e.g. `frontend/app/shared/lib/exportChecklist.ts`). No changes to the Flask API, `db.py`, or templates.
- **No Alembic migration required** — no schema changes; the export reads data already returned by `POST /api/carrito`.
- **No cached routes affected** (`/`, `/precios`, `/ahorro`, `/buscar` untouched; `/carrito` and `/api/*` are uncached and unchanged).
- **No latest-price queries touched** — the `max_por_fuente` CTE logic is not modified; the export consumes the existing optimal-cart response.
- Note: the OpenSpec project context describes a Jinja2/vanilla-JS frontend, but the production UI served via Traefik is the React app in `frontend/` (docker-compose `frontend` service, port 3000). This change targets the React app.
