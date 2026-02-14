from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Submission, SubmissionQueue


class SubmissionQueueRepository:
    def create(self, db: Session, submission_id: int) -> SubmissionQueue:
        entry = SubmissionQueue(submission_id=submission_id)
        db.add(entry)
        db.flush()
        return entry

    def claim_next(self, db: Session) -> SubmissionQueue | None:
        """Claim the oldest unclaimed queue entry.

        Uses SELECT ... FOR UPDATE SKIP LOCKED.
        """
        stmt = (
            select(SubmissionQueue)
            .where(SubmissionQueue.last_checked_at.is_(None))
            .order_by(SubmissionQueue.created_at.asc())
            .limit(1)
            .with_for_update(of=SubmissionQueue, skip_locked=True)
        )
        entry = db.scalars(stmt).first()
        if entry is None:
            return None

        entry.last_checked_at = datetime.now(UTC)
        entry.attempt_count += 1
        db.flush()
        return entry

    def list_all(self, db: Session) -> list[SubmissionQueue]:
        stmt = (
            select(SubmissionQueue)
            .options(
                selectinload(SubmissionQueue.submission).selectinload(
                    Submission.problem
                ),
                selectinload(SubmissionQueue.submission).selectinload(Submission.runs),
                selectinload(SubmissionQueue.submission).selectinload(
                    Submission.evaluations
                ),
            )
            .order_by(SubmissionQueue.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    def mark_failed(self, db: Session, entry: SubmissionQueue, error: str) -> None:
        """Record failure details for the current attempt.

        ``attempt_count`` is incremented in ``claim_next`` when the worker
        dequeues an item for processing; do not increment again here.
        """
        entry.last_error = error
        db.flush()
