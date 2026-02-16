import json
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
    test_cases: list[dict] | None = None,
    function_signature: str | None = None,
) -> Submission:
    """Upload code (and optional test cases) to storage and create a Submission row."""
    submission_uuid = uuid.uuid4()
    base_path = f"submissions/{submission_uuid}"
    artifact_uri = storage.upload(f"{base_path}/solution.py", code.encode())

    if test_cases is not None:
        runner_cases = [
            {"input": tc.get("input", []), "expected": tc.get("output")}
            for tc in test_cases
        ]
        payload = {
            "function_signature": function_signature,
            "test_cases": runner_cases,
        }
        storage.upload(
            f"{base_path}/test_cases.json",
            json.dumps(payload).encode(),
        )

    return repo.create(db, problem_id=problem_id, artifact_uri=artifact_uri)
