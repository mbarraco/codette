from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SubmissionQueue


class SubmissionQueueRepository:
    def claim_next(self, db: Session) -> SubmissionQueue | None:
        """Claim the oldest unclaimed queue entry.

        Uses SELECT ... FOR UPDATE SKIP LOCKED.
        """
        stmt = (
            select(SubmissionQueue)
            .where(SubmissionQueue.last_checked_at.is_(None))
            .order_by(SubmissionQueue.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        entry = db.scalars(stmt).first()
        if entry is None:
            return None

        entry.last_checked_at = datetime.now(UTC)
        entry.attempt_count += 1
        db.flush()
        return entry

    def mark_failed(self, db: Session, entry: SubmissionQueue, error: str) -> None:
        """Record a failure on a queue entry."""
        entry.last_error = error
        entry.attempt_count += 1
        db.flush()
