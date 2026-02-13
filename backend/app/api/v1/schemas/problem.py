from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProblemResponse(BaseModel):
    uuid: UUID
    statement: str
    hints: str | None
    examples: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
