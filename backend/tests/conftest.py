from pathlib import Path

import pytest
from google.cloud import storage as gcs
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.adapters.storage import StorageAdapter
from app.core.settings import TestSettings
from app.models import Base, Problem

RESOURCES_DIR = Path(__file__).resolve().parent / "resources"

test_settings = TestSettings()


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(test_settings.database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db(engine) -> Session:
    """Yields a DB session that rolls back after each test."""
    conn = engine.connect()
    txn = conn.begin()
    session = Session(bind=conn)
    yield session
    session.close()
    txn.rollback()
    conn.close()


@pytest.fixture()
def problem(db: Session) -> Problem:
    p = Problem(
        title="Two Sum",
        statement="Return the sum of two integers.",
        hints="Think about the + operator.",
        examples="add(1, 2) == 3",
    )
    db.add(p)
    db.flush()
    return p


@pytest.fixture()
def solution_file() -> Path:
    """Path to the test submission source file."""
    path = RESOURCES_DIR / "solution.py"
    assert path.exists(), f"Test resource missing: {path}"
    return path


@pytest.fixture(scope="session")
def _gcs_bucket():
    """Ensure the test bucket exists in fake-gcs-server (session-scoped)."""
    client = gcs.Client()
    bucket = client.bucket(test_settings.storage_bucket)
    if not bucket.exists():
        client.create_bucket(bucket)
    return bucket


@pytest.fixture()
def storage(_gcs_bucket) -> StorageAdapter:
    return StorageAdapter(test_settings.storage_bucket)
