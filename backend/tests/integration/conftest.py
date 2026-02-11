from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.adapters.repository.submission import SubmissionRepository
from app.adapters.storage import StorageAdapter
from app.models import Submission, SubmissionQueue
from app.services.submission import create_submission


@pytest.fixture()
def submission(
    db: Session, problem, solution_file: Path, storage: StorageAdapter
) -> Submission:
    repo = SubmissionRepository()
    code = solution_file.read_text()

    return create_submission(
        db=db,
        repo=repo,
        storage=storage,
        problem_id=problem.id,
        code=code,
    )


@pytest.fixture()
def queue_entry(db: Session, submission: Submission) -> SubmissionQueue:
    entry = SubmissionQueue(submission_id=submission.id)
    db.add(entry)
    db.flush()
    return entry
