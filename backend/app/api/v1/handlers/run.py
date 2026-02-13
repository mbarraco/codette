from sqlalchemy.orm import Session

from app.adapters.repository.run import RunRepository
from app.models import Run


def handle_list_runs(db: Session) -> list[Run]:
    repo = RunRepository()
    return repo.list_all(db)
