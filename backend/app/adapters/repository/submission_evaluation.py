from sqlalchemy.orm import Session

from app.models import SubmissionEvaluation


class SubmissionEvaluationRepository:
    def create(
        self,
        db: Session,
        run_id: int,
        submission_id: int,
        success: bool,
        metadata: dict | None = None,
    ) -> SubmissionEvaluation:
        """Insert a new SubmissionEvaluation and flush to get its ID."""
        evaluation = SubmissionEvaluation(
            run_id=run_id,
            submission_id=submission_id,
            success=success,
            metadata_=metadata,
        )
        db.add(evaluation)
        db.flush()
        return evaluation
