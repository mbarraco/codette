"""Shared error types for runner/grader job payloads."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class JobErrorCode(StrEnum):
    FILE_NOT_FOUND = "file_not_found"
    INVALID_ARTIFACT_URI = "invalid_artifact_uri"
    VALIDATION_ERROR = "validation_error"
    INTERNAL_ERROR = "internal_error"


class JobError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: JobErrorCode
    message: str
    details: dict[str, Any] | None = None
