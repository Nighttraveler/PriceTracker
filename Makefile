.PHONY: up down restart build migrate run test psql help

# Variables
PYTHON := ./venv/bin/python
PYTEST := ./venv/bin/pytest
DOCKER_COMPOSE := docker-compose
DB_URL := postgresql://user:password@localhost:5432/price_tracker

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

up: ## Start containers in background
	$(DOCKER_COMPOSE) up -d

down: ## Stop containers
	$(DOCKER_COMPOSE) down

build: ## Build (or rebuild) Docker images
	$(DOCKER_COMPOSE) build

restart: down build ## Rebuild images and restart all containers
	$(DOCKER_COMPOSE) up -d

migrate: ## Migrate SQLite data to PostgreSQL
	$(PYTHON) scripts/migrate_sqlite_to_postgres.py

run: ## Run the web dashboard (http://0.0.0.0:5000)
	$(PYTHON) app.py

test: ## Run unit tests (no network)
	$(PYTEST) tests/ -m "not integration"

psql: ## Open a psql shell to the PostgreSQL container (use Q="..." for one-off queries)
	@if [ -n "$(Q)" ]; then \
		$(DOCKER_COMPOSE) exec db psql -U user price_tracker -c "$(Q)"; \
	else \
		$(DOCKER_COMPOSE) exec -it db psql -U user price_tracker; \
	fi
