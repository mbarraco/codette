"""API-layer tests for POST /submissions."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.adapters.storage import StorageAdapter
from app.models import Problem, Submission


def test_returns_201_with_submission(client: TestClient, problem: Problem) -> None:
    response = client.post(
        "/submissions/",
        json={"problem_id": problem.id, "code": "def add(a, b): return a + b"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["problem_id"] == problem.id
    assert body["id"] is not None
    assert body["uuid"] is not None
    assert body["artifact_uri"].startswith("gs://")
    assert "solution.py" in body["artifact_uri"]
    assert body["created_at"] is not None


def test_artifact_uploaded_to_storage(
    client: TestClient, db: Session, storage: StorageAdapter, problem: Problem
) -> None:
    code = "def solve(): return 42\n"
    response = client.post(
        "/submissions/",
        json={"problem_id": problem.id, "code": code},
    )

    artifact_uri = response.json()["artifact_uri"]
    blob_path = artifact_uri.split("/", 3)[3]

    blob = storage._bucket.blob(blob_path)
    assert blob.exists()
    assert blob.download_as_text() == code
    row = db.get(Submission, response.json()["id"])
    assert row is not None
    assert row.problem_id == problem.id


def test_missing_code_returns_422(client: TestClient, problem: Problem) -> None:
    response = client.post(
        "/submissions/",
        json={"problem_id": problem.id},
    )
    assert response.status_code == 422


def test_missing_problem_id_returns_422(client: TestClient) -> None:
    response = client.post(
        "/submissions/",
        json={"code": "x = 1"},
    )
    assert response.status_code == 422


def test_empty_body_returns_422(client: TestClient) -> None:
    response = client.post("/submissions/")
    assert response.status_code == 422
