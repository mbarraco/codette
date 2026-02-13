COMPOSE := docker compose --env-file .env -f infra/docker-compose.yml

.PHONY: setup up down build logs ps db-shell \
        up-api up-web up-worker \
        migrate restart clean \
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

test:
	$(COMPOSE) --profile test run --rm test

test-build: ## Rebuild test image, then run tests
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
