# Proposal: Production Docker Build

## Why

The Flask API currently runs in Docker with the Werkzeug development server (`python app.py`), which is single-threaded and explicitly not meant for production — a single slow request blocks the whole site (this already caused a full outage when a slow dashboard query jammed the SSR frontend). The images also run as root, have no healthchecks, and compose has no restart policies for the app/frontend services.

## What Changes

- Rewrite the backend `Dockerfile` as a production multi-stage build that serves the Flask API with **gunicorn** (multiple workers, sensible timeouts) instead of `python app.py`.
- Harden the frontend `Dockerfile` for production: `NODE_ENV=production`, non-root user, healthcheck-friendly runtime (keep the existing multi-stage `react-router-serve` setup).
- Update `docker-compose.yml` for production operation:
  - `restart: unless-stopped` on all services.
  - Healthchecks for `db` (pg_isready), `app` (HTTP), and `frontend` (HTTP).
  - `depends_on` with `condition: service_healthy` so the frontend SSR never starts before the API is ready.
  - Gunicorn worker/timeout configuration via environment variables.
- Run app and frontend containers as non-root users.
- No application code changes except (if needed) a lightweight health endpoint on the Flask API for the healthcheck.

**No Alembic migration required** — no schema changes.
**No cached-route or latest-price-query changes** — serving layer only; Flask routes and SQL are untouched.

## Capabilities

### New Capabilities
- `production-deployment`: How the API, frontend, scraper, and DB are built and served in production — WSGI server, process model, container hardening, healthchecks, and compose orchestration.

### Modified Capabilities

(none — no existing spec covers deployment)

## Impact

- `Dockerfile` (backend/scraper image — shared by `app` and `scraper` services): rewritten; gunicorn added to `requirements.txt`.
- `frontend/Dockerfile`: hardened (non-root, NODE_ENV).
- `docker-compose.yml`: restart policies, healthchecks, dependency conditions.
- `app.py`: possibly a `/api/v1/health` endpoint if none exists.
- Scraper service keeps `python scheduler.py` as its command — gunicorn only applies to the web API.
- Traefik labels and networking stay as-is.
