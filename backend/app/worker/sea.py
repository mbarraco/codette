import json

from sqlalchemy.orm import Session

from app.adapters.repository.run import RunRepository
from app.adapters.repository.submission_evaluation import SubmissionEvaluationRepository
from app.adapters.repository.submission_queue import SubmissionQueueRepository
from app.adapters.storage import StorageAdapter
from app.models import SubmissionQueue
from app.worker.contracts import (
    ExecutionStatus,
    GraderAdapter,
    GraderOutput,
    GraderRequest,
    GraderVerdict,
    RunnerAdapter,
    RunnerRequest,
)


class SeaWorker:
    def __init__(
        self,
        db: Session,
        queue_repo: SubmissionQueueRepository,
        run_repo: RunRepository,
        eval_repo: SubmissionEvaluationRepository,
        storage: StorageAdapter,
        runner_adapter: RunnerAdapter,
        grader_adapter: GraderAdapter,
    ) -> None:
        self.db = db
        self.queue_repo = queue_repo
        self.run_repo = run_repo
        self.eval_repo = eval_repo
        self.storage = storage
        self.runner_adapter = runner_adapter
        self.grader_adapter = grader_adapter

    def process_next(self) -> SubmissionQueue | None:
        """Claim the next queue entry and run the full evaluation pipeline."""
        entry = self.queue_repo.claim_next(self.db)
        if entry is None:
            return None

        # Load the submission to get artifact info
        submission = entry.submission
        run = self.run_repo.create(self.db, submission_id=submission.id)

        try:
            # -- Runner --
            bucket = self.storage._bucket.name
            runner_output_path = f"runs/{run.id}/runner_output.json"
            runner_request = RunnerRequest(
                run_id=run.id,
                submission_id=submission.id,
                problem_id=submission.problem_id,
                submission_artifact_uri=submission.artifact_uri,
                output_uri=f"gs://{bucket}/{runner_output_path}",
                timeout_s=30,
            )
            runner_outcome = self.runner_adapter.execute(runner_request)
            if runner_outcome["status"] != ExecutionStatus.SUCCEEDED:
                self.run_repo.update(self.db, run, status="failed")
                return entry

            self.run_repo.update(
                self.db,
                run,
                status="runner_done",
                execution_ref=runner_outcome["execution_ref"],
                runner_output_uri=runner_request["output_uri"],
            )

            # -- Grader --
            grader_output_path = f"runs/{run.id}/grader_output.json"
            grader_request = GraderRequest(
                run_id=run.id,
                submission_id=submission.id,
                problem_id=submission.problem_id,
                runner_output_uri=runner_request["output_uri"],
                output_uri=f"gs://{bucket}/{grader_output_path}",
                timeout_s=30,
            )
            grader_outcome = self.grader_adapter.execute(grader_request)
            if grader_outcome["status"] != ExecutionStatus.SUCCEEDED:
                self.run_repo.update(self.db, run, status="failed")
                return entry

            self.run_repo.update(
                self.db,
                run,
                grader_output_uri=grader_request["output_uri"],
            )

            # -- Evaluation --
            grader_blob = self.storage.download(grader_request["output_uri"])
            grader_output: GraderOutput = json.loads(grader_blob)
            success = grader_output["verdict"] == GraderVerdict.PASS

            self.eval_repo.create(
                self.db,
                run_id=run.id,
                submission_id=submission.id,
                success=success,
                metadata={"summary": grader_output["summary"]},
            )
            self.run_repo.update(self.db, run, status="done")

        except Exception:
            self.run_repo.update(self.db, run, status="failed")
            raise

        return entry
