# API Layer Rules

## Required Endpoint Pattern
- Every resource must have exactly these three files:
  - `backend/app/api/v1/schemas/<resource>.py`
  - `backend/app/api/v1/handlers/<resource>.py`
  - `backend/app/api/v1/routes/<resource>.py`
- Always register resource routers in `backend/app/api/v1/router.py`.
- Always mount version routers in `backend/app/api/main.py` under `/api/v1`.

### Router registration example
```python
# backend/app/api/v1/router.py
from app.api.v1.routes.submission import router as submission_router

router = APIRouter()
router.include_router(submission_router, prefix="/submissions", tags=["submissions"])
```

## Schema Rules
- Define request and response models with Pydantic v2.
- Always add `model_config = ConfigDict(from_attributes=True)` on response schemas that serialize ORM models.
- Keep schema modules focused on data contracts only — never put logic in schemas.

### Correct schema
```python
# backend/app/api/v1/schemas/submission.py
class SubmissionCreate(BaseModel):
    code: str
    problem_id: int

class SubmissionResponse(BaseModel):
    id: int
    uuid: UUID
    artifact_uri: str
    problem_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

## Handler Rules
- Accept validated inputs and `db: Session`.
- Build adapter instances in handlers using `get_settings()` when config is required.
- Always delegate business logic to `app/services/*` — never put domain logic in handlers.
- Always commit database transactions in handlers when a write succeeds.
- Return domain models or domain-level errors.
- Never import FastAPI request/response primitives into handlers.

### Correct handler
```python
# backend/app/api/v1/handlers/submission.py
from sqlalchemy.orm import Session

from app.adapters.repository.submission import SubmissionRepository
from app.adapters.storage import StorageAdapter
from app.core.settings import get_settings
from app.models import Submission
from app.services.submission import create_submission

def handle_create_submission(db: Session, problem_id: int, code: str) -> Submission:
    settings = get_settings()
    storage = StorageAdapter(settings.storage_bucket)
    repo = SubmissionRepository()
    submission = create_submission(db, repo, storage, problem_id, code)
    db.commit()
    return submission
```

## Route Rules
- Parse HTTP input and validate through schemas.
- Always inject `db` with `Depends(get_db)`.
- Call exactly one handler function and return its result.
- Always put status codes and response models on route decorators.
- Never import repositories, adapters, or settings directly in route modules.
- Never place business logic or SQLAlchemy queries in route functions.

### Correct route
```python
# backend/app/api/v1/routes/submission.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.api.v1.handlers.submission import handle_create_submission
from app.api.v1.schemas.submission import SubmissionCreate, SubmissionResponse

router = APIRouter()

@router.post("/", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def post_submission(
    body: SubmissionCreate,
    db: Session = Depends(get_db),
) -> SubmissionResponse:
    submission = handle_create_submission(db, body.problem_id, body.code)
    return submission
```

### Wrong — business logic in route
```python
# NEVER do this in a route module
@router.post("/")
def post_submission(body: SubmissionCreate, db: Session = Depends(get_db)):
    storage = StorageAdapter(get_settings().storage_bucket)  # NEVER
    path = f"submissions/{uuid4()}/solution.py"              # NEVER — this is business logic
    storage.upload(path, body.code.encode())                 # NEVER
    submission = Submission(problem_id=body.problem_id, artifact_uri=f"gs://bucket/{path}")
    db.add(submission)
    db.commit()
    return submission
```
