# Codette

Mini-LeetCode platform for coding challenges.

## Project Status

> Warning: Codette is under active development and not production-ready.
> API contracts, database schema, and UI behavior may change without notice.
> Expect rough edges and occasional instability while core features evolve.

## Project Structure

```
codette/
├── backend/           # FastAPI backend (API + Worker)
│   ├── app/
│   │   ├── api/       # FastAPI application
│   │   ├── core/      # Shared utilities
│   │   └── worker/    # Background job processor
│   └── migrations/    # Alembic database migrations
├── web/               # React frontend (Vite + TypeScript)
├── jobs/
│   ├── runner/        # Code execution sandbox
│   └── grader/        # Output comparison service
└── infra/             # Docker Compose configuration
```

## Architecture Angle and Style

Codette uses a pragmatic layered architecture with explicit boundaries:

- Backend request flow is intentionally thin and directional:
  `routes -> handlers -> services -> adapters -> models`.
  - Routes own HTTP concerns.
  - Handlers own orchestration and dependency wiring.
  - Services own business logic.
  - Adapters own infrastructure boundaries (DB repositories, storage, task execution).
- Public API contracts are schema-first (Pydantic v2) and expose UUIDs instead of internal DB IDs.
- The evaluation pipeline is asynchronous:
  submission -> queue entry -> worker -> runner job -> grader job -> evaluation.
- Worker execution is adapter-driven:
  - Local mode uses Docker sibling containers (`LocalRunnerAdapter` / `LocalGraderAdapter`).
  - Production-oriented mode can use GCP job adapters.
- Frontend is a React + Vite SPA with route-level pages, shared components, an auth context, and a single fetch abstraction (`useFetch` for reads, `apiFetch` for auth-aware requests).
- Observability is built in via request trace IDs propagated through middleware and logging.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)
- Node.js 20+ (for local development)

### Running Backend Services with Docker Compose

```bash
# Copy environment file
cp .env.example .env

# Start backend services
docker compose -f infra/docker-compose.yml up --build db gcs api worker

# Apply migrations and seed development data
make migrate
make seed

# In another terminal, verify the API:
# API health check
curl http://localhost:8000/health
# Returns: {"status": "ok"}
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| db      | 5432 | PostgreSQL database |
| gcs     | 4443 | Fake GCS server |
| api     | 8000 | FastAPI backend |
| worker  | -    | Background job processor |

### Building Runner/Grader Images

These images are used by the worker pipeline (especially in local E2E runs):

```bash
docker compose -f infra/docker-compose.yml build runner grader
```

## Local Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run API server
uvicorn app.api.main:app --reload

# Run worker (in another terminal)
python -m app.worker.main
```

### Frontend

```bash
cd web

# Install dependencies
npm install

# Start dev server
npm run dev
```

### Database Migrations

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head
```

## Testing

### Backend tests

```bash
make test
```

### End-to-End tests (Playwright)

```bash
# Run with current images
make e2e

# Rebuild e2e image before running
make e2e-build

# Optional: run a subset
E2E_GREP="Auth API|Pipeline" make e2e
```

Current E2E coverage (from `e2e/tests/*.spec.ts`):

- `auth.spec.ts`
  - login success/failure
  - `/auth/me` token validation
  - unauthenticated access rejection
  - invitation-based registration
  - RBAC checks (student cannot create invitations/problems)
- `problems.spec.ts`
  - problem CRUD via UI (create, list, edit, delete)
  - test-case entry in the problem form
  - empty-state behavior
- `submissions.spec.ts`
  - submission list/delete flow
  - submission creation via API and via UI editor
  - monitor-page visibility and problem-link navigation
- `pipeline.spec.ts`
  - full async evaluation path:
    create problem with test cases -> submit code -> monitor shows `passed`
  - queue attempt count visibility in monitor

The Playwright fixture seeds and authenticates dev users (`admin`, `teacher`, `student`) and runs Chromium headless in Docker.

## Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run -a
```

## Environment Variables

See `.env.example` for available configuration options.

| Variable | Default | Description |
|----------|---------|-------------|
| POSTGRES_USER | codette | Database user |
| POSTGRES_PASSWORD | codette | Database password |
| POSTGRES_DB | codette | Database name |
| DATABASE_URL | postgresql://... | Full database URL |
| API_PORT | 8000 | API server port |
| GCS_PORT | 4443 | Fake GCS server port |

## Development Seed Data

```bash
# Requires running API + DB containers
make seed
```

The seed command is idempotent and upserts a small set of sample problems for local development.
