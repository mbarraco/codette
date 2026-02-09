# Codette Backend

FastAPI backend with API server and background worker.

## Structure

- `app/api/` - FastAPI application
- `app/worker/` - Background worker for job processing
- `app/core/` - Shared utilities (settings, logging, database)
- `migrations/` - Alembic database migrations

## Development

### Local Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Run API server
uvicorn app.api.main:app --reload

# Run worker
python -m app.worker.main
```

### Docker

The Dockerfile supports multi-target builds:

```bash
# Build API image
docker build --target api -t codette-api .

# Build worker image
docker build --target worker -t codette-worker .
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```
