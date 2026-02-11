"""Service-layer test for submission creation."""

from google.cloud import storage as gcs
from sqlalchemy.orm import Session

from app.adapters.repository.submission import SubmissionRepository
from app.adapters.storage import StorageAdapter
from app.models import Problem, Submission
from app.services.submission import create_submission


def test_create_submission(
    db: Session, storage: StorageAdapter, problem: Problem
) -> None:
    code = "def add(a, b):\n    return a + b\n"
    repo = SubmissionRepository()

    submission = create_submission(
        db=db,
        repo=repo,
        storage=storage,
        problem_id=problem.id,
        code=code,
    )

    # DB row was created
    assert isinstance(submission, Submission)
    assert submission.id is not None
    assert submission.problem_id == problem.id
    assert submission.artifact_uri.startswith("gs://")
    assert "solution.py" in submission.artifact_uri

    # Blob exists in fake-gcs
    client = gcs.Client()
    bucket = client.bucket("codette-test")
    # artifact_uri is gs://bucket/path — strip the prefix
    blob_path = submission.artifact_uri.split("/", 3)[3]
    blob = bucket.blob(blob_path)

    assert blob.exists()
    assert blob.download_as_text() == code
