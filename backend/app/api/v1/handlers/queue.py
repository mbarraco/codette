from sqlalchemy.orm import Session

from app.adapters.repository.submission_queue import SubmissionQueueRepository
from app.models import SubmissionQueue


def handle_list_queue_entries(db: Session) -> list[SubmissionQueue]:
    repo = SubmissionQueueRepository()
    return repo.list_all(db)
