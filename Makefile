COMPOSE := docker compose -f infra/docker-compose.yml
TEST_DB_NAME ?= codette_test
E2E_DB_NAME ?= codette_e2e

.PHONY: setup up down build logs ps db-shell \
        up-api up-web up-worker \
        migrate seed restart clean setup-tests \
        test test-build test-shell \
        setup-e2e e2e e2e-build

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

up-web: ## Start only Web + API + DB
	$(COMPOSE) up -d web

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

setup-e2e: .env ## Reset e2e database (drop + recreate)
	$(COMPOSE) --profile e2e stop api-e2e web-e2e 2>/dev/null || true
	$(COMPOSE) up -d db gcs
	$(COMPOSE) exec -T db sh -c '/scripts/wait-for-pg.sh && /scripts/reset-db.sh $(E2E_DB_NAME)'

e2e: setup-e2e ## Run Playwright end-to-end tests in Docker
	$(COMPOSE) --profile e2e run --rm e2e

e2e-build: setup-e2e ## Rebuild e2e image, then run Playwright tests
	$(COMPOSE) --profile e2e run --rm --build e2e

## ---------- Tool images ----------

build-tools: ## Build runner and grader images
	$(COMPOSE) --profile tools build

## ---------- Help ----------

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
