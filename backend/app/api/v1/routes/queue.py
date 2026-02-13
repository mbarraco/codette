from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.api.v1.handlers.queue import handle_list_queue_entries
from app.api.v1.schemas.queue import QueueEntryResponse

router = APIRouter()


@router.get("/", response_model=list[QueueEntryResponse])
def get_queue_entries(db: Session = Depends(get_db)) -> list[QueueEntryResponse]:
    return handle_list_queue_entries(db)
