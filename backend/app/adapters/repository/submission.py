import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models import Submission, SubmissionQueue


class SubmissionRepository:
    def create(self, db: Session, problem_id: int, artifact_uri: str) -> Submission:
        """Insert a new Submission and flush to get its ID."""
        submission = Submission(problem_id=problem_id, artifact_uri=artifact_uri)
        db.add(submission)
        db.flush()
        return submission

    def get_by_uuid(self, db: Session, submission_uuid: uuid.UUID) -> Submission | None:
        return (
            db.query(Submission)
            .filter(Submission.uuid == submission_uuid, Submission.deleted_at.is_(None))
            .options(
                selectinload(Submission.problem),
                selectinload(Submission.runs),
                selectinload(Submission.queue_entries),
                selectinload(Submission.evaluations),
            )
            .one_or_none()
        )

    def list_all(self, db: Session) -> list[Submission]:
        """Return all non-deleted submissions with related entities, newest first."""
        return list(
            db.query(Submission)
            .filter(Submission.deleted_at.is_(None))
            .options(
                selectinload(Submission.problem),
                selectinload(Submission.runs),
                selectinload(Submission.queue_entries).noload(
                    SubmissionQueue.submission
                ),
                selectinload(Submission.evaluations),
            )
            .order_by(Submission.created_at.desc())
            .all()
        )

    def soft_delete(self, db: Session, submission: Submission) -> None:
        submission.deleted_at = func.now()  # type: ignore[assignment]
        db.flush()
