## Why

The cart-search modal on `/carrito` renders at the wrong size on both form factors — capped at 384px on desktop (`max-w-2xl` loses to the Dialog base's `sm:max-w-sm`) and near full-screen on mobile, where its 5-column results table doesn't fit. It also fires a `GET /api/v1/buscar_carrito` request on every keystroke, wasting backend queries and causing result flicker.

## What Changes

- Fix modal width: proper size per breakpoint (wide on desktop via `sm:max-w-2xl`, comfortable on mobile).
- Responsive results layout: stacked cards on mobile (name, category, source chips, min price, add button), table on `sm:` and up.
- Debounce the search input (300ms) so requests fire only after the user stops typing.
- Extract the existing `useDebounce` hook from `frontend/app/routes/buscar.tsx` into `~/shared/lib/useDebounce.ts` and reuse it in both routes.
- Keep previous results visible while a new search is in flight (`placeholderData: keepPreviousData`) to avoid flicker.

No Alembic migration required — frontend-only change, no schema or API changes.
No cached routes affected — `/carrito` and `/api/*` are uncached; `buscar.tsx` changes are refactor-only (same 300ms debounce behavior).
No latest-price queries touched — the `max_por_fuente` CTE and all SQL are unchanged.

## Capabilities

### New Capabilities
- `cart-search`: product search modal on the cart page — responsive layout (cards on mobile, table on desktop), debounced querying, and add-to-cart from results.

### Modified Capabilities

(none — `cart-quick-add` covers the dashboard quick-add button; the modal's behavior was never specified)

## Impact

- `frontend/app/routes/carrito.tsx` — modal sizing, responsive results rendering, debounced query.
- `frontend/app/routes/buscar.tsx` — imports shared `useDebounce` instead of defining it locally (no behavior change).
- `frontend/app/shared/lib/useDebounce.ts` — new shared hook.
- No backend, API, or database changes.
