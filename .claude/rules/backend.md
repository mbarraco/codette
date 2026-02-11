# Backend Architecture Rules

## Layer Layout
- Use this backend layout under `backend/app/`: `api/`, `services/`, `adapters/`, `worker/`, `models/`, `core/`.
- Keep dependency flow inward: `api -> handlers -> services -> adapters -> models`.
- Keep worker orchestration in `backend/app/worker/` and inject dependencies through constructors.

## API and Handler Boundaries
- Route modules in `backend/app/api/routes/` must stay thin and HTTP-only.
- Handler modules in `backend/app/api/handlers/` orchestrate use cases and service calls.
- Handlers may call multiple services or adapters when a use case requires it.

## Service Rules
- Services are framework-agnostic and contain business logic.
- Service functions must accept explicit dependencies (`db`, repository instances, external adapters).
- Services must not import FastAPI types.

## Adapter Rules
- Put all SQLAlchemy query logic in `backend/app/adapters/repository/` modules.
- Use one repository file per model or aggregate.
- Keep external systems (storage, job runners, third-party APIs) in dedicated adapter files.
- Prefer concrete adapters first.
- Introduce protocols or interfaces only when multiple implementations are required.

## Settings and Environments
- Define settings in `backend/app/core/settings.py` using `pydantic-settings`.
- Use separate settings classes for app and tests.
- Read settings through lazy `get_settings()` access.
- Fail fast on missing required settings by avoiding silent defaults for required fields.
