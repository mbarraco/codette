import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.api.main import app
from app.core.settings import get_settings
from app.models import User
from app.services.token import create_access_token


@pytest.fixture()
def client(db: Session):
    """TestClient whose DB dependency is the transactional test session."""

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    yield TestClient(app)
    app.dependency_overrides.clear()


def _make_token(user: User) -> str:
    settings = get_settings()
    return create_access_token(user.id, settings.jwt_secret_key, settings.jwt_algorithm)


@pytest.fixture()
def auth_client(client: TestClient, student_user: User) -> TestClient:
    """TestClient with a valid student Bearer token."""
    client.headers["Authorization"] = f"Bearer {_make_token(student_user)}"
    return client


@pytest.fixture()
def admin_client(client: TestClient, admin_user: User) -> TestClient:
    """TestClient with a valid admin Bearer token."""
    client.headers["Authorization"] = f"Bearer {_make_token(admin_user)}"
    return client
