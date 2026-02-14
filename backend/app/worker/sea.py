import json

from sqlalchemy.orm import Session

from app.adapters.repository.run import RunRepository
from app.adapters.repository.submission_evaluation import SubmissionEvaluationRepository
from app.adapters.repository.submission_queue import SubmissionQueueRepository
from app.adapters.storage import StorageAdapter
from app.models import Run, SubmissionQueue
from app.worker.contracts import (
    ExecutionStatus,
    GraderAdapter,
    GraderOutput,
    GraderRequest,
    GraderVerdict,
    RunnerAdapter,
    RunnerRequest,
)
from app.worker.request_factory import ExecutionRequestFactory


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
        request_factory: ExecutionRequestFactory | None = None,
    ) -> None:
        self.db = db
        self.queue_repo = queue_repo
        self.run_repo = run_repo
        self.eval_repo = eval_repo
        self.storage = storage
        self.runner_adapter = runner_adapter
        self.grader_adapter = grader_adapter
        self.request_factory = request_factory or ExecutionRequestFactory(
            storage_bucket=storage.bucket_name
        )

    def process_next(self) -> SubmissionQueue | None:
        """Claim the next queue entry and run the full evaluation pipeline."""
        entry = self.queue_repo.claim_next(self.db)
        if entry is None:
            return None

        submission = entry.submission
        run = self.run_repo.create(self.db, submission_id=submission.id)

        runner_request = self.request_factory.build_runner_request(
            run=run,
            submission=submission,
        )
        grader_request = self.request_factory.build_grader_request(
            run=run,
            submission=submission,
            runner_output_uri=runner_request["output_uri"],
        )
        try:
            if not self._execute_runner(
                entry=entry,
                run=run,
                runner_request=runner_request,
            ):
                return entry

            if not self._execute_grader(
                entry=entry,
                run=run,
                grader_request=grader_request,
            ):
                return entry

            self._evaluate_run(
                run=run,
                submission_id=submission.id,
                grader_output_uri=grader_request["output_uri"],
            )
        except Exception as exc:
            self._mark_run_failed(
                entry=entry,
                run=run,
                stage="worker",
                error=str(exc),
            )
            raise

        return entry

    def _execute_runner(
        self,
        entry: SubmissionQueue,
        run: Run,
        runner_request: RunnerRequest,
    ) -> bool:
        runner_outcome = self.runner_adapter.execute(runner_request)
        if runner_outcome["status"] != ExecutionStatus.SUCCEEDED:
            self._mark_run_failed(
                entry=entry,
                run=run,
                stage="runner",
                error=runner_outcome["error"],
                execution_ref=runner_outcome["execution_ref"],
            )
            return False

        self.run_repo.update(
            self.db,
            run,
            status="runner_done",
            execution_ref=runner_outcome["execution_ref"],
            runner_output_uri=runner_request["output_uri"],
        )
        return True

    def _execute_grader(
        self,
        entry: SubmissionQueue,
        run: Run,
        grader_request: GraderRequest,
    ) -> bool:
        grader_outcome = self.grader_adapter.execute(grader_request)
        if grader_outcome["status"] != ExecutionStatus.SUCCEEDED:
            self._mark_run_failed(
                entry=entry,
                run=run,
                stage="grader",
                error=grader_outcome["error"],
            )
            return False

        self.run_repo.update(
            self.db,
            run,
            grader_output_uri=grader_request["output_uri"],
        )
        return True

    def _evaluate_run(
        self, run: Run, submission_id: int, grader_output_uri: str
    ) -> None:
        grader_blob = self.storage.download(grader_output_uri)
        grader_output: GraderOutput = json.loads(grader_blob)
        success = grader_output["verdict"] == GraderVerdict.PASS

        self.eval_repo.create(
            self.db,
            run_id=run.id,
            submission_id=submission_id,
            success=success,
            metadata={"summary": grader_output["summary"]},
        )
        self.run_repo.update(self.db, run, status="done")

    def _mark_run_failed(
        self,
        entry: SubmissionQueue,
        run: Run,
        stage: str,
        error: str | None,
        execution_ref: str | None = None,
    ) -> None:
        error_text = error or "Execution failed"
        self.run_repo.update(
            self.db,
            run,
            status="failed",
            execution_ref=execution_ref,
            failure_stage=stage,
            failure_error=error_text,
        )
        self.queue_repo.mark_failed(self.db, entry, error=error_text)
