"""Pydantic schemas for runner request/input/output payloads."""

from typing import Any, Literal

from errors import JobError
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RunnerRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    submission_artifact_uri: str
    output_uri: str
    timeout_s: int = Field(gt=0)


class TestCase(BaseModel):
    model_config = ConfigDict(extra="ignore")

    input: list[Any] = Field(default_factory=list)
    expected: Any = None


class TestCasesConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    function_signature: str | None = None
    test_cases: list[TestCase] = Field(default_factory=list)


class HarnessInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    solution_path: str
    test_cases: list[TestCase]
    function_signature: str | None = None


class HarnessTestCaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input: list[Any]
    expected: Any
    actual: Any
    stdout: str
    error: str | None
    passed: bool


class HarnessOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: list[HarnessTestCaseResult] = Field(default_factory=list)
    error: str | None = None


class HarnessExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "runtime_error", "timeout"]
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int = Field(ge=0)


class RunnerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["runner_output.v1"] = "runner_output.v1"
    run_uuid: str
    status: Literal["ok", "runtime_error", "timeout", "system_error"]
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int = Field(ge=0)
    error: JobError | None = None

    @field_validator("stdout", "stderr", mode="before")
    @classmethod
    def _coerce_stream(cls, value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, bytes):
            return value.decode(errors="replace")
        raise TypeError("must be a string or bytes")
