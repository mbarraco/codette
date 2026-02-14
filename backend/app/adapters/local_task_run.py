import logging

import docker

from app.worker.contracts import (
    ExecutionOutcome,
    ExecutionStatus,
    GraderRequest,
    RunnerRequest,
)

logger = logging.getLogger(__name__)

_CONTAINER_TIMEOUT_S = 120


class LocalTaskRunAdapter:
    """Launches runner/grader as local Docker containers.

    Mirrors production where ``GcpTaskRunAdapter`` launches Cloud Run Jobs,
    but uses the Docker SDK to run sibling containers on the host.
    """

    def __init__(
        self,
        image_name: str,
        network: str,
        storage_bucket: str,
        storage_emulator_host: str,
    ) -> None:
        self._image_name = image_name
        self._network = network
        self._storage_bucket = storage_bucket
        self._storage_emulator_host = storage_emulator_host
        self._client = docker.from_env()

    def execute(self, request: RunnerRequest | GraderRequest) -> ExecutionOutcome:
        run_uuid = request["run_uuid"]
        logger.info(
            "Launching local container %s for run %s", self._image_name, run_uuid
        )

        container = self._client.containers.run(
            image=self._image_name,
            command=[run_uuid],
            environment={
                "STORAGE_BUCKET": self._storage_bucket,
                "STORAGE_EMULATOR_HOST": self._storage_emulator_host,
            },
            network=self._network,
            detach=True,
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
