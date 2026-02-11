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
