COMPOSE := docker compose -f infra/docker-compose.yml
TEST_DB_NAME ?= codette_test

.PHONY: setup up down build logs ps db-shell \
        up-api up-web up-worker \
        migrate restart clean setup-tests \
        test test-build test-shell

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

## ---------- Tests ----------

setup-tests: .env ## Ensure test dependencies are up and test database exists
	$(COMPOSE) up -d db gcs
	$(COMPOSE) exec -T db sh -lc 'until pg_isready -U "$${POSTGRES_USER:-codette}" -d "$${POSTGRES_DB:-codette}" >/dev/null 2>&1; do sleep 1; done'
	$(COMPOSE) exec -T db sh -lc 'if ! psql -U "$${POSTGRES_USER:-codette}" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '\''$(TEST_DB_NAME)'\''" | grep -q 1; then psql -v ON_ERROR_STOP=1 -U "$${POSTGRES_USER:-codette}" -d postgres -c "CREATE DATABASE $(TEST_DB_NAME)"; fi'

test: setup-tests
	$(COMPOSE) --profile test run --rm test

test-build: setup-tests ## Rebuild test image, then run tests
	$(COMPOSE) --profile test run --rm --build test

test-shell: ## Open a bash shell in the test container
	$(COMPOSE) --profile test run --rm --entrypoint /bin/bash test

## ---------- Tool images ----------

build-tools: ## Build runner and grader images
	$(COMPOSE) --profile tools build

## ---------- Help ----------

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
