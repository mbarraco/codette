"""Pydantic schemas for grader request/output payloads."""

from typing import Literal

from errors import JobError
from pydantic import BaseModel, ConfigDict


class GraderRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    runner_output_uri: str
    output_uri: str


class RunnerOutput(BaseModel):
    """Runner output as consumed by the grader (extra fields ignored)."""

    model_config = ConfigDict(extra="ignore")

    status: str
    stdout: str = ""
    stderr: str = ""
    error: JobError | None = None


class HarnessTestResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    passed: bool


class HarnessResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    results: list[HarnessTestResult] = []


class GraderOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["grader_output.v1"] = "grader_output.v1"
    run_uuid: str
    verdict: Literal["pass", "fail", "system_error"]
    summary: str
    metadata: dict | None = None
    error: JobError | None = None
