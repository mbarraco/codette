import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Problem


class ProblemRepository:
    def get_by_uuid(self, db: Session, problem_uuid: uuid.UUID) -> Problem | None:
        return (
            db.query(Problem)
            .filter(Problem.uuid == problem_uuid, Problem.deleted_at.is_(None))
            .one_or_none()
        )

    def create(
        self,
        db: Session,
        title: str,
        statement: str,
        hints: str | None,
        examples: str | None,
        test_cases: list[dict] | None,
        function_signature: str,
    ) -> Problem:
        problem = Problem(
            title=title,
            statement=statement,
            hints=hints,
            examples=examples,
            test_cases=test_cases,
            function_signature=function_signature,
        )
        db.add(problem)
        db.flush()
        return problem

    def list_all(self, db: Session) -> list[Problem]:
        return list(
            db.query(Problem)
            .filter(Problem.deleted_at.is_(None))
            .order_by(Problem.created_at.desc())
            .all()
        )

    def update(self, db: Session, problem: Problem, **fields: object) -> Problem:
        for key, value in fields.items():
            setattr(problem, key, value)
        db.flush()
        return problem

    def soft_delete(self, db: Session, problem: Problem) -> None:
        problem.deleted_at = func.now()  # type: ignore[assignment]
        db.flush()
