from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.api.handlers.submission import (
    handle_create_submission,
    handle_list_submissions,
)
from app.api.schemas.submission import (
    SubmissionCreate,
    SubmissionDetail,
    SubmissionResponse,
)

router = APIRouter()


@router.get("/", response_model=list[SubmissionDetail])
def list_submissions(db: Session = Depends(get_db)) -> list[SubmissionDetail]:
    return handle_list_submissions(db)


@router.post(
    "/", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED
)
def post_submission(
    body: SubmissionCreate,
    db: Session = Depends(get_db),
) -> SubmissionResponse:
    submission = handle_create_submission(db, body.problem_id, body.code)
    return submission
