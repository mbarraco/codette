import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.adapters.repository.run import RunRepository
from app.adapters.repository.submission import SubmissionRepository
from app.adapters.repository.submission_evaluation import SubmissionEvaluationRepository
from app.adapters.repository.submission_queue import SubmissionQueueRepository
from app.adapters.storage import StorageAdapter
from app.models import Problem, Submission, SubmissionQueue
from app.services.submission import create_submission
from app.worker.request_factory import ExecutionRequestFactory
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
        request_factory=ExecutionRequestFactory(storage_bucket=storage.bucket_name),
    )


# ---------------------------------------------------------------------------
# Realistic pipeline fixtures
# ---------------------------------------------------------------------------

_JOBS_ROOT = str(Path(__file__).resolve().parent.parent.parent.parent / "jobs")


@pytest.fixture(autouse=False)
def _jobs_on_path():
    """Temporarily add the jobs/ directory to sys.path so runner/grader imports work."""
    if _JOBS_ROOT not in sys.path:
        sys.path.insert(0, _JOBS_ROOT)
    yield
    if _JOBS_ROOT in sys.path:
        sys.path.remove(_JOBS_ROOT)


_ADD_TEST_CASES = [
    {"input": [1, 2], "output": 3},
    {"input": [0, 0], "output": 0},
    {"input": [-1, 5], "output": 4},
]


@pytest.fixture()
def problem_with_test_cases(db: Session) -> Problem:
    p = Problem(
        title="Add Two Numbers",
        statement="Return the sum of two integers.",
        hints="Think about the + operator.",
        examples="add(1, 2) == 3",
        function_signature="def add(a, b):",
        test_cases=_ADD_TEST_CASES,
    )
    db.add(p)
    db.flush()
    return p


@pytest.fixture()
def make_submission(
    db: Session,
    storage: StorageAdapter,
    problem_with_test_cases: Problem,
    _jobs_on_path,
) -> Callable[[str], tuple[Submission, SubmissionQueue]]:
    """Factory fixture: creates a Submission + queue entry with the given code."""

    def _factory(code: str) -> tuple[Submission, SubmissionQueue]:
        repo = SubmissionRepository()
        sub = create_submission(
            db=db,
            repo=repo,
            storage=storage,
            problem_id=problem_with_test_cases.id,
            code=code,
            test_cases=_ADD_TEST_CASES,
            function_signature=problem_with_test_cases.function_signature,
        )
        entry = SubmissionQueue(submission_id=sub.id)
        db.add(entry)
        db.flush()
        return sub, entry

    return _factory


@pytest.fixture()
def realistic_sea_worker(
    db: Session, storage: StorageAdapter, _jobs_on_path
) -> SeaWorker:
    from tests.app.adapters.realistic_task_run import (
        RealisticGraderAdapter,
        RealisticRunnerAdapter,
    )

    return SeaWorker(
        db=db,
        queue_repo=SubmissionQueueRepository(),
        run_repo=RunRepository(),
        eval_repo=SubmissionEvaluationRepository(),
        storage=storage,
        runner_adapter=RealisticRunnerAdapter(storage),
        grader_adapter=RealisticGraderAdapter(storage),
        request_factory=ExecutionRequestFactory(storage_bucket=storage.bucket_name),
    )
