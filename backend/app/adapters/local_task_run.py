"""Local Docker-based adapters for runner and grader execution.

Mirrors production where ``GcpRunnerAdapter`` / ``GcpGraderAdapter`` launch
Cloud Run Jobs, but uses the Docker SDK to run sibling containers on the host.
"""

import logging

from app.worker.contracts import (
    ExecutionOutcome,
    ExecutionStatus,
    GraderRequest,
    RunnerRequest,
)

logger = logging.getLogger(__name__)

_CONTAINER_TIMEOUT_S = 120


class _LocalContainerAdapter:
    """Shared Docker container lifecycle logic.

    Not part of the public API — use ``LocalRunnerAdapter`` or
    ``LocalGraderAdapter`` instead.
    """

    container_label = "task"

    def __init__(
        self,
        image_name: str,
        network: str,
        storage_bucket: str,
        storage_emulator_host: str,
        docker_client: object | None = None,
    ) -> None:
        self._image_name = image_name
        self._network = network
        self._storage_bucket = storage_bucket
        self._storage_emulator_host = storage_emulator_host
        if docker_client is not None:
            self._client = docker_client
        else:
            import docker

            self._client = docker.from_env()

    def _run_container(self, run_uuid: str, entrypoint: list[str]) -> ExecutionOutcome:
        logger.info(
            "Launching local container %s for run %s", self._image_name, run_uuid
        )

        try:
            container = self._client.containers.run(
                image=self._image_name,
                name=f"codette-{self.container_label}-{run_uuid}",
                entrypoint=entrypoint,
                command=[run_uuid],
                environment={
                    "STORAGE_BUCKET": self._storage_bucket,
                    "STORAGE_EMULATOR_HOST": self._storage_emulator_host,
                },
                network=self._network,
                detach=True,
            )
        except Exception as exc:
            return ExecutionOutcome(
                execution_ref=f"local:{self._image_name}",
                status=ExecutionStatus.FAILED,
                error=f"Container launch failed: {exc}",
            )

        try:
            result = container.wait(timeout=_CONTAINER_TIMEOUT_S)
            exit_code = result.get("StatusCode", -1)
            succeeded = exit_code == 0

            error_msg = None
            if not succeeded:
                logs = container.logs(tail=50).decode(errors="replace")
                error_msg = f"Container exited with code {exit_code}: {logs}"

            status = ExecutionStatus.SUCCEEDED if succeeded else ExecutionStatus.FAILED
            logger.info(
                "Container %s finished with status=%s (exit_code=%d)",
                container.short_id,
                status,
                exit_code,
            )

            return ExecutionOutcome(
                execution_ref=f"local:{container.short_id}",
                status=status,
                error=error_msg,
            )
        finally:
            container.remove(force=True)


class LocalRunnerAdapter(_LocalContainerAdapter):
    """Launches the runner image as a local Docker container.

    Implements the ``RunnerAdapter`` protocol.
    """

    container_label = "runner"

    def execute(self, request: RunnerRequest) -> ExecutionOutcome:
        return self._run_container(request["run_uuid"], ["python", "-m", "runner.run"])


class LocalGraderAdapter(_LocalContainerAdapter):
    """Launches the grader image as a local Docker container.

    Implements the ``GraderAdapter`` protocol.
    """

    container_label = "grader"

    def execute(self, request: GraderRequest) -> ExecutionOutcome:
        return self._run_container(request["run_uuid"], ["python", "-m", "grader.run"])
