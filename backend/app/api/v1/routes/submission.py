import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.api.v1.handlers.submission import (
    handle_create_submission,
    handle_delete_submission,
    handle_get_submission,
    handle_list_submissions,
)
from app.api.v1.schemas.submission import (
    SubmissionCreate,
    SubmissionDetail,
    SubmissionResponse,
)

router = APIRouter()


@router.get("/", response_model=list[SubmissionDetail])
def list_submissions(db: Session = Depends(get_db)) -> list[SubmissionDetail]:
    return handle_list_submissions(db)


@router.get("/{submission_uuid}", response_model=SubmissionDetail)
def get_submission(
    submission_uuid: uuid.UUID,
    db: Session = Depends(get_db),
) -> SubmissionDetail:
    return handle_get_submission(db, submission_uuid)


@router.post(
    "/", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED
)
def post_submission(
    body: SubmissionCreate,
    db: Session = Depends(get_db),
) -> SubmissionResponse:
    submission = handle_create_submission(db, body.problem_uuid, body.code)
    return submission


@router.delete("/{submission_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_submission(
    submission_uuid: uuid.UUID,
    db: Session = Depends(get_db),
) -> Response:
    handle_delete_submission(db, submission_uuid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
