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


def handle_list_problems(db: Session) -> list[Problem]:
    repo = ProblemRepository()
    return repo.list_all(db)


def handle_create_problem(
    db: Session,
    title: str,
    statement: str,
    hints: str | None,
    examples: str | None,
    test_cases: list[dict] | None,
    function_signature: str,
) -> Problem:
    repo = ProblemRepository()
    problem = repo.create(
        db,
        title=title,
        statement=statement,
        hints=hints,
        examples=examples,
        test_cases=test_cases,
        function_signature=function_signature,
    )
    db.commit()
    return problem


def handle_update_problem(
    db: Session,
    problem_uuid: uuid.UUID,
    **fields: object,
) -> Problem:
    repo = ProblemRepository()
    problem = repo.get_by_uuid(db, problem_uuid)
    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem {problem_uuid} not found",
        )
    problem = repo.update(db, problem, **fields)
    db.commit()
    return problem


def handle_delete_problem(db: Session, problem_uuid: uuid.UUID) -> None:
    repo = ProblemRepository()
    problem = repo.get_by_uuid(db, problem_uuid)
    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem {problem_uuid} not found",
        )
    repo.soft_delete(db, problem)
    db.commit()
