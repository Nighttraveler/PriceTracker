# Spec: production-deployment

## Purpose

Defines how the price-tracker stack is packaged and run in production: the API's WSGI
server, health checks, container hardening, compose orchestration, and the scraper's
entrypoint.

## Requirements

### Requirement: API served by a production WSGI server
The Flask API container SHALL serve the application with gunicorn instead of the Werkzeug development server. Gunicorn SHALL run with more than one worker so a single slow request cannot block all other requests, and worker count and timeout SHALL be configurable via environment variables (`GUNICORN_WORKERS`, `GUNICORN_TIMEOUT`) with sensible defaults.

#### Scenario: Concurrent requests during a slow query
- **WHEN** one API request is executing a slow database query
- **THEN** other API requests are still served by the remaining gunicorn workers

#### Scenario: Default startup
- **WHEN** the `app` container starts with no gunicorn env vars set
- **THEN** gunicorn binds to `0.0.0.0:5000` with the default worker count and timeout

### Requirement: API health endpoint
The Flask API SHALL expose `GET /api/v1/health` returning HTTP 200 with a JSON body when the app can reach the database. The endpoint MUST NOT be cached.

#### Scenario: Healthy service
- **WHEN** `GET /api/v1/health` is requested and the database is reachable
- **THEN** the API responds 200 with `{"status": "ok"}`

#### Scenario: Database unreachable
- **WHEN** `GET /api/v1/health` is requested and the database connection fails
- **THEN** the API responds with a non-200 status

### Requirement: Production container images
Backend and frontend images SHALL be production-hardened: they MUST run as a non-root user, MUST NOT include build-only toolchains in the final image (multi-stage builds), and the frontend runtime MUST set `NODE_ENV=production`.

#### Scenario: Non-root runtime
- **WHEN** either container is running
- **THEN** the main process runs as a non-root user

#### Scenario: Frontend production mode
- **WHEN** the frontend container starts
- **THEN** the React Router SSR server runs with `NODE_ENV=production` serving the pre-built bundle

### Requirement: Compose orchestration with healthchecks
`docker-compose.yml` SHALL define healthchecks for `db`, `app`, and `frontend`, apply `restart: unless-stopped` to all services, and start the frontend only after the API is healthy (`depends_on` with `condition: service_healthy`).

#### Scenario: Startup ordering
- **WHEN** the stack is started with `docker compose up -d`
- **THEN** the frontend container starts only after the `app` healthcheck passes, and `app` starts only after the `db` healthcheck passes

#### Scenario: Crash recovery
- **WHEN** any service process exits unexpectedly
- **THEN** Docker restarts the container automatically

### Requirement: Scraper keeps its own entrypoint
The scraper service SHALL continue to run `python scheduler.py` using the shared backend image; gunicorn applies only to the web API service.

#### Scenario: Scraper startup
- **WHEN** the `scraper` container starts
- **THEN** it runs the scheduler process, not gunicorn
