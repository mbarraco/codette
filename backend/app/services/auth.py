from sqlalchemy.orm import Session

from app.adapters.repository.invitation import InvitationRepository
from app.adapters.repository.user import UserRepository
from app.models import User
from app.services.password import hash_password, verify_password


class RegistrationError(Exception):
    pass


class AuthenticationError(Exception):
    pass


def register_user(
    db: Session,
    user_repo: UserRepository,
    invitation_repo: InvitationRepository,
    email: str,
    password: str,
) -> User:
    invitation = invitation_repo.get_by_email(db, email)
    if invitation is None:
        raise RegistrationError("No invitation found for this email")
    if invitation.used_at is not None:
        raise RegistrationError("Invitation has already been used")

    existing = user_repo.get_by_email(db, email)
    if existing is not None:
        raise RegistrationError("A user with this email already exists")

    pw_hash = hash_password(password)
    user = user_repo.create(
        db,
        email=email,
        password_hash=pw_hash,
        role=invitation.role,
    )
    invitation_repo.mark_used(db, invitation)
    return user


def authenticate_user(
    db: Session,
    user_repo: UserRepository,
    email: str,
    password: str,
) -> User:
    user = user_repo.get_by_email(db, email)
    if user is None:
        raise AuthenticationError("Invalid email or password")
    if not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password")
    return user
