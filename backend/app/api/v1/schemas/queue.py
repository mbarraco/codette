from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from app.api.v1.schemas.submission import EvaluationSummary, RunSummary


class QueueEntryResponse(BaseModel):
    uuid: UUID
    submission_uuid: UUID
    problem_uuid: UUID
    attempt_count: int
    last_checked_at: datetime | None
    last_error: str | None
    created_at: datetime
    runs: list[RunSummary]
    evaluations: list[EvaluationSummary]

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def flatten_submission(cls, data: Any) -> Any:
        if hasattr(data, "submission"):
            sub = data.submission
            data.submission_uuid = sub.uuid
            data.problem_uuid = sub.problem.uuid
            data.runs = sub.runs
            data.evaluations = sub.evaluations
        return data
