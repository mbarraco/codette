"""GCP Cloud Run Jobs adapters for runner and grader execution."""

import logging

from google.cloud import run_v2

from app.worker.contracts import (
    ExecutionOutcome,
    ExecutionStatus,
    GraderRequest,
    RunnerRequest,
)

logger = logging.getLogger(__name__)


class _GcpJobAdapter:
    """Shared Cloud Run Job execution logic.

    Not part of the public API — use ``GcpRunnerAdapter`` or
    ``GcpGraderAdapter`` instead.
    """

    def __init__(self, project: str, location: str, job_name: str) -> None:
        self._client = run_v2.ExecutionsClient()
        self._job_path = run_v2.JobsClient.job_path(project, location, job_name)

    def _run_job(self, run_uuid: str) -> ExecutionOutcome:
        logger.info("Launching job %s for run %s", self._job_path, run_uuid)

        run_job_request = run_v2.RunJobRequest(
            name=self._job_path,
            overrides=run_v2.RunJobRequest.Overrides(
                container_overrides=[
                    run_v2.RunJobRequest.Overrides.ContainerOverride(
                        args=[run_uuid],
                    ),
                ],
            ),
        )

        operation = self._client.run_job(request=run_job_request)
        execution = operation.result()

        succeeded = self._is_succeeded(execution)
        error_msg = None if succeeded else self._extract_error(execution)

        status = ExecutionStatus.SUCCEEDED if succeeded else ExecutionStatus.FAILED
        logger.info("Job execution %s finished with status=%s", execution.name, status)

        return ExecutionOutcome(
            execution_ref=execution.name,
            status=status,
            error=error_msg,
        )

    def _is_succeeded(self, execution: run_v2.Execution) -> bool:
        for condition in execution.conditions:
            if (
                condition.type_ == "Completed"
                and condition.state == run_v2.Condition.State.CONDITION_SUCCEEDED
            ):
                return True
        return False

    def _extract_error(self, execution: run_v2.Execution) -> str:
        messages = []
        for condition in execution.conditions:
            if condition.state == run_v2.Condition.State.CONDITION_FAILED:
                messages.append(f"{condition.type_}: {condition.message}")
        return "; ".join(messages) if messages else "Execution failed (unknown reason)"


class GcpRunnerAdapter(_GcpJobAdapter):
    """Launches a Cloud Run Job to execute runner tasks.

    Implements the ``RunnerAdapter`` protocol.
    """

    def execute(self, request: RunnerRequest) -> ExecutionOutcome:
        return self._run_job(request["run_uuid"])


class GcpGraderAdapter(_GcpJobAdapter):
    """Launches a Cloud Run Job to execute grader tasks.

    Implements the ``GraderAdapter`` protocol.
    """

    def execute(self, request: GraderRequest) -> ExecutionOutcome:
        return self._run_job(request["run_uuid"])
