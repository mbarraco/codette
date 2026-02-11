from sqlalchemy.orm import Session

from app.adapters.repository.submission_queue import SubmissionQueueRepository
from app.models import SubmissionQueue


class SeaWorker:
    def __init__(self, db: Session, queue_repo: SubmissionQueueRepository) -> None:
        self.db = db
        self.queue_repo = queue_repo

    def process_next(self) -> SubmissionQueue | None:
        """Claim the next queue entry and process it.

        For now only the claim step is implemented.
        Future steps: create run → runner → grader → write evaluation.
        """
        entry = self.queue_repo.claim_next(self.db)
        if entry is None:
            return None

        # TODO: create run record
        # TODO: write submission_input to storage
        # TODO: invoke runner
        # TODO: invoke grader
        # TODO: read grader verdict, write evaluation

        return entry
