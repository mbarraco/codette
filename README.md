# Codette

Mini-LeetCode platform for coding challenges.

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

These are placeholder images for future implementation:

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
