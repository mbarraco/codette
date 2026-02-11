# API Layer Rules

## Required Endpoint Pattern
- Always scaffold endpoints with this structure.
- `backend/app/api/schemas/<resource>.py`
- `backend/app/api/handlers/<resource>.py`
- `backend/app/api/routes/<resource>.py`
- Always mount the router in `backend/app/api/main.py`.

## Schema Rules
- Define request and response models with Pydantic v2.
- Use `ConfigDict(from_attributes=True)` on response schemas that serialize ORM models.
- Keep schema modules focused on data contracts only.

## Handler Rules
- Accept validated inputs and `db: Session`.
- Build adapter instances in handlers using `get_settings()` when config is required.
- Delegate business logic to `app/services/*`.
- Commit database transactions in handlers when a write succeeds.
- Return domain models or domain-level errors.
- Never import FastAPI request/response primitives into handlers.

## Route Rules
- Parse HTTP input and validate through schemas.
- Inject `db` with `Depends(get_db)`.
- Call one handler function and return its result.
- Keep status codes and response models on route decorators.
- Never import repositories, adapters, or settings directly in route modules.
- Never place business logic or SQLAlchemy queries in route functions.
