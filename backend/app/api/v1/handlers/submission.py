import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.repository.problem import ProblemRepository
from app.adapters.repository.submission import SubmissionRepository
from app.adapters.repository.submission_queue import SubmissionQueueRepository
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
    submission = create_submission(
        db,
        repo,
        storage,
        problem.id,
        code,
        test_cases=problem.test_cases,
        function_signature=problem.function_signature,
    )
    queue_repo = SubmissionQueueRepository()
    queue_repo.create(db, submission_id=submission.id)
    db.commit()
    submission.problem = problem
    return submission


def handle_list_submissions(db: Session) -> list[Submission]:
    repo = SubmissionRepository()
    return repo.list_all(db)


def handle_get_submission(db: Session, submission_uuid: uuid.UUID) -> Submission:
    repo = SubmissionRepository()
    submission = repo.get_by_uuid(db, submission_uuid)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_uuid} not found",
        )
    return submission


def handle_delete_submission(db: Session, submission_uuid: uuid.UUID) -> None:
    repo = SubmissionRepository()
    submission = repo.get_by_uuid(db, submission_uuid)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_uuid} not found",
        )
    repo.soft_delete(db, submission)
    db.commit()
