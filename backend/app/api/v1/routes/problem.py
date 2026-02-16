from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.api.dependencies import get_current_user, require_role
from app.api.v1.handlers.problem import (
    handle_create_problem,
    handle_delete_problem,
    handle_get_problem,
    handle_list_problems,
    handle_update_problem,
)
from app.api.v1.schemas.problem import (
    ProblemCreate,
    ProblemResponse,
    ProblemUpdate,
)
from app.models import User
from app.models.user import UserRole

router = APIRouter()

_teacher_or_admin = require_role(UserRole.TEACHER, UserRole.ADMIN)


@router.post(
    "/",
    response_model=ProblemResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_problem(
    body: ProblemCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(_teacher_or_admin),
) -> ProblemResponse:
    return handle_create_problem(
        db,
        title=body.title,
        statement=body.statement,
        hints=body.hints,
        examples=body.examples,
        test_cases=(
            [tc.model_dump() for tc in body.test_cases] if body.test_cases else None
        ),
        function_signature=body.function_signature,
    )


@router.get(
    "/",
    response_model=list[ProblemResponse],
    status_code=status.HTTP_200_OK,
)
def list_problems(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[ProblemResponse]:
    return handle_list_problems(db)


@router.get(
    "/{problem_uuid}",
    response_model=ProblemResponse,
    status_code=status.HTTP_200_OK,
)
def get_problem(
    problem_uuid: UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ProblemResponse:
    return handle_get_problem(db, problem_uuid)


@router.patch(
    "/{problem_uuid}",
    response_model=ProblemResponse,
    status_code=status.HTTP_200_OK,
)
def patch_problem(
    problem_uuid: UUID,
    body: ProblemUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(_teacher_or_admin),
) -> ProblemResponse:
    fields = body.model_dump(exclude_unset=True)
    return handle_update_problem(db, problem_uuid, **fields)


@router.delete(
    "/{problem_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_problem(
    problem_uuid: UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(_teacher_or_admin),
) -> Response:
    handle_delete_problem(db, problem_uuid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
