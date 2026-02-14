from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Run


class RunRepository:
    def create(self, db: Session, submission_id: int) -> Run:
        """Insert a new Run with status 'queued' and flush to get its ID."""
        run = Run(submission_id=submission_id)
        db.add(run)
        db.flush()
        return run

    def list_all(self, db: Session) -> list[Run]:
        stmt = (
            select(Run)
            .options(selectinload(Run.submission))
            .order_by(Run.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    def update(
        self,
        db: Session,
        run: Run,
        *,
        status: str | None = None,
        execution_ref: str | None = None,
        failure_stage: str | None = None,
        failure_error: str | None = None,
        runner_output_uri: str | None = None,
        grader_output_uri: str | None = None,
    ) -> None:
        """Update one or more fields on a Run."""
        if status is not None:
            run.status = status
        if execution_ref is not None:
            run.execution_ref = execution_ref
        if failure_stage is not None:
            run.failure_stage = failure_stage
        if failure_error is not None:
            run.failure_error = failure_error
        if runner_output_uri is not None:
            run.runner_output_uri = runner_output_uri
        if grader_output_uri is not None:
            run.grader_output_uri = grader_output_uri
        db.flush()
