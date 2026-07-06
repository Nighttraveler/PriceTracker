---
name: verify
description: How to run and drive the price-tracker frontend for runtime verification (dev server + Playwright with system Chromium on the Pi).
---

# Verifying frontend changes (price-tracker)

## Handle

- Backend API is already running in Docker on `http://localhost:5000` (`price-tracker-app-1`); PostgreSQL on :5432. No need to start them.
- Frontend dev server: `cd frontend && npm run dev` → http://localhost:5173 (background it).
- Production serves same-origin via Traefik; in dev, browser calls from :5173 to :5000 are **blocked by CORS**. Launch Chromium with `--disable-web-security` for verification runs.

## Driving with Playwright

- No ms-playwright browsers installed (ARM Pi). Use system Chromium: `executablePath: "/usr/bin/chromium"`.
- `playwright` isn't hoisted (pnpm layout); resolve via `@playwright/test`:
  ```js
  import { createRequire } from "module"
  const require = createRequire("/home/fer/projects/price-tracker/frontend/package.json")
  const { chromium } = require("@playwright/test")
  const browser = await chromium.launch({
    executablePath: "/usr/bin/chromium",
    headless: true,
    args: ["--disable-web-security"], // dev-only CORS bypass
  })
  ```
- Run scripts from anywhere; the createRequire anchor handles resolution.

## Gotchas

- First page load triggers a Vite dependency-optimizer reload mid-session — the page reloads once and can break locators. Load the page once to warm it, or tolerate one reload.
- Cart search modal: `[role=dialog]`; wait for `table tbody tr` (desktop) or `div.sm\\:hidden > div` cards (mobile) instead of fixed timeouts.
- Toasts: `[data-sonner-toast]`.
- Useful flows: `/carrito` → "Buscar" button → modal (search, debounce, add-to-cart); `/buscar` for the search page.
- Pre-existing (as of 2026-07): `npm run typecheck` fails with 1 error in `producto.$id.tsx`; oxlint warns exhaustive-deps in `buscar.tsx`.
