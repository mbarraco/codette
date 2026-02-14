import logging

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

    def execute(self, request: RunnerRequest | GraderRequest) -> ExecutionOutcome:
        run_uuid = request["run_uuid"]
        logger.info(
            "Launching local container %s for run %s", self._image_name, run_uuid
        )

        launch_error: Exception | None = None
        container = None
        for entrypoint, command in self._build_launch_specs(request):
            try:
                container = self._client.containers.run(
                    image=self._image_name,
                    entrypoint=entrypoint,
                    command=command,
                    environment={
                        "STORAGE_BUCKET": self._storage_bucket,
                        "STORAGE_EMULATOR_HOST": self._storage_emulator_host,
                    },
                    network=self._network,
                    detach=True,
                )
                launch_error = None
                break
            except Exception as exc:
                launch_error = exc
                continue

        if container is None:
            assert launch_error is not None
            return ExecutionOutcome(
                execution_ref=f"local:{self._image_name}",
                status=ExecutionStatus.FAILED,
                error=f"Container launch failed: {launch_error}",
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

    def _build_launch_specs(
        self, request: RunnerRequest | GraderRequest
    ) -> list[tuple[list[str] | None, list[str]]]:
        run_uuid = request["run_uuid"]
        # Prefer image default entrypoint (if present), then fall back to explicit
        # python script entrypoint for images that don't define one.
        if "runner_output_uri" in request:
            return [
                (None, [run_uuid]),
                (["python", "grade.py"], [run_uuid]),
            ]
        return [
            (None, [run_uuid]),
            (["python", "run.py"], [run_uuid]),
        ]
