"""
SEA happy-path integration test (scaffolded).

Tests the full worker flow against a real Postgres instance:
  Problem in DB → enqueue submission → worker claims →
  runner produces output → grader produces verdict →
  evaluation written to DB.

Steps after "claim" are scaffolded — they will fail until
the corresponding adapters are implemented.
"""

from sqlalchemy.orm import Session

from app.adapters.repository.submission_queue import SubmissionQueueRepository
from app.models import (
    Submission,
    SubmissionQueue,
)
from app.worker.sea import SeaWorker

# ---------------------------------------------------------------------------
# Happy-path test
# ---------------------------------------------------------------------------


def test_sea_happy_path(
    db: Session, submission: Submission, queue_entry: SubmissionQueue
) -> None:
    assert queue_entry.id is not None
    assert queue_entry.attempt_count == 0

    # -- Build the worker with its adapters ------------------------------
    queue_repo = SubmissionQueueRepository()
    worker = SeaWorker(db=db, queue_repo=queue_repo)

    # -- Act 1: Worker claims the queue entry ----------------------------
    claimed = worker.process_next()
    assert claimed is not None
    assert claimed.id == queue_entry.id
    assert claimed.last_checked_at is not None
    assert claimed.attempt_count == 1

    # -- Act 1b: No more entries to claim --------------------------------
    second = worker.process_next()
    assert second is None

    # -- Act 2: Worker creates a run record ------------------------------
    #    (will fail until RunRepository adapter is implemented)
    # from app.adapters.repository.run import RunRepository
    # run_repo = RunRepository()
    # run: Run = run_repo.create(db, submission)
    # assert run.status == "queued"
    # assert run.submission_id == submission.id

    # -- Act 3: Worker writes submission_input.json to object storage ----
    #    (will fail until the worker is wired to write submission_input.json)
    # submission_input_uri = storage.upload(...)
    # assert submission_input_uri.endswith("submission_input.json")

    # -- Act 4: Worker invokes the Runner --------------------------------
    #    (will fail until RunnerAdapter is implemented)
    # from app.adapters.runner import RunnerAdapter
    # runner = RunnerAdapter()
    # runner_output_uri = runner.invoke(run, submission_input_uri)
    # run.status = "runner_done"
    # run.runner_output_uri = runner_output_uri
    # db.flush()

    # -- Act 5: Worker invokes the Grader --------------------------------
    #    (will fail until GraderAdapter is implemented)
    # from app.adapters.grader import GraderAdapter
    # grader = GraderAdapter()
    # grader_output_uri = grader.invoke(run, runner_output_uri)
    # run.grader_output_uri = grader_output_uri
    # db.flush()

    # -- Act 6: Worker reads grader verdict and writes evaluation --------
    # verdict = storage.read_grader_output(grader_output_uri)
    # assert "success" in verdict
    #
    # evaluation = SubmissionEvaluation(
    #     run_id=run.id,
    #     submission_id=submission.id,
    #     success=verdict["success"],
    #     metadata_=verdict.get("metadata"),
    # )
    # db.add(evaluation)
    # run.status = "done" if verdict["success"] else "failed"
    # db.flush()

    # -- Assert: final state (uncomment when full flow is wired) ---------
    # assert evaluation.id is not None
    # assert evaluation.success is True
    # saved_run = db.get(Run, run.id)
    # assert saved_run.status == "done"
    # saved_eval = db.get(SubmissionEvaluation, evaluation.id)
    # assert saved_eval.run_id == run.id
