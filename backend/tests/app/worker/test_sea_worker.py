from dataclasses import dataclass

import pytest
from sqlalchemy.orm import Session

from app.adapters.repository.run import RunRepository
from app.adapters.repository.submission_evaluation import SubmissionEvaluationRepository
from app.adapters.repository.submission_queue import SubmissionQueueRepository
from app.models import Run, Submission, SubmissionQueue
from app.worker.contracts import ExecutionOutcome, ExecutionStatus
from app.worker.request_factory import ExecutionRequestFactory
from app.worker.sea import SeaWorker


@dataclass
class StubStorage:
    bucket_name: str = "codette-test"

    def download(self, _uri: str) -> bytes:
        raise RuntimeError("unexpected download")


class FailingDownloadStorage(StubStorage):
    def download(self, _uri: str) -> bytes:
        raise RuntimeError("grader output missing")


class FailingRunnerAdapter:
    def execute(self, _request) -> ExecutionOutcome:
        return ExecutionOutcome(
            execution_ref="local:runner-failed",
            status=ExecutionStatus.FAILED,
            error="Runner container failed",
        )


class SucceedingRunnerAdapter:
    def execute(self, _request) -> ExecutionOutcome:
        return ExecutionOutcome(
            execution_ref="local:runner-ok",
            status=ExecutionStatus.SUCCEEDED,
            error=None,
        )


class FailingGraderAdapter:
    def execute(self, _request) -> ExecutionOutcome:
        return ExecutionOutcome(
            execution_ref="local:grader-failed",
            status=ExecutionStatus.FAILED,
            error="Grader container failed",
        )


class SucceedingGraderAdapter:
    def execute(self, _request) -> ExecutionOutcome:
        return ExecutionOutcome(
            execution_ref="local:grader-ok",
            status=ExecutionStatus.SUCCEEDED,
            error=None,
        )


class UnexpectedGraderCallAdapter:
    def execute(self, _request) -> ExecutionOutcome:
        raise AssertionError("grader should not run when runner fails")


def _enqueue_submission(db: Session, submission: Submission) -> SubmissionQueue:
    entry = SubmissionQueue(submission_id=submission.id)
    db.add(entry)
    db.flush()
    return entry


def _build_worker(
    db: Session,
    storage: StubStorage,
    runner_adapter,
    grader_adapter,
) -> SeaWorker:
    return SeaWorker(
        db=db,
        queue_repo=SubmissionQueueRepository(),
        run_repo=RunRepository(),
        eval_repo=SubmissionEvaluationRepository(),
        storage=storage,
        runner_adapter=runner_adapter,
        grader_adapter=grader_adapter,
        request_factory=ExecutionRequestFactory(storage_bucket=storage.bucket_name),
    )


def test_process_next_marks_run_and_queue_when_runner_fails(
    db: Session, submission: Submission
) -> None:
    entry = _enqueue_submission(db, submission)
    worker = _build_worker(
        db=db,
        storage=StubStorage(),
        runner_adapter=FailingRunnerAdapter(),
        grader_adapter=UnexpectedGraderCallAdapter(),
    )

    claimed = worker.process_next()

    assert claimed is not None
    run = db.query(Run).filter_by(submission_id=submission.id).one()
    failed_entry = db.query(SubmissionQueue).filter_by(id=entry.id).one()
    assert run.status == "failed"
    assert run.execution_ref == "local:runner-failed"
    assert run.failure_stage == "runner"
    assert run.failure_error == "Runner container failed"
    assert failed_entry.last_error == "Runner container failed"
    assert failed_entry.attempt_count == 1


def test_process_next_marks_run_and_queue_when_grader_fails(
    db: Session, submission: Submission
) -> None:
    entry = _enqueue_submission(db, submission)
    worker = _build_worker(
        db=db,
        storage=StubStorage(),
        runner_adapter=SucceedingRunnerAdapter(),
        grader_adapter=FailingGraderAdapter(),
    )

    claimed = worker.process_next()

    assert claimed is not None
    run = db.query(Run).filter_by(submission_id=submission.id).one()
    failed_entry = db.query(SubmissionQueue).filter_by(id=entry.id).one()
    assert run.status == "failed"
    assert run.execution_ref == "local:runner-ok"
    assert run.failure_stage == "grader"
    assert run.failure_error == "Grader container failed"
    assert failed_entry.last_error == "Grader container failed"
    assert failed_entry.attempt_count == 1


def test_process_next_marks_worker_failure_when_evaluation_raises(
    db: Session, submission: Submission
) -> None:
    entry = _enqueue_submission(db, submission)
    worker = _build_worker(
        db=db,
        storage=FailingDownloadStorage(),
        runner_adapter=SucceedingRunnerAdapter(),
        grader_adapter=SucceedingGraderAdapter(),
    )

    with pytest.raises(RuntimeError, match="grader output missing"):
        worker.process_next()

    run = db.query(Run).filter_by(submission_id=submission.id).one()
    failed_entry = db.query(SubmissionQueue).filter_by(id=entry.id).one()
    assert run.status == "failed"
    assert run.execution_ref == "local:runner-ok"
    assert run.failure_stage == "worker"
    assert run.failure_error == "grader output missing"
    assert failed_entry.last_error == "grader output missing"
    assert failed_entry.attempt_count == 1
