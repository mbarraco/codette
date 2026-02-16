"""
End-to-end integration tests for the full SEA worker pipeline.

Unlike test_sea.py which uses canned fake adapters, these tests exercise the
actual runner harness and grader evaluation logic in-process, verifying that
the full data flow (solution code -> harness -> runner output -> grader -> verdict)
works correctly for various submission scenarios.
"""

from sqlalchemy.orm import Session

from app.adapters.storage import StorageAdapter
from app.models import Run, Submission, SubmissionEvaluation, SubmissionQueue
from app.worker.sea import SeaWorker


def _run_pipeline(
    db: Session,
    sea_worker: SeaWorker,
    submission: Submission,
    queue_entry: SubmissionQueue,
) -> tuple[Run, SubmissionEvaluation, SubmissionQueue]:
    """Execute the pipeline and return (run, evaluation, queue_entry)."""
    claimed = sea_worker.process_next()
    assert claimed is not None
    assert claimed.id == queue_entry.id

    run = db.query(Run).filter_by(submission_id=submission.id).one()
    evaluation = db.query(SubmissionEvaluation).filter_by(run_id=run.id).one()
    updated_entry = db.query(SubmissionQueue).filter_by(id=queue_entry.id).one()
    return run, evaluation, updated_entry


def test_pipeline_correct_submission_passes(
    db: Session,
    storage: StorageAdapter,
    realistic_sea_worker: SeaWorker,
    make_submission,
) -> None:
    submission, queue_entry = make_submission("def add(a, b): return a + b")

    run, evaluation, entry = _run_pipeline(
        db, realistic_sea_worker, submission, queue_entry
    )

    assert run.status == "done"
    assert evaluation.success is True
    assert "3/3 tests passed" in evaluation.metadata_["summary"]
    assert entry.last_error is None


def test_pipeline_wrong_submission_fails(
    db: Session,
    storage: StorageAdapter,
    realistic_sea_worker: SeaWorker,
    make_submission,
) -> None:
    submission, queue_entry = make_submission("def add(a, b): return a * b")

    run, evaluation, entry = _run_pipeline(
        db, realistic_sea_worker, submission, queue_entry
    )

    assert run.status == "done"
    assert evaluation.success is False
    assert "fail" in entry.last_error.lower() or "passed" in entry.last_error.lower()


def test_pipeline_runtime_error_fails(
    db: Session,
    storage: StorageAdapter,
    realistic_sea_worker: SeaWorker,
    make_submission,
) -> None:
    submission, queue_entry = make_submission("def add(a, b): raise ValueError('boom')")

    run, evaluation, entry = _run_pipeline(
        db, realistic_sea_worker, submission, queue_entry
    )

    assert run.status == "done"
    assert evaluation.success is False
    assert entry.last_error is not None


def test_pipeline_wrong_function_name_fails(
    db: Session,
    storage: StorageAdapter,
    realistic_sea_worker: SeaWorker,
    make_submission,
) -> None:
    submission, queue_entry = make_submission("def sum(a, b): return a + b")

    run, evaluation, entry = _run_pipeline(
        db, realistic_sea_worker, submission, queue_entry
    )

    assert run.status == "done"
    assert evaluation.success is False
    assert entry.last_error is not None
