import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.repository.problem import ProblemRepository
from app.models import Problem


def handle_get_problem(db: Session, problem_uuid: uuid.UUID) -> Problem:
    repo = ProblemRepository()
    problem = repo.get_by_uuid(db, problem_uuid)
    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem {problem_uuid} not found",
        )
    return problem
