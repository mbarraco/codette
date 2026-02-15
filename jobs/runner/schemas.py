"""Pydantic schemas for runner request/input/output payloads."""

from typing import Any, Literal

from errors import JobError
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator


class RunnerRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    submission_artifact_uri: str
    output_uri: str
    timeout_s: int = Field(gt=0)


class TestCase(BaseModel):
    model_config = ConfigDict(extra="ignore")

    input: list[Any] = Field(default_factory=list)
    expected: Any = None


class WrappedTestCasesConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    function_signature: str | None = None
    test_cases: list[TestCase] = Field(default_factory=list)


_TEST_CASES_CONFIG_ADAPTER = TypeAdapter(WrappedTestCasesConfig | list[TestCase])


def parse_test_cases_config(raw: Any) -> tuple[list[TestCase], str | None]:
    """Validate accepted test-case config shapes and return normalized values."""
    parsed = _TEST_CASES_CONFIG_ADAPTER.validate_python(raw)
    if isinstance(parsed, list):
        return parsed, None
    return parsed.test_cases, parsed.function_signature


class HarnessInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    solution_path: str
    test_cases: list[TestCase]
    function_signature: str | None = None


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
