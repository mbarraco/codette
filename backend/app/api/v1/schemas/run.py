from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class RunResponse(BaseModel):
    uuid: UUID
    submission_uuid: UUID
    status: str
    execution_ref: str | None
    failure_stage: str | None
    failure_error: str | None
    runner_output_uri: str | None
    grader_output_uri: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def flatten_submission(cls, data: Any) -> Any:
        if hasattr(data, "submission"):
            data.submission_uuid = data.submission.uuid
        return data
