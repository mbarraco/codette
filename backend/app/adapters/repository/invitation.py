import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Invitation
from app.models.user import UserRole


class InvitationRepository:
    def get_by_uuid(self, db: Session, invitation_uuid: uuid.UUID) -> Invitation | None:
        return (
            db.query(Invitation)
            .filter(Invitation.uuid == invitation_uuid)
            .one_or_none()
        )

    def get_by_email(self, db: Session, email: str) -> Invitation | None:
        return db.query(Invitation).filter(Invitation.email == email).one_or_none()

    def create(
        self,
        db: Session,
        email: str,
        role: UserRole,
        created_by_id: int | None = None,
    ) -> Invitation:
        invitation = Invitation(email=email, role=role, created_by_id=created_by_id)
        db.add(invitation)
        db.flush()
        return invitation

    def list_all(self, db: Session) -> list[Invitation]:
        return list(db.query(Invitation).order_by(Invitation.created_at.desc()).all())

    def mark_used(self, db: Session, invitation: Invitation) -> None:
        invitation.used_at = func.now()  # type: ignore[assignment]
        db.flush()
