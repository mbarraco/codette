from sqlalchemy.orm import Session

from app.models import Submission


class SubmissionRepository:
    def create(self, db: Session, problem_id: int, artifact_uri: str) -> Submission:
        """Insert a new Submission and flush to get its ID."""
        submission = Submission(problem_id=problem_id, artifact_uri=artifact_uri)
        db.add(submission)
        db.flush()
        return submission
