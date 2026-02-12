from enum import StrEnum
from typing import Literal, Protocol, TypedDict


class ExecutionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class RunnerResultStatus(StrEnum):
    OK = "ok"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    SYSTEM_ERROR = "system_error"


class GraderVerdict(StrEnum):
    PASS = "pass"
    FAIL = "fail"


class ExecutionOutcome(TypedDict):
    execution_ref: str
    status: ExecutionStatus
    error: str | None


class RunnerRequest(TypedDict):
    run_uuid: str
    submission_id: int
    problem_id: int
    submission_artifact_uri: str
    output_uri: str
    timeout_s: int


class RunnerOutput(TypedDict):
    schema_version: Literal["runner_output.v1"]
    run_uuid: str
    status: RunnerResultStatus
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int


class GraderRequest(TypedDict):
    run_uuid: str
    submission_id: int
    problem_id: int
    runner_output_uri: str
    output_uri: str
    timeout_s: int


class GraderOutput(TypedDict):
    schema_version: Literal["grader_output.v1"]
    run_uuid: str
    verdict: GraderVerdict
    summary: str
    metadata: dict[str, object] | None


class RunnerAdapter(Protocol):
    def execute(self, request: RunnerRequest) -> ExecutionOutcome: ...


class GraderAdapter(Protocol):
    def execute(self, request: GraderRequest) -> ExecutionOutcome: ...
