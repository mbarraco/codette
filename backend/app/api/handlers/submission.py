from sqlalchemy.orm import Session

from app.adapters.repository.submission import SubmissionRepository
from app.adapters.storage import StorageAdapter
from app.core.settings import get_settings
from app.models import Submission
from app.services.submission import create_submission


def handle_create_submission(db: Session, problem_id: int, code: str) -> Submission:
    settings = get_settings()
    storage = StorageAdapter(settings.storage_bucket)
    repo = SubmissionRepository()
    submission = create_submission(db, repo, storage, problem_id, code)
    db.commit()
    return submission
