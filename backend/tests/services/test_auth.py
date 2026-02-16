import pytest
from sqlalchemy.orm import Session

from app.adapters.repository.invitation import InvitationRepository
from app.adapters.repository.user import UserRepository
from app.models import Invitation, User
from app.models.user import UserRole
from app.services.auth import (
    AuthenticationError,
    RegistrationError,
    authenticate_user,
    register_user,
)


@pytest.fixture()
def user_repo() -> UserRepository:
    return UserRepository()


@pytest.fixture()
def invitation_repo() -> InvitationRepository:
    return InvitationRepository()


def test_register_user_with_valid_invitation(
    db: Session,
    user_repo: UserRepository,
    invitation_repo: InvitationRepository,
    unused_invitation: Invitation,
) -> None:
    user = register_user(
        db, user_repo, invitation_repo, unused_invitation.email, "password123"
    )
    assert user.email == unused_invitation.email
    assert user.role == unused_invitation.role
    db.refresh(unused_invitation)
    assert unused_invitation.used_at is not None


def test_register_user_fails_without_invitation(
    db: Session,
    user_repo: UserRepository,
    invitation_repo: InvitationRepository,
) -> None:
    with pytest.raises(RegistrationError, match="No invitation"):
        register_user(db, user_repo, invitation_repo, "noinvite@test.com", "pw")


def test_register_user_fails_with_used_invitation(
    db: Session,
    user_repo: UserRepository,
    invitation_repo: InvitationRepository,
    unused_invitation: Invitation,
) -> None:
    invitation_repo.mark_used(db, unused_invitation)
    with pytest.raises(RegistrationError, match="already been used"):
        register_user(db, user_repo, invitation_repo, unused_invitation.email, "pw")


def test_register_user_fails_with_existing_email(
    db: Session,
    user_repo: UserRepository,
    invitation_repo: InvitationRepository,
    student_user: User,
) -> None:
    inv = Invitation(email=student_user.email, role=UserRole.STUDENT)
    db.add(inv)
    db.flush()
    with pytest.raises(RegistrationError, match="already exists"):
        register_user(db, user_repo, invitation_repo, student_user.email, "pw")


def test_authenticate_user_with_valid_credentials(
    db: Session,
    user_repo: UserRepository,
    student_user: User,
) -> None:
    user = authenticate_user(db, user_repo, "student@test.com", "password123")
    assert user.id == student_user.id


def test_authenticate_user_fails_with_wrong_password(
    db: Session,
    user_repo: UserRepository,
    student_user: User,
) -> None:
    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        authenticate_user(db, user_repo, "student@test.com", "wrong-password")


def test_authenticate_user_fails_with_unknown_email(
    db: Session,
    user_repo: UserRepository,
) -> None:
    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        authenticate_user(db, user_repo, "unknown@test.com", "pw")
