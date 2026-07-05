# Design: Production Docker Build

## Context

The stack runs four compose services: `db` (postgres:16-alpine), `app` (Flask JSON API), `frontend` (React Router v8 SSR via `react-router-serve`), and `scraper` (shares the backend image, runs `scheduler.py`). Today:

- The backend `Dockerfile` is single-stage, runs as root, and its CMD is `python app.py` — the Werkzeug dev server, single-threaded. A slow query recently blocked every request and took the site down (frontend SSR has a 10s timeout on its API calls).
- The frontend `Dockerfile` is already multi-stage (deps → build → runtime) with `react-router-serve` on the built bundle, but runs as root and doesn't set `NODE_ENV=production`.
- `docker-compose.yml` has plain `depends_on` (no health conditions), no healthchecks, and no restart policy on `app`/`frontend`.
- Traefik (external compose stack) routes `pricetracker.home.arpa` → frontend:3000.

## Goals / Non-Goals

**Goals:**
- Serve the Flask API with gunicorn (multi-worker) in the container.
- Non-root, multi-stage production images for backend and frontend.
- Healthchecks + ordered startup + automatic restarts in compose.
- A `/api/v1/health` endpoint that verifies DB connectivity.

**Non-Goals:**
- No change to Traefik routing, networks, or TLS.
- No change to application logic, SQL, caching, or scraper behavior.
- No Kubernetes/registry/CI pipeline work — local `docker compose build` remains the deployment method.
- No dev/prod compose split (the current compose file becomes the production one; local dev uses the existing `pnpm dev` / `python app.py` outside Docker).

## Decisions

1. **Gunicorn with sync workers, default `workers=2` (Pi has 4 cores, shared with SSR + Postgres + scraper), `timeout=60`.**
   Configurable via `GUNICORN_WORKERS` / `GUNICORN_TIMEOUT` env vars read in the CMD: `gunicorn -b 0.0.0.0:5000 -w ${GUNICORN_WORKERS:-2} -t ${GUNICORN_TIMEOUT:-60} app:app`. Sync workers over gevent/uvicorn: the app is psycopg2 + SimpleCache, both incompatible with async without extra work; multiple sync workers already solve the head-of-line blocking problem. Shell-form CMD (or an entrypoint script) is required for env expansion.
   *Note:* SimpleCache is per-process, so each worker keeps its own cache. Acceptable — cache is a TTL read cache, worst case N cold fills.

2. **Backend image: two-stage build.** Stage 1 (`python:3.12-slim` + `gcc`, `libpq-dev`) installs requirements into a venv or `--prefix`; stage 2 copies only the installed packages + app source, installs `libpq5` runtime lib only, creates an `app` user (`useradd -r`), `USER app`. Gunicorn added to `requirements.txt`. The same image keeps serving the `scraper` service — its compose `command: python scheduler.py` overrides the gunicorn CMD, so nothing changes for it. `curl` (or use python urllib) must be available for the healthcheck; prefer a tiny `HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/v1/health')"` to avoid installing curl.

3. **Health endpoint in `api.py` blueprint** (`/api/v1/health`): runs `SELECT 1` through the existing `Database` handle; returns `{"status": "ok"}` 200 or 503 on failure. Lives under `/api/v1` so it's excluded from Flask caching by the existing convention and reachable through CORS config untouched (GET only).

4. **Frontend image hardening, not rewrite.** Keep deps/build/runtime stages. In runtime stage: `ENV NODE_ENV=production`, run as the existing `node` user (`USER node`), and replace `pnpm start` with `node ./node_modules/.bin/react-router-serve ./build/server/index.js` — direct node invocation avoids pnpm as PID 1 and gives correct signal handling. Healthcheck uses `wget -qO- http://localhost:3000/` (busybox wget is in alpine) — but note `/` triggers an SSR API call; a HEAD/`GET /` is acceptable at 30s intervals given the dashboard endpoint is now fast; interval/timeout tuned generously (interval 30s, timeout 10s, retries 3, start_period 20s).

5. **Compose changes:**
   - `db`: healthcheck `pg_isready -U user -d price_tracker`; `restart: unless-stopped`.
   - `app`: healthcheck via the Dockerfile HEALTHCHECK (compose inherits it) or explicit compose healthcheck (explicit preferred — visible in one place); `depends_on: db: condition: service_healthy`; `restart: unless-stopped`.
   - `frontend`: `depends_on: app: condition: service_healthy`; `restart: unless-stopped`.
   - `scraper`: `depends_on: db: condition: service_healthy`; keeps `restart: unless-stopped`.
   - Add `GUNICORN_WORKERS`/`GUNICORN_TIMEOUT` (optional, defaulted) to `app` environment.

## Risks / Trade-offs

- [Gunicorn workers each open their own Postgres connection] → 2–4 sync workers ≈ 2–4 connections; Postgres default max_connections=100, no pooler needed at this scale.
- [Per-worker SimpleCache multiplies cold-cache misses] → acceptable; if it hurts, switch to `flask-caching` filesystem/redis backend later (out of scope).
- [Healthcheck on `/` of the SSR frontend exercises the API on every probe] → generous interval (30s) and the dashboard endpoint is now milliseconds; alternatively probe a static asset if this proves noisy.
- [`condition: service_healthy` delays startup] → start_period tuned so cold boot still comes up in well under a minute.
- [Shell-form gunicorn CMD means shell is PID 1] → use `exec gunicorn ...` in the CMD/entrypoint so gunicorn replaces the shell and receives signals.

## Migration Plan

1. `docker compose build app frontend` (scraper reuses the app image).
2. `docker compose up -d` — compose recreates changed containers; brief API downtime (~seconds) while `app` restarts.
3. Verify: `curl http://localhost:5000/api/v1/health`, `curl http://localhost:3000/`, `docker compose ps` shows all healthy.
4. Rollback: `git checkout` the previous Dockerfiles/compose and `docker compose up -d --build`.

## Open Questions

- None blocking. (Worker count default of 2 can be revisited once real memory usage on the Pi is observed.)
