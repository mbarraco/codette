from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.api.dependencies import require_role
from app.api.v1.handlers.invitation import (
    handle_create_invitation,
    handle_list_invitations,
)
from app.api.v1.schemas.invitation import InvitationCreate, InvitationResponse
from app.models import User
from app.models.user import UserRole

router = APIRouter()


@router.post(
    "/",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_invitation(
    body: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> InvitationResponse:
    return handle_create_invitation(db, body.email, body.role, current_user.id)  # type: ignore[return-value]


@router.get("/", response_model=list[InvitationResponse])
def list_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> list[InvitationResponse]:
    return handle_list_invitations(db)  # type: ignore[return-value]
