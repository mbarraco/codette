from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.api.dependencies import get_current_user
from app.api.v1.handlers.auth import handle_login, handle_register
from app.api.v1.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.models import User

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    user = handle_register(db, body.email, body.password)
    return user  # type: ignore[return-value]


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    access_token = handle_login(db, body.email, body.password)
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return current_user  # type: ignore[return-value]
