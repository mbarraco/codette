from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.repository.invitation import InvitationRepository
from app.adapters.repository.user import UserRepository
from app.core.settings import get_settings
from app.models import User
from app.services.auth import (
    AuthenticationError,
    RegistrationError,
    authenticate_user,
    register_user,
)
from app.services.token import create_access_token


def handle_register(db: Session, email: str, password: str) -> User:
    user_repo = UserRepository()
    invitation_repo = InvitationRepository()
    try:
        user = register_user(db, user_repo, invitation_repo, email, password)
    except RegistrationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    db.commit()
    return user


def handle_login(db: Session, email: str, password: str) -> str:
    user_repo = UserRepository()
    try:
        user = authenticate_user(db, user_repo, email, password)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    settings = get_settings()
    return create_access_token(
        user.id,
        settings.jwt_secret_key,
        settings.jwt_algorithm,
        settings.access_token_expire_minutes,
    )
