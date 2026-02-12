from sqlalchemy.orm import Session, selectinload

from app.models import Submission, SubmissionQueue


class SubmissionRepository:
    def create(self, db: Session, problem_id: int, artifact_uri: str) -> Submission:
        """Insert a new Submission and flush to get its ID."""
        submission = Submission(problem_id=problem_id, artifact_uri=artifact_uri)
        db.add(submission)
        db.flush()
        return submission

    def list_all(self, db: Session) -> list[Submission]:
        """Return all submissions with related entities, newest first."""
        return list(
            db.query(Submission)
            .options(
                selectinload(Submission.runs),
                selectinload(Submission.queue_entries).noload(
                    SubmissionQueue.submission
                ),
                selectinload(Submission.evaluations),
            )
            .order_by(Submission.created_at.desc())
            .all()
        )
