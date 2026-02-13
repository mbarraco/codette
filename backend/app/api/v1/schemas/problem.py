from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TestCase(BaseModel):
    input: list[Any]
    output: Any


class ProblemCreate(BaseModel):
    title: str
    statement: str
    hints: str | None = None
    examples: str | None = None
    test_cases: list[TestCase] | None = None


class ProblemUpdate(BaseModel):
    title: str | None = None
    statement: str | None = None
    hints: str | None = None
    examples: str | None = None
    test_cases: list[TestCase] | None = None


class ProblemResponse(BaseModel):
    uuid: UUID
    title: str
    statement: str
    hints: str | None
    examples: str | None
    test_cases: list[TestCase] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
