from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.repository.invitation import InvitationRepository
from app.models import Invitation
from app.models.user import UserRole


def handle_create_invitation(
    db: Session, email: str, role: UserRole, created_by_id: int
) -> Invitation:
    repo = InvitationRepository()
    existing = repo.get_by_email(db, email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invitation for {email} already exists",
        )
    invitation = repo.create(db, email=email, role=role, created_by_id=created_by_id)
    db.commit()
    return invitation


def handle_list_invitations(db: Session) -> list[Invitation]:
    repo = InvitationRepository()
    return repo.list_all(db)
