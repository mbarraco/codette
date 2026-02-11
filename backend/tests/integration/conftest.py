from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.settings import TestSettings
from app.models import Base, Problem, Submission, SubmissionQueue

RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources"

test_settings = TestSettings()


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(test_settings.database_url)
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


@pytest.fixture()
def submission(db: Session, problem: Problem, solution_file: Path) -> Submission:
    bucket = test_settings.storage_bucket
    # TODO: upload solution_file to fake-gcs-server when StorageAdapter is implemented
    s = Submission(
        artifact_uri=f"gs://{bucket}/submissions/test/{solution_file.name}",
        problem_id=problem.id,
    )
    db.add(s)
    db.flush()
    return s


@pytest.fixture()
def queue_entry(db: Session, submission: Submission) -> SubmissionQueue:
    entry = SubmissionQueue(submission_id=submission.id)
    db.add(entry)
    db.flush()
    return entry
