"""
SEA happy-path integration test.

Tests the full worker flow against a real Postgres instance:
  Problem in DB -> enqueue submission -> worker claims ->
  runner produces output -> grader produces verdict ->
  evaluation written to DB.
"""

from sqlalchemy.orm import Session

from app.adapters.storage import StorageAdapter
from app.models import (
    Run,
    Submission,
    SubmissionEvaluation,
    SubmissionQueue,
)
from app.worker.sea import SeaWorker


def test_sea_happy_path(
    db: Session,
    storage: StorageAdapter,
    sea_worker: SeaWorker,
    submission: Submission,
    queue_entry: SubmissionQueue,
) -> None:
    assert queue_entry.id is not None
    assert queue_entry.attempt_count == 0

    # -- Act: process the queue entry (full pipeline) ----------------------
    claimed = sea_worker.process_next()
    assert claimed is not None
    assert claimed.id == queue_entry.id
    assert claimed.last_checked_at is not None
    assert claimed.attempt_count == 1

    # -- No more entries to claim ------------------------------------------
    second = sea_worker.process_next()
    assert second is None

    # -- Assert: Run record created with final status ----------------------
    run = db.query(Run).filter_by(submission_id=submission.id).one()
    assert run.status == "done"
    assert run.execution_ref is not None

    # -- Assert: runner output exists in storage ---------------------------
    assert run.runner_output_uri is not None
    runner_blob = storage.download(run.runner_output_uri)
    assert b"runner_output.v1" in runner_blob

    # -- Assert: grader output exists in storage ---------------------------
    assert run.grader_output_uri is not None
    grader_blob = storage.download(run.grader_output_uri)
    assert b"grader_output.v1" in grader_blob

    # -- Assert: evaluation row exists with success=True -------------------
    evaluation = db.query(SubmissionEvaluation).filter_by(run_id=run.id).one()
    assert evaluation.success is True
    assert evaluation.submission_id == submission.id
