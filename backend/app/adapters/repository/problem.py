import uuid

from sqlalchemy.orm import Session

from app.models import Problem


class ProblemRepository:
    def get_by_uuid(self, db: Session, problem_uuid: uuid.UUID) -> Problem | None:
        return db.query(Problem).filter(Problem.uuid == problem_uuid).one_or_none()
