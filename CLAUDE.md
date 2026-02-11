# Codette Claude Rules

## Core Architecture
- Always preserve dependency direction: `routes -> handlers -> services -> adapters -> models`.
- Routes handle HTTP concerns only.
- Handlers orchestrate use cases and dependency wiring.
- Services contain business logic and coordinate adapter calls.
- Adapters encapsulate external boundaries and repository access.
- Never call repositories or adapters directly from route modules.

## Shared Conventions
- Use Python 3.12+ typing syntax (`list[str]`, `X | None`) and Pydantic v2.
- Pass `db: Session` from `Depends(get_db)` down the stack.
- Never create ad-hoc database sessions in services.
- Access runtime config through `get_settings()`.
- Do not instantiate settings at import time.
- Keep one SQLAlchemy model per file and re-export models from `backend/app/models/__init__.py`.

## Change Checklist
- Register each new router in `backend/app/api/main.py`.
- After model changes, generate an Alembic migration.
- Run `make test` after backend changes.
