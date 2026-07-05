# Tasks: prod-docker-build

## 1. API health endpoint

- [x] 1.1 Add `GET /api/v1/health` to `api.py`: `SELECT 1` via the existing `Database`, return `{"status": "ok"}` 200 or 503 on DB failure
- [x] 1.2 Add a test for the health endpoint in `tests/test_api_v1.py` (200 happy path)

## 2. Backend production image (gunicorn)

- [x] 2.1 Add `gunicorn` to `requirements.txt`
- [x] 2.2 Rewrite `Dockerfile` as a two-stage build: builder stage installs deps with `gcc`/`libpq-dev`; runtime stage on `python:3.12-slim` with only `libpq5`, copies installed packages + source
- [x] 2.3 Create non-root `app` user in the runtime stage and set `USER app`
- [x] 2.4 Set CMD to `exec gunicorn -b 0.0.0.0:5000 -w ${GUNICORN_WORKERS:-2} -t ${GUNICORN_TIMEOUT:-60} app:app` (shell form or entrypoint script for env expansion)
- [x] 2.5 Verify the scraper still works with this image (`command: python scheduler.py` override, file permissions on `/app/data` and `/app/logs` for the non-root user) — `app` user created with uid 1000 to match host bind-mount ownership

## 3. Frontend production image hardening

- [x] 3.1 Set `ENV NODE_ENV=production` and `USER node` in the runtime stage of `frontend/Dockerfile`
- [x] 3.2 Replace `CMD ["pnpm", "start"]` with direct node invocation of `react-router-serve ./build/server/index.js` for proper PID 1 signal handling

## 4. Compose orchestration

- [x] 4.1 Add healthcheck to `db` (`pg_isready -U user -d price_tracker`) and `restart: unless-stopped`
- [x] 4.2 Add healthcheck to `app` (python urllib probe of `/api/v1/health`), `restart: unless-stopped`, `depends_on: db: condition: service_healthy`, and optional `GUNICORN_WORKERS`/`GUNICORN_TIMEOUT` env vars
- [x] 4.3 Add healthcheck to `frontend` (wget probe of `:3000/`), `restart: unless-stopped`, `depends_on: app: condition: service_healthy`
- [x] 4.4 Update `scraper` to `depends_on: db: condition: service_healthy`

## 5. Verification

- [x] 5.1 `docker compose build` succeeds for app and frontend
- [x] 5.2 `docker compose up -d` brings all services to healthy state (`docker compose ps`) — fixed frontend CMD to invoke `@react-router/serve/bin.cjs` directly (the `.bin/react-router-serve` shim is a shell script, not runnable by `node`)
- [x] 5.3 Confirm gunicorn workers running and both processes run as non-root (verified via `/proc` since the slim image has no `ps`: master + 2 workers as uid 1000 `app`; frontend as `node`)
- [x] 5.4 Smoke test: `/api/v1/health`, `/api/v1/dashboard?dias=7`, frontend `/` return 200; 4 concurrent requests against the 2-worker gunicorn app all completed in well under 100ms each, confirming no head-of-line blocking
- [x] 5.5 Confirm scraper container starts and logs a scheduler tick — required an explicit `docker compose build scraper` since it shares the Dockerfile with `app` but compose builds/tags it as a separate image
