from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.api.v1.handlers.problem import handle_get_problem
from app.api.v1.schemas.problem import ProblemResponse

router = APIRouter()


@router.get(
    "/{problem_uuid}",
    response_model=ProblemResponse,
    status_code=status.HTTP_200_OK,
)
def get_problem(
    problem_uuid: UUID,
    db: Session = Depends(get_db),
) -> ProblemResponse:
    return handle_get_problem(db, problem_uuid)
