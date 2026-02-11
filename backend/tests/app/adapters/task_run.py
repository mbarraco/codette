import json
import uuid

from app.adapters.storage import StorageAdapter
from app.worker.contracts import (
    ExecutionOutcome,
    ExecutionStatus,
    GraderOutput,
    GraderRequest,
    GraderVerdict,
    RunnerOutput,
    RunnerRequest,
    RunnerResultStatus,
)


class FakeRunnerAdapter:
    def __init__(self, storage: StorageAdapter) -> None:
        self._storage = storage

    def execute(self, request: RunnerRequest) -> ExecutionOutcome:
        output: RunnerOutput = {
            "schema_version": "runner_output.v1",
            "run_id": request["run_id"],
            "status": RunnerResultStatus.OK,
            "stdout": "3\n",
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 42,
        }
        self._storage.upload(
            request["output_uri"].split("/", 3)[-1],
            json.dumps(output).encode(),
        )
        return ExecutionOutcome(
            execution_ref=f"fake-runner-{uuid.uuid4()}",
            status=ExecutionStatus.SUCCEEDED,
            error=None,
        )


class FakeGraderAdapter:
    def __init__(self, storage: StorageAdapter) -> None:
        self._storage = storage

    def execute(self, request: GraderRequest) -> ExecutionOutcome:
        output: GraderOutput = {
            "schema_version": "grader_output.v1",
            "run_id": request["run_id"],
            "verdict": GraderVerdict.PASS,
            "summary": "All tests passed",
            "metadata": None,
        }
        self._storage.upload(
            request["output_uri"].split("/", 3)[-1],
            json.dumps(output).encode(),
        )
        return ExecutionOutcome(
            execution_ref=f"fake-grader-{uuid.uuid4()}",
            status=ExecutionStatus.SUCCEEDED,
            error=None,
        )
