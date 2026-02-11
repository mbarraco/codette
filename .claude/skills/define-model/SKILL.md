# Define SQLAlchemy Model

Create or update a SQLAlchemy 2.0 model following project conventions.

## Base Schema (all tables)

Every table includes these columns automatically:

- `id` — integer, primary key, autoincrement
- `uuid` — uuid4, unique, non-nullable, default generated
- `created_at` — timestamp, non-nullable, server default `now()`
- `updated_at` — timestamp, non-nullable, server default `now()`, on-update `now()`

## Foreign Key Rules

- All foreign keys reference `<table>.id` (the integer PK), never `uuid`.
- Name FK columns `<singular_table>_id` (e.g. `submission_id` → `submissions.id`).
- `uuid` is for external/API exposure only — internal references always use `id`.

## File Conventions

- One file per model in `backend/app/models/`.
- Re-export from `backend/app/models/__init__.py`.
- Use `Mapped` / `mapped_column` syntax.
- After creating or modifying a model, remind the user to generate an Alembic migration.

## Task: $ARGUMENTS
