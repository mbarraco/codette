from sqlalchemy.orm import Session

from app.models import Run


class RunRepository:
    def create(self, db: Session, submission_id: int) -> Run:
        """Insert a new Run with status 'queued' and flush to get its ID."""
        run = Run(submission_id=submission_id)
        db.add(run)
        db.flush()
        return run

    def update(
        self,
        db: Session,
        run: Run,
        *,
        status: str | None = None,
        execution_ref: str | None = None,
        runner_output_uri: str | None = None,
        grader_output_uri: str | None = None,
    ) -> None:
        """Update one or more fields on a Run."""
        if status is not None:
            run.status = status
        if execution_ref is not None:
            run.execution_ref = execution_ref
        if runner_output_uri is not None:
            run.runner_output_uri = runner_output_uri
        if grader_output_uri is not None:
            run.grader_output_uri = grader_output_uri
        db.flush()
