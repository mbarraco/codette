import logging

from sqlalchemy.orm import Session

from app.adapters.repository.invitation import InvitationRepository
from app.models.user import UserRole

logger = logging.getLogger(__name__)


def bootstrap_admin_invitation(db: Session, admin_email: str | None) -> None:
    if admin_email is None:
        return

    repo = InvitationRepository()
    existing = repo.get_by_email(db, admin_email)
    if existing is not None:
        return

    repo.create(db, email=admin_email, role=UserRole.ADMIN)
    db.commit()
    logger.info("Bootstrapped admin invitation for %s", admin_email)
