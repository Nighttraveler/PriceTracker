## Context

The cart lives in the browser: a list of product IDs in localStorage (zustand `persist`, key `pt_carrito`, `frontend/app/shared/stores/cart.ts`). The cart page (`frontend/app/routes/carrito.tsx`) POSTs those IDs to `/api/carrito`, which returns the optimal split: `carrito` = array of `{ fuente, productos[{ id, nombre, precio, precio_max, ahorro, url, todas_fuentes }], total, ahorro_total }`, plus `productos`, `fuentes`, and `no_encontrados`.

The app is served by Traefik on the home LAN only (`pricetracker.home.arpa`). At the supermarket the phone has no access to it, so the shopping list must be exported to the phone before leaving home and must work fully offline.

The production UI is the React app in `frontend/` (React Router + Vite + zustand), not the legacy Jinja templates.

## Goals / Non-Goals

**Goals:**
- One-tap export of the current optimal cart as a single file usable offline on a phone.
- In-store interactivity: check items off, see per-store remaining subtotal and grand total update.
- Zero dependencies inside the exported file: no network requests, no frameworks, opens in any mobile browser from the file manager.
- No backend changes.

**Non-Goals:**
- Web Share API integration (explicitly ruled out; classic download only).
- CSV/JSON exports (may come later as separate data exports).
- Re-importing an exported file back into the app.
- Guaranteed checkbox-state persistence across file reopens.
- Making the cart page itself work offline (PWA).

## Decisions

**1. Self-contained HTML file over CSV/text.**
The user shops with the file open on the phone and wants to check items off. Only HTML gives interactivity with zero app dependencies. CSV requires a spreadsheet app and mangles Argentine decimal commas; plain text is read-only.

**2. Generate entirely client-side from state already on the page.**
`carrito.tsx` already holds the full `/api/carrito` response. A new pure function (`frontend/app/shared/lib/exportChecklist.ts`) takes that response plus a date and returns the complete HTML string. No new Flask endpoint — keeps the backend untouched and the function trivially unit-testable (string in/string out). Alternative considered: a Flask `GET /api/carrito/export` returning `text/html` — rejected because it duplicates state the page already has and adds a cache/URL-length concern for no benefit.

**3. Delivery: Blob + anchor download, filename `lista-YYYY-MM-DD.html`.**
`URL.createObjectURL(new Blob([html], { type: "text/html" }))` on a temporary `<a download>`. Universally supported; predictable UX (file lands in Downloads).

**4. Inside the file: inline vanilla CSS + one small `<script>`, no external references.**
Mobile browsers open downloads via `file://` (or Android `content://`), where any external fetch fails and CSP is unpredictable. Everything inline. Checkbox logic is a few dozen lines of vanilla JS: toggle a class on row tap, recompute subtotals from `data-precio` attributes.

**5. Checkbox persistence: best-effort localStorage, silent degradation.**
Key: `lista-<exportTimestamp>`; value: array of checked product IDs. Wrapped in try/catch — Android `content://` contexts often deny storage. If storage fails, state is in-memory only, which covers the realistic case (tab stays open during one shopping trip). The UI makes no promise of persistence.

**6. Row = tap target.**
The entire item row toggles the checkbox (no tiny checkbox hit area). Checked rows get strikethrough + reduced opacity and drop out of the store's "remaining" subtotal. Layout uses large text and works in dark mode via `prefers-color-scheme`.

**7. Content of the file.**
Header with title and export date (es-AR format). One section per `fuente` in the optimal split, items sorted as the API returns them (cheapest first), each row showing name and price. Per-store footer: "remaining" (unchecked sum) alongside the fixed store total and total savings. Grand-total footer. Prices formatted as ARS with thousands separators. `no_encontrados` IDs, if any, are noted in a small footer line. Product URLs are intentionally omitted — dead weight offline.

## Risks / Trade-offs

- [Stale prices at the store] → Date stamp in the header makes list age obvious; prices are frozen at export time, which is acceptable within a shopping trip.
- [localStorage unavailable when opened from file manager] → try/catch degradation to in-memory state; feature still fully usable if the tab stays open.
- [User forgets to re-export after editing the cart] → Filename and header carry the date; nothing else feasible without connectivity.
- [HTML string built by concatenation risks broken markup with odd product names] → Escape `&<>"'` in all interpolated text; unit test with names containing quotes/ampersands.
- [Exported file drifts from cart page styling] → Accepted; the export is a utility document, not a themed page. Keep its CSS minimal and independent.

## Open Questions

None — format, delivery mechanism, and persistence stance were settled during exploration.
