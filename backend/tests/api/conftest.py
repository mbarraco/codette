import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.adapters.db import get_db
from app.api.main import app


@pytest.fixture()
def client(db: Session):
    """TestClient whose DB dependency is the transactional test session."""

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    yield TestClient(app)
    app.dependency_overrides.clear()
