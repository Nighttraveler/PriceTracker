## 1. Export HTML generator

- [x] 1.1 Create `frontend/app/shared/lib/exportChecklist.ts` with a pure function that takes the `/api/carrito` response (optimal split, `no_encontrados`) and an export date, and returns the complete self-contained HTML string (inline CSS + vanilla JS, no external references)
- [x] 1.2 Implement HTML escaping for all interpolated text (product names, store names) and ARS price formatting with thousands separators
- [x] 1.3 Implement the checklist layout: date-stamped header, one section per store with item rows (name + price), per-store fixed total and savings, grand total, and a footer note for unresolved IDs
- [x] 1.4 Implement the inline script: row tap toggles checked state (strikethrough + opacity), recomputes per-store "remaining" subtotals and grand remaining total from `data-precio` attributes
- [x] 1.5 Implement best-effort persistence: save/restore checked product IDs in `localStorage` keyed by export timestamp, wrapped in try/catch with silent in-memory fallback
- [x] 1.6 Add dark-mode support via `prefers-color-scheme` and large tap-friendly row styling

## 2. Cart page integration

- [x] 2.1 Add a "Download list" button to `frontend/app/routes/carrito.tsx`, enabled only when the optimal split has at least one product
- [x] 2.2 Wire the button to build the HTML via `exportChecklist.ts` and trigger a Blob + anchor download named `lista-YYYY-MM-DD.html`

## 3. Tests and verification

- [x] 3.1 Unit tests (vitest) for the generator: multi-store split renders both sections and correct totals; names with `&`, `<`, `"` are escaped; empty `no_encontrados` produces no footer note; ARS formatting
- [x] 3.2 Runtime verification per the `verify` skill: add products to the cart, download the file, open it standalone in Chromium, and confirm offline rendering, row toggling with live remaining totals, and no console errors or network requests
- [x] 3.3 Verify the empty-cart state disables/hides the button
