# Model Rules

## Base Columns
- Every table model must inherit the shared base mixin that provides `id`, `uuid`, `created_at`, and `updated_at`.
- `id` is the internal primary key and must be an autoincrement integer.
- `uuid` is externally visible and must be unique and non-null.
- `created_at` and `updated_at` must use database-side timestamps from `func.now()`.

## Foreign Key Rules
- Always reference `<table>.id` in foreign keys.
- Never reference `uuid` in foreign keys.
- Name foreign key columns `<singular_table>_id`.

## File and Export Rules
- Keep one model per file under `backend/app/models/`.
- Use SQLAlchemy 2.0 typed mappings (`Mapped`, `mapped_column`).
- Re-export new model classes from `backend/app/models/__init__.py`.

## Migration Rule
- After creating or modifying models, generate an Alembic migration.
