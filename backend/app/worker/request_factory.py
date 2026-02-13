import json

from app.adapters.storage import StorageAdapter
from app.models import Run, Submission
from app.worker.contracts import GraderRequest, RunnerRequest


class ExecutionRequestFactory:
    def __init__(
        self,
        storage_bucket: str,
        storage: StorageAdapter | None = None,
        *,
        runner_timeout_s: int = 30,
        grader_timeout_s: int = 30,
    ) -> None:
        self.storage_bucket = storage_bucket
        self.storage = storage
        self.runner_timeout_s = runner_timeout_s
        self.grader_timeout_s = grader_timeout_s

    def build_runner_request(self, run: Run, submission: Submission) -> RunnerRequest:
        run_uuid = str(run.uuid)
        request = RunnerRequest(
            run_uuid=run_uuid,
            submission_id=submission.id,
            problem_id=submission.problem_id,
            submission_artifact_uri=submission.artifact_uri,
            output_uri=self._output_uri(
                run_uuid=run_uuid,
                file_name="runner_output.json",
            ),
            timeout_s=self.runner_timeout_s,
        )

        if self.storage is not None:
            self.storage.upload(
                f"runs/{run_uuid}/runner_request.json",
                json.dumps(request).encode(),
            )

        return request

    def build_grader_request(
        self,
        run: Run,
        submission: Submission,
        runner_output_uri: str,
    ) -> GraderRequest:
        run_uuid = str(run.uuid)
        request = GraderRequest(
            run_uuid=run_uuid,
            submission_id=submission.id,
            problem_id=submission.problem_id,
            runner_output_uri=runner_output_uri,
            output_uri=self._output_uri(
                run_uuid=run_uuid,
                file_name="grader_output.json",
            ),
            timeout_s=self.grader_timeout_s,
        )

        if self.storage is not None:
            self.storage.upload(
                f"runs/{run_uuid}/grader_request.json",
                json.dumps(request).encode(),
            )

        return request

    def _output_uri(self, run_uuid: str, file_name: str) -> str:
        return f"gs://{self.storage_bucket}/runs/{run_uuid}/{file_name}"
