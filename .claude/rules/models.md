# Model Rules

## Base Columns
- Every table model must inherit `BaseMixin` and `Base` from `app.models.base`.
- `BaseMixin` provides `id`, `uuid`, `created_at`, and `updated_at` — never redefine these columns.
- `id` is the internal primary key and must be an autoincrement integer.
- `uuid` is externally visible and must be unique and non-null.
- `created_at` and `updated_at` must use database-side timestamps from `func.now()`.

### BaseMixin definition (from `backend/app/models/base.py`)
```python
class BaseMixin:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[_uuid.UUID] = mapped_column(
        unique=True, nullable=False, default=_uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
```

## Foreign Key Rules
- Always reference `<table>.id` in foreign keys — never reference `uuid`.
- Always name foreign key columns `<singular_table>_id`.

### Correct model with foreign key
```python
# backend/app/models/submission.py
class Submission(BaseMixin, Base):
    __tablename__ = "submissions"

    artifact_uri: Mapped[str] = mapped_column(Text, nullable=False)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), nullable=False)
```

### Wrong — FK references uuid
```python
problem_uuid: Mapped[UUID] = mapped_column(ForeignKey("problems.uuid"))  # NEVER
```

## Relationship Rules
- Always set `lazy="noload"` on relationships — eager loading must be explicit in repository queries.
- Use string forward references for related model types.

### Correct relationship
```python
runs: Mapped[list["Run"]] = relationship(back_populates="submission", lazy="noload")
```

### Wrong — default lazy loading
```python
runs: Mapped[list["Run"]] = relationship(back_populates="submission")  # NEVER — implicit lazy="select"
```

## File and Export Rules
- Keep exactly one model per file under `backend/app/models/`.
- Always use SQLAlchemy 2.0 typed mappings (`Mapped`, `mapped_column`).
- Always re-export new model classes from `backend/app/models/__init__.py`.

### Re-export pattern
```python
# backend/app/models/__init__.py
from .base import Base, BaseMixin
from .problem import Problem
from .run import Run
from .submission import Submission

__all__ = ["Base", "BaseMixin", "Problem", "Run", "Submission"]
```

## Migration Rule
- Always generate an Alembic migration after creating or modifying models.
