from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.adapters.repository.run import RunRepository
from app.adapters.repository.submission import SubmissionRepository
from app.adapters.repository.submission_evaluation import SubmissionEvaluationRepository
from app.adapters.repository.submission_queue import SubmissionQueueRepository
from app.adapters.storage import StorageAdapter
from app.models import Submission, SubmissionQueue
from app.services.submission import create_submission
from app.worker.sea import SeaWorker
from tests.app.adapters.task_run import FakeGraderAdapter, FakeRunnerAdapter


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


@pytest.fixture()
def sea_worker(db: Session, storage: StorageAdapter) -> SeaWorker:
    return SeaWorker(
        db=db,
        queue_repo=SubmissionQueueRepository(),
        run_repo=RunRepository(),
        eval_repo=SubmissionEvaluationRepository(),
        storage=storage,
        runner_adapter=FakeRunnerAdapter(storage),
        grader_adapter=FakeGraderAdapter(storage),
    )
