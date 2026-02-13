# Backend Architecture Rules

## Layer Layout
- The backend lives under `backend/app/` with these top-level packages: `api/`, `services/`, `adapters/`, `worker/`, `models/`, `core/`.
- Every import must follow this dependency direction — never import against the arrow:

```
api/routes -> api/handlers -> services -> adapters -> models
                                                  \-> core
```

## Dependency Direction
- Route modules must never import from `services/`, `adapters/`, or `models/` (except schema types).
- Handler modules must never import from `api/routes/`.
- Service modules must never import from `api/` or `worker/`.
- Adapter modules must never import from `services/` or `api/`.

### Correct — handler imports service and adapter
```python
# backend/app/api/v1/handlers/submission.py
from app.adapters.repository.submission import SubmissionRepository
from app.adapters.storage import StorageAdapter
from app.services.submission import create_submission
```

### Wrong — route imports repository directly
```python
# backend/app/api/v1/routes/submission.py
from app.adapters.repository.submission import SubmissionRepository  # NEVER
```

### Wrong — service imports FastAPI types
```python
# backend/app/services/submission.py
from fastapi import HTTPException  # NEVER
```

## Worker Rules
- Keep worker orchestration in `backend/app/worker/`.
- Always inject dependencies through constructors — never import adapters at module level in workers.
