from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SubmissionCreate(BaseModel):
    code: str
    problem_id: int


class SubmissionResponse(BaseModel):
    id: int
    uuid: UUID
    artifact_uri: str
    problem_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
