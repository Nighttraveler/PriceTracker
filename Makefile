.PHONY: up down migrate run test

# Variables
PYTHON := ./venv/bin/python
PYTEST := ./venv/bin/pytest
DOCKER_COMPOSE := docker-compose

# Startup containers
up:
	$(DOCKER_COMPOSE) up -d

# Stop containers
down:
	$(DOCKER_COMPOSE) down

# Run migration
migrate:
	$(PYTHON) scripts/migrate_sqlite_to_postgres.py

# Run application
run:
	$(PYTHON) app.py

# Run tests
test:
	$(PYTEST) tests/
