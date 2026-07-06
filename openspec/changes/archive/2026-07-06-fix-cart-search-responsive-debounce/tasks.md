## 1. Shared debounce hook

- [x] 1.1 Create `frontend/app/shared/lib/useDebounce.ts` with the `useDebounce<T>(value, delay)` hook currently defined in `frontend/app/routes/buscar.tsx:35-42`
- [x] 1.2 Update `buscar.tsx` to import the shared hook and remove its local definition (no behavior change)

## 2. Debounced cart search

- [x] 2.1 In `CartSearchModal` (`frontend/app/routes/carrito.tsx`), derive `debouncedQ = useDebounce(q, 300)` and use it in the `useQuery` key and request URL
- [x] 2.2 Add `placeholderData: keepPreviousData` (from `@tanstack/react-query`) to the modal query so previous results stay visible while fetching
- [x] 2.3 Verify typing still resets `page` to 1 and the pagination footer reflects the debounced query's totals

## 3. Responsive modal layout

- [x] 3.1 Change the modal's `DialogContent` className from `max-w-2xl` to `sm:max-w-2xl` so it overrides the Dialog base `sm:max-w-sm` on desktop
- [x] 3.2 Keep the existing results table but render it only on `sm:`+ (`hidden sm:block` on its container)
- [x] 3.3 Add a stacked-card list for mobile (`sm:hidden`): each card shows product name, category, source chips, minimum price, and the add/added control
- [x] 3.4 Extract the add/added control into a small shared component (or inline function) used by both the table row and the mobile card

## 4. Verification

- [x] 4.1 Run `/verify` or manually exercise the flow: desktop ≥640px shows a ~672px-wide modal with the table; mobile <640px shows cards with no horizontal scroll
- [x] 4.2 Confirm in the browser network tab that typing a word quickly produces a single `/api/v1/buscar_carrito` request ~300ms after the last keystroke
- [x] 4.3 Confirm no flicker: previous results remain visible with the "Buscando…" indicator during refetch
- [x] 4.4 Confirm adding a product from both layouts updates the cart store, shows the toast, and closes the modal; `npm run build` (or the frontend typecheck) passes
