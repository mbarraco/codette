from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SubmissionCreate(BaseModel):
    code: str
    problem_uuid: UUID


class SubmissionResponse(BaseModel):
    uuid: UUID
    artifact_uri: str
    problem_uuid: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RunSummary(BaseModel):
    uuid: UUID
    status: str
    execution_ref: str | None
    failure_stage: str | None
    failure_error: str | None
    runner_output_uri: str | None
    grader_output_uri: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QueueEntrySummary(BaseModel):
    uuid: UUID
    attempt_count: int
    last_checked_at: datetime | None
    last_error: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationSummary(BaseModel):
    uuid: UUID
    success: bool
    metadata_: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubmissionDetail(BaseModel):
    uuid: UUID
    artifact_uri: str
    problem_uuid: UUID
    created_at: datetime
    runs: list[RunSummary]
    queue_entries: list[QueueEntrySummary]
    evaluations: list[EvaluationSummary]

    model_config = ConfigDict(from_attributes=True)
