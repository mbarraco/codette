from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.api.v1.handlers.run import handle_list_runs
from app.api.v1.schemas.run import RunResponse

router = APIRouter()


@router.get("/", response_model=list[RunResponse])
def get_runs(db: Session = Depends(get_db)) -> list[RunResponse]:
    return handle_list_runs(db)
