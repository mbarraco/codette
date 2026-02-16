"""Realistic fake adapters that execute actual harness/grader logic in-process.

Unlike ``FakeRunnerAdapter`` / ``FakeGraderAdapter`` which return canned output,
these adapters run the real runner harness and grader evaluation code so that the
full data flow (solution code -> harness -> runner output -> grader -> verdict)
is exercised end-to-end without Docker or subprocesses.
"""

import json
import tempfile
import uuid
from pathlib import Path

from app.adapters.storage import StorageAdapter
from app.worker.contracts import (
    ExecutionOutcome,
    ExecutionStatus,
    GraderRequest,
    RunnerOutput,
    RunnerRequest,
    RunnerResultStatus,
)


class RealisticRunnerAdapter:
    """Runs the actual harness logic in-process, reading/writing real GCS files.

    Implements the ``RunnerAdapter`` protocol.
    """

    def __init__(self, storage: StorageAdapter) -> None:
        self._storage = storage

    def execute(self, request: RunnerRequest) -> ExecutionOutcome:
        from runner.harness import execute as harness_execute
        from runner.schemas import HarnessInput, TestCasesConfig

        artifact_uri = request["submission_artifact_uri"]
        prefix = f"gs://{self._storage.bucket_name}/"
        artifact_path = artifact_uri[len(prefix) :]
        submission_dir = artifact_path.rsplit("/", 1)[0]

        solution_bytes = self._storage.download(artifact_uri)
        test_cases_uri = f"{prefix}{submission_dir}/test_cases.json"
        test_cases_bytes = self._storage.download(test_cases_uri)

        work_dir = Path(tempfile.mkdtemp(prefix="realistic_runner_"))
        (work_dir / "solution.py").write_bytes(solution_bytes)

        config = TestCasesConfig.model_validate_json(test_cases_bytes)
        harness_input = HarnessInput(
            solution_path=str(work_dir / "solution.py"),
            test_cases=config.test_cases,
            function_signature=config.function_signature,
        )

        harness_output = harness_execute(harness_input)

        runner_output: RunnerOutput = {
            "schema_version": "runner_output.v1",
            "run_uuid": request["run_uuid"],
            "status": RunnerResultStatus.OK,
            "stdout": harness_output.model_dump_json(),
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 1,
        }

        output_path = request["output_uri"][len(prefix) :]
        self._storage.upload(output_path, json.dumps(runner_output).encode())

        return ExecutionOutcome(
            execution_ref=f"realistic-runner-{uuid.uuid4()}",
            status=ExecutionStatus.SUCCEEDED,
            error=None,
        )


class RealisticGraderAdapter:
    """Runs the actual grader evaluation logic in-process.

    Implements the ``GraderAdapter`` protocol.
    """

    def __init__(self, storage: StorageAdapter) -> None:
        self._storage = storage

    def execute(self, request: GraderRequest) -> ExecutionOutcome:
        from grader.run import _evaluate
        from grader.schemas import GraderOutput
        from grader.schemas import RunnerOutput as GraderRunnerOutput

        runner_output_bytes = self._storage.download(request["runner_output_uri"])
        runner_output = GraderRunnerOutput.model_validate_json(runner_output_bytes)

        verdict, summary = _evaluate(runner_output)

        grader_output = GraderOutput(
            run_uuid=request["run_uuid"],
            verdict=verdict,
            summary=summary,
        )

        prefix = f"gs://{self._storage.bucket_name}/"
        output_path = request["output_uri"][len(prefix) :]
        self._storage.upload(output_path, grader_output.model_dump_json().encode())

        return ExecutionOutcome(
            execution_ref=f"realistic-grader-{uuid.uuid4()}",
            status=ExecutionStatus.SUCCEEDED,
            error=None,
        )
