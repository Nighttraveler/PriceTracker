## Context

The frontend is a React Router v8 SSR SPA (`frontend/`) with TanStack Query, Zustand (cart store, localStorage-persisted under `pt-cart`), Tailwind v4, and shadcn-style base components. (The older "vanilla JS + Bootstrap" description predates the React rewrite in commit `c5c6f16`.)

Current state of the cart-search modal (`frontend/app/routes/carrito.tsx`, `CartSearchModal`):

- `DialogContent` receives `className="max-w-2xl"`, but the shadcn Dialog base (`frontend/app/shared/ui/shadcn/dialog.tsx:64`) sets `max-w-[calc(100%-2rem)] sm:max-w-sm`. Because `max-w-2xl` has no `sm:` variant, tailwind-merge does not dedupe it against `sm:max-w-sm`, and the breakpoint variant wins on desktop → modal capped at 384px on PC while spanning nearly the whole screen on mobile.
- Results render only as a 5-column table inside `overflow-x-auto`, which is unusable at mobile widths.
- `useQuery` keys on the raw input `q`, so every keystroke triggers `GET /api/v1/buscar_carrito`.
- `buscar.tsx` already has a local `useDebounce(value, 300)` hook solving the same problem.

## Goals / Non-Goals

**Goals:**
- Modal renders wide on desktop (`sm:max-w-2xl`) and comfortably within mobile screens.
- Results: table on `sm:`+, stacked cards below `sm:`.
- 300ms debounce on the search input; single shared `useDebounce` hook.
- Previous results stay visible during refetch (no flicker).

**Non-Goals:**
- No changes to the `/api/v1/buscar_carrito` endpoint or any backend/SQL code.
- No redesign of the cart page itself or the optimal-cart section.
- No change to `/buscar` behavior (refactor-only: import the shared hook).

## Decisions

1. **Fix width with `sm:max-w-2xl` instead of overriding the Dialog base component.**
   Changing `dialog.tsx` defaults would affect every dialog in the app; scoping the override to this modal's `className` is safer. Using the same `sm:` variant guarantees tailwind-merge replaces `sm:max-w-sm`.

2. **Dual rendering (cards + table) toggled with Tailwind `hidden sm:block` / `sm:hidden`, not JS media queries.**
   The result set is small (10 per page), so rendering both structures and toggling via CSS is simpler than `matchMedia` hooks and is SSR-safe (no hydration mismatch from window-dependent logic). Both structures map over the same `resultados` array and share the add-button logic.

3. **Extract `useDebounce` to `~/shared/lib/useDebounce.ts` and reuse.**
   The hook already exists verbatim in `buscar.tsx:35-42`. Moving it to shared avoids a second copy; `buscar.tsx` switches to the import with zero behavior change. 300ms matches the existing site-wide convention.

4. **`placeholderData: keepPreviousData` (TanStack Query v5) on the modal query.**
   Keeps the previous page of results rendered while the debounced query refetches, with `isFetching` still available for the "Buscando…" indicator. Alternative (caching only) still blanks the list on new keys.

5. **Keep the initial empty-query fetch.**
   Today opening the modal shows the first 10 products with no query typed; that behavior is retained (no `enabled: q.length > 0` gate) since browsing-from-empty is useful and the endpoint is cheap and uncached by Flask but cached client-side (`staleTime: 60s`).

6. **Cap modal height at `max-h-[85dvh]` with an internally scrollable results area.**
   Found during runtime verification: the shadcn Dialog base sets no max height, so 10 results overflowed the mobile viewport and the add buttons were unreachable. `DialogContent` becomes `flex flex-col max-h-[85dvh]` and the results container `flex-1 min-h-0 overflow-y-auto`, keeping header and input pinned while results scroll.

## Risks / Trade-offs

- [Dual card/table markup duplicates row content] → Both branches map the same data; extract a small shared `AddButton` piece so add/added logic isn't duplicated. Acceptable for a 10-item list.
- [tailwind-merge behavior assumption] → Verify visually at `sm` boundary (640px) after the change; if the base component's `sm:max-w-sm` still leaks through, adjust the Dialog to accept a size override.
- [Debounce hides feedback while typing] → `isFetching` indicator plus kept previous results make the 300ms delay imperceptible.
