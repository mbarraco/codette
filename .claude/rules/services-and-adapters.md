# Service and Adapter Rules

## Service Rules
- Services live in `backend/app/services/` — one file per domain concept.
- Services must be framework-agnostic — never import FastAPI types.
- Service functions must accept all dependencies as explicit arguments (`db`, repository instances, external adapters).
- Never create database sessions inside services — always receive `db: Session` from the caller.
- Never commit transactions in services — the handler is responsible for committing.

### Correct service function
```python
# backend/app/services/submission.py
import uuid

from sqlalchemy.orm import Session

from app.adapters.repository.submission import SubmissionRepository
from app.adapters.storage import StorageAdapter
from app.models import Submission

def create_submission(
    db: Session,
    repo: SubmissionRepository,
    storage: StorageAdapter,
    problem_id: int,
    code: str,
) -> Submission:
    """Upload code to storage and create a Submission row."""
    submission_uuid = uuid.uuid4()
    path = f"submissions/{submission_uuid}/solution.py"
    artifact_uri = storage.upload(path, code.encode())
    return repo.create(db, problem_id=problem_id, artifact_uri=artifact_uri)
```

### Wrong — service creates its own dependencies
```python
def create_submission(db: Session, problem_id: int, code: str) -> Submission:
    settings = get_settings()                         # NEVER — inject adapter from handler
    storage = StorageAdapter(settings.storage_bucket)  # NEVER
    repo = SubmissionRepository()                      # NEVER
    ...
```

### Wrong — service commits transaction
```python
def create_submission(db: Session, repo, storage, problem_id, code) -> Submission:
    submission = repo.create(db, problem_id=problem_id, artifact_uri=uri)
    db.commit()  # NEVER — handler must commit
    return submission
```

## Repository Rules
- All SQLAlchemy query logic must live in `backend/app/adapters/repository/` — one file per model or aggregate.
- Repository classes must accept `db: Session` on each method — never store session state.
- Always use `db.flush()` (not `db.commit()`) after inserts to get generated IDs.
- Always use `selectinload()` for eager loading relationships in list queries.

### Correct repository
```python
# backend/app/adapters/repository/submission.py
from sqlalchemy.orm import Session, selectinload
from app.models import Submission

class SubmissionRepository:
    def create(self, db: Session, problem_id: int, artifact_uri: str) -> Submission:
        submission = Submission(problem_id=problem_id, artifact_uri=artifact_uri)
        db.add(submission)
        db.flush()
        return submission

    def list_all(self, db: Session) -> list[Submission]:
        return list(
            db.query(Submission)
            .options(
                selectinload(Submission.runs),
                selectinload(Submission.queue_entries),
                selectinload(Submission.evaluations),
            )
            .order_by(Submission.created_at.desc())
            .all()
        )
```

## External Adapter Rules
- Keep external systems (storage, job runners, third-party APIs) in dedicated adapter files under `backend/app/adapters/`.
- Always accept configuration through constructor arguments — never read settings inside adapters.
- Always use concrete adapters first — only introduce protocols when multiple implementations exist.

### Correct external adapter
```python
# backend/app/adapters/storage.py
from google.cloud import storage

class StorageAdapter:
    def __init__(self, bucket_name: str) -> None:
        self._client = storage.Client()
        self._bucket = self._client.bucket(bucket_name)

    def upload(self, destination_path: str, data: bytes) -> str:
        blob = self._bucket.blob(destination_path)
        blob.upload_from_string(data)
        return f"gs://{self.bucket_name}/{destination_path}"
```

### Wrong — adapter reads settings
```python
class StorageAdapter:
    def __init__(self) -> None:
        settings = get_settings()                         # NEVER — accept bucket_name as arg
        self._bucket = storage.Client().bucket(settings.storage_bucket)
```

## Port and Adapter Naming Rules
- Ports are `Protocol` classes that define the interface the domain needs. They live in `backend/app/worker/contracts.py`.
- Each port defines exactly one responsibility. If the domain needs "run code" and "grade code", those are two separate protocols (`RunnerAdapter`, `GraderAdapter`), not one combined protocol.
- Adapter class names must end with the port name they implement: `Local` + `RunnerAdapter` = `LocalRunnerAdapter`, `Gcp` + `GraderAdapter` = `GcpGraderAdapter`.
- Never implement multiple ports in a single class. If two adapters share infrastructure logic (e.g., Docker container lifecycle), extract a private base class and have each adapter extend it.
- When multiple adapters share infrastructure code, use a private base class prefixed with underscore (e.g., `_LocalContainerAdapter`). The base class is an implementation detail — only the concrete adapter classes are part of the public API.

### Correct — one port, one adapter
```python
# backend/app/worker/contracts.py (ports)
class RunnerAdapter(Protocol):
    def execute(self, request: RunnerRequest) -> ExecutionOutcome: ...

class GraderAdapter(Protocol):
    def execute(self, request: GraderRequest) -> ExecutionOutcome: ...

# backend/app/adapters/local_runner.py (adapter)
class LocalRunnerAdapter(_LocalContainerAdapter):
    def execute(self, request: RunnerRequest) -> ExecutionOutcome: ...

# backend/app/adapters/local_grader.py (adapter)
class LocalGraderAdapter(_LocalContainerAdapter):
    def execute(self, request: GraderRequest) -> ExecutionOutcome: ...
```

### Wrong — one class implementing two ports
```python
class LocalTaskRunAdapter:                                    # NEVER — name doesn't match any port
    def execute(self, request: RunnerRequest | GraderRequest):  # NEVER — union type breaks protocol contract
        if "runner_output_uri" in request:                      # NEVER — runtime branching on role
            ...
```

### Wrong — adapter name doesn't end with the port name
```python
class GcpTaskRunner:       # NEVER — port is RunnerAdapter, so name must end with RunnerAdapter
class LocalExecutor:       # NEVER — which port does this implement?
```
