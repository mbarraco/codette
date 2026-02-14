COMPOSE := docker compose -f infra/docker-compose.yml
TEST_DB_NAME ?= codette_test
E2E_DB_NAME ?= codette_e2e

.PHONY: setup up down build logs ps db-shell \
        up-api up-worker \
        migrate seed restart clean setup-tests \
        test test-build test-shell \
        e2e e2e-build

## ---------- First-time setup ----------

setup: .env build up migrate ## Set up the dev environment from scratch

.env:
	cp .env.example .env

## ---------- Core lifecycle ----------

build: ## Build all service images
	$(COMPOSE) build

up: ## Start all services (detached)
	$(COMPOSE) up -d

down: ## Stop all services
	$(COMPOSE) down

restart: ## Restart all services
	$(COMPOSE) restart

clean: ## Stop services and remove volumes
	$(COMPOSE) down -v

## ---------- Individual services ----------

up-api: ## Start only API + DB
	$(COMPOSE) up -d api

up-worker: ## Start only Worker + DB
	$(COMPOSE) up -d worker

## ---------- Utilities ----------

logs: ## Tail logs for all services
	$(COMPOSE) logs -f

ps: ## Show running services
	$(COMPOSE) ps

db-shell: ## Open a psql shell
	$(COMPOSE) exec db psql -U $${POSTGRES_USER:-codette} -d $${POSTGRES_DB:-codette}

migrate: ## Run Alembic migrations inside the API container
	$(COMPOSE) exec api alembic upgrade head

seed: migrate ## Seed development data inside the API container (idempotent)
	$(COMPOSE) exec api sh -lc 'PYTHONPATH=/app python /app/scripts/dev/seed_dev_data.py'

## ---------- Tests ----------

setup-tests: .env ## Ensure test dependencies are up and test database exists
	$(COMPOSE) up -d db gcs
	$(COMPOSE) exec -T db sh -c '/scripts/wait-for-pg.sh && /scripts/ensure-db.sh $(TEST_DB_NAME)'

test: setup-tests
	$(COMPOSE) --profile test run --rm test

test-build: setup-tests ## Rebuild test image, then run tests
	$(COMPOSE) --profile test run --rm --build test

test-shell: ## Open a bash shell in the test container
	$(COMPOSE) --profile test run --rm --entrypoint /bin/bash test

## ---------- E2E tests ----------

e2e: .env ## Run Playwright end-to-end tests in Docker
	E2E_DB_NAME=$(E2E_DB_NAME) sh ./scripts/run-e2e.sh run

e2e-build: .env ## Rebuild e2e image, then run Playwright tests
	E2E_DB_NAME=$(E2E_DB_NAME) sh ./scripts/run-e2e.sh build

## ---------- Tool images ----------

build-tools: ## Build runner and grader images
	$(COMPOSE) --profile tools build

## ---------- Help ----------

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
