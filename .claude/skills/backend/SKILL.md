# Backend Development Skill

You are working on a **FastAPI + SQLAlchemy + PostgreSQL** backend.

## Architecture

The backend follows a layered architecture. Dependencies flow inward: **API → Handler → Adapters → Models**.

```
app/
  api/             # API layer: routers, request/response schemas
  handlers/        # Handler layer: use-case / business logic orchestration
  adapters/        # Adapters layer: all external boundaries
    repository/    #   DB access (one file per model)
    ...            #   Other adapters: storage, job runners, external APIs
  worker/          # Worker layer: long-running orchestrators
  models/          # Domain models: SQLAlchemy ORM models
  core/            # Cross-cutting: settings, db session, logging
```

### Layers

1. **API** (`app/api/`) — Thin FastAPI routers. Parse HTTP input, validate with Pydantic schemas, delegate to a handler, return a response. No business logic, no direct DB access.

2. **Handler** (`app/handlers/`) — Orchestrates use cases. Receives validated data from the API layer, applies business rules, and calls one or more adapters. Returns domain models or raises domain errors.

3. **Adapters** (`app/adapters/`) — All external boundaries live here. Two categories:

   - **Repositories** (`app/adapters/repository/`) — Encapsulate all SQLAlchemy queries. One file per model. Receive `Session` as a method argument. Never imported by the API layer directly.
   - **External adapters** (storage, job runners, third-party APIs) — Each adapter is its own file under `app/adapters/`. Same adapter class can serve multiple environments when the difference is just config (e.g. storage endpoint URL). Use separate implementations only when the mechanics genuinely differ (e.g. local docker exec vs cloud job API).

4. **Worker** (`app/worker/`) — Long-running orchestrators. Receive adapters and `db: Session` via constructor injection. Own the processing flow, not the infrastructure details.

5. **Models** (`app/models/`) — SQLAlchemy 2.0 `DeclarativeBase` models using `Mapped` / `mapped_column`. One file per table, re-export from `__init__.py`. Models serve as domain entities — intentional coupling of domain and persistence for pragmatism.

### Adapter conventions

- Adapters are **concrete classes, not abstract interfaces**. Introduce a Protocol only when a second implementation is needed.
- Environment-specific wiring uses an `ENVIRONMENT` setting with a factory function to select the right adapter implementation.
- Repositories receive `Session` as a method argument. External adapters are configured at construction time.

### Settings & environments

- Settings live in `app/core/settings.py` using `pydantic-settings`.
- Separate settings classes per environment context (e.g. `Settings` for app, `TestSettings` for tests), each reading from its own `.env` file.
- App code accesses settings via a lazy `get_settings()` function (cached with `lru_cache`), never via a module-level singleton. This prevents import-time side effects.
- Required values (like `database_url`) have no defaults — missing config fails loudly at startup.

### General conventions

- Python 3.12+, modern type hints (`list[str]`, `X | None`).
- Pydantic v2 schemas live next to the router that uses them (e.g. `api/schemas/`).
- DB sessions enter via `Depends(get_db)` in the API layer and are passed down.
- Route files export an `APIRouter` and are mounted in `app/api/main.py`.
- After creating or modifying models, remind the user to generate an Alembic migration.

## Task: $ARGUMENTS

1. Read the relevant existing files before making changes.
2. Create or update code following the layer responsibilities above.
3. Register any new routers in `app/api/main.py`.
4. After modifying models, remind the user to run an Alembic migration.
