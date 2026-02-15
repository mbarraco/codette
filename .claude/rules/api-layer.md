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
- Never expose internal autoincrement `id` fields in schemas — use `uuid` as the external identifier.
- Never accept internal integer foreign keys in request schemas — accept the related resource's `uuid` instead (e.g. `problem_uuid: UUID` not `problem_id: int`).

### Correct schema
```python
# backend/app/api/v1/schemas/submission.py
class SubmissionCreate(BaseModel):
    code: str
    problem_uuid: UUID

class SubmissionResponse(BaseModel):
    uuid: UUID
    artifact_uri: str
    problem_uuid: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### Wrong — exposes internal IDs
```python
class SubmissionCreate(BaseModel):
    code: str
    problem_id: int  # NEVER — accept problem_uuid: UUID instead

class SubmissionResponse(BaseModel):
    id: int           # NEVER — internal ID must not be in API responses
    uuid: UUID
    artifact_uri: str
    problem_id: int   # NEVER — use problem_uuid: UUID instead
    created_at: datetime
```

## Handler Rules
- Accept validated inputs and `db: Session`.
- Build adapter instances in handlers using `get_settings()` when config is required.
- Always delegate business logic to `app/services/*` — never put domain logic in handlers.
- Always commit database transactions in handlers when a write succeeds.
- Return domain models or domain-level errors.
- Never import FastAPI request/response primitives into handlers.
- Handlers are the UUID-to-integer translation layer: accept UUIDs from the API, resolve to internal integer IDs via repositories, and pass integer IDs to services.

### Correct handler
```python
# backend/app/api/v1/handlers/submission.py
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.repository.problem import ProblemRepository
from app.adapters.repository.submission import SubmissionRepository
from app.adapters.storage import StorageAdapter
from app.core.settings import get_settings
from app.models import Submission
from app.services.submission import create_submission

def handle_create_submission(
    db: Session, problem_uuid: uuid.UUID, code: str
) -> Submission:
    problem_repo = ProblemRepository()
    problem = problem_repo.get_by_uuid(db, problem_uuid)
    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem {problem_uuid} not found",
        )

    settings = get_settings()
    storage = StorageAdapter(settings.storage_bucket)
    repo = SubmissionRepository()
    submission = create_submission(db, repo, storage, problem.id, code)
    db.commit()
    submission.problem = problem
    return submission
```

### Wrong — handler accepts internal integer IDs from the API
```python
def handle_create_submission(db: Session, problem_id: int, code: str) -> Submission:
    # NEVER — accept problem_uuid and resolve to integer ID via repository
    ...
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
    submission = handle_create_submission(db, body.problem_uuid, body.code)
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

## Request Tracing Rules
- Every HTTP request is assigned a `trace_id` by `TraceIdMiddleware` in `backend/app/core/middleware.py`.
- The middleware generates a UUID4 hex string, or propagates the client-sent `X-Trace-ID` header.
- The `trace_id` is stored in a `ContextVar` (`backend/app/core/context.py`) and is available for the duration of the request.
- The `trace_id` is returned to the client in the `X-Trace-ID` response header.
- A `TraceIdFilter` in `backend/app/core/logging.py` automatically injects `trace_id` into every log record — no manual passing required.

### Accessing the trace_id in application code
```python
from app.core.context import get_trace_id

trace_id = get_trace_id()  # returns current request's trace_id or "-"
```

### Rules
- Never pass `trace_id` as a function argument through the stack — read it from `get_trace_id()` when needed.
- Never generate trace IDs outside the middleware — the middleware is the single source.
- When making outbound HTTP calls to other services (e.g., worker callbacks), forward the `X-Trace-ID` header to enable distributed tracing.
- Always register `TraceIdMiddleware` in `backend/app/api/main.py` before any routers.

### Wrong — passing trace_id through the stack
```python
def handle_create_submission(db: Session, trace_id: str, ...) -> Submission:  # NEVER
    service_result = create_submission(db, repo, storage, trace_id, ...)      # NEVER
```

### Wrong — generating trace_id in a handler
```python
def handle_create_submission(db: Session, ...) -> Submission:
    trace_id = uuid.uuid4().hex  # NEVER — middleware handles this
```
