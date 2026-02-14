from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class TestCase(BaseModel):
    input: list[Any]
    output: Any


class ProblemCreate(BaseModel):
    title: str
    statement: str
    hints: str | None = None
    examples: str | None = None
    test_cases: list[TestCase] | None = None
    function_signature: str


class ProblemUpdate(BaseModel):
    title: str | None = None
    statement: str | None = None
    hints: str | None = None
    examples: str | None = None
    test_cases: list[TestCase] | None = None
    function_signature: str | None = None

    @model_validator(mode="after")
    def reject_null_function_signature(self) -> "ProblemUpdate":
        if (
            "function_signature" in self.model_fields_set
            and self.function_signature is None
        ):
            raise ValueError("function_signature cannot be null")
        return self


class ProblemResponse(BaseModel):
    uuid: UUID
    title: str
    statement: str
    hints: str | None
    examples: str | None
    test_cases: list[TestCase] | None
    function_signature: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
