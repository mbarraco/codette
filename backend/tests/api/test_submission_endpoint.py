"""API-layer tests for /api/v1/submissions endpoints."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.adapters.storage import StorageAdapter
from app.models import Problem, Run, Submission, SubmissionEvaluation, SubmissionQueue


def test_api_v1_submissions_post_returns_201_with_submission(
    client: TestClient, problem: Problem
) -> None:
    response = client.post(
        "/api/v1/submissions/",
        json={"problem_uuid": str(problem.uuid), "code": "def add(a, b): return a + b"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["problem_uuid"] == str(problem.uuid)
    assert body["uuid"] is not None
    assert "id" not in body
    assert body["artifact_uri"].startswith("gs://")
    assert "solution.py" in body["artifact_uri"]
    assert body["created_at"] is not None


def test_api_v1_submissions_post_uploads_artifact_to_storage(
    client: TestClient, db: Session, storage: StorageAdapter, problem: Problem
) -> None:
    code = "def solve(): return 42\n"
    response = client.post(
        "/api/v1/submissions/",
        json={"problem_uuid": str(problem.uuid), "code": code},
    )

    artifact_uri = response.json()["artifact_uri"]
    blob_path = artifact_uri.split("/", 3)[3]

    blob = storage._bucket.blob(blob_path)
    assert blob.exists()
    assert blob.download_as_text() == code
    sub_uuid = response.json()["uuid"]
    row = db.query(Submission).filter(Submission.uuid == sub_uuid).one()
    assert row is not None
    assert row.problem_id == problem.id


def test_api_v1_submissions_post_returns_422_when_code_missing(
    client: TestClient, problem: Problem
) -> None:
    response = client.post(
        "/api/v1/submissions/",
        json={"problem_uuid": str(problem.uuid)},
    )
    assert response.status_code == 422


def test_api_v1_submissions_post_returns_422_when_problem_uuid_missing(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/submissions/",
        json={"code": "x = 1"},
    )
    assert response.status_code == 422


def test_api_v1_submissions_post_returns_404_when_problem_not_found(
    client: TestClient,
) -> None:
    import uuid

    response = client.post(
        "/api/v1/submissions/",
        json={"problem_uuid": str(uuid.uuid4()), "code": "x = 1"},
    )
    assert response.status_code == 404


def test_api_v1_submissions_post_returns_422_when_body_empty(
    client: TestClient,
) -> None:
    response = client.post("/api/v1/submissions/")
    assert response.status_code == 422


def test_api_v1_submissions_get_returns_nested_data(
    client: TestClient, db: Session, problem: Problem
) -> None:
    sub = Submission(artifact_uri="gs://bucket/solution.py", problem_id=problem.id)
    db.add(sub)
    db.flush()

    run = Run(submission_id=sub.id, status="completed")
    db.add(run)
    db.flush()

    evaluation = SubmissionEvaluation(run_id=run.id, submission_id=sub.id, success=True)
    queue_entry = SubmissionQueue(submission_id=sub.id, attempt_count=1)
    db.add_all([evaluation, queue_entry])
    db.flush()
    db.expire_all()

    response = client.get("/api/v1/submissions/")

    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1

    detail = next(s for s in body if s["uuid"] == str(sub.uuid))
    assert "id" not in detail
    assert detail["problem_uuid"] == str(problem.uuid)
    assert len(detail["runs"]) == 1
    assert detail["runs"][0]["status"] == "completed"
    assert len(detail["evaluations"]) == 1
    assert detail["evaluations"][0]["success"] is True
    assert len(detail["queue_entries"]) == 1
    assert detail["queue_entries"][0]["attempt_count"] == 1


def test_api_v1_submissions_get_returns_empty_list(client: TestClient) -> None:
    response = client.get("/api/v1/submissions/")
    assert response.status_code == 200
    assert response.json() == []


def test_api_v1_submissions_uuid_get_returns_submission(
    client: TestClient, submission: Submission
) -> None:
    response = client.get(f"/api/v1/submissions/{submission.uuid}")
    assert response.status_code == 200
    body = response.json()
    assert body["uuid"] == str(submission.uuid)
    assert body["artifact_uri"] == submission.artifact_uri
    assert "id" not in body


def test_api_v1_submissions_uuid_get_returns_404_when_not_found(
    client: TestClient,
) -> None:
    response = client.get(f"/api/v1/submissions/{uuid.uuid4()}")
    assert response.status_code == 404


def test_api_v1_submissions_uuid_delete_returns_204(
    client: TestClient, submission: Submission
) -> None:
    response = client.delete(f"/api/v1/submissions/{submission.uuid}")
    assert response.status_code == 204

    # Verify it's no longer accessible
    response = client.get(f"/api/v1/submissions/{submission.uuid}")
    assert response.status_code == 404


def test_api_v1_submissions_uuid_delete_returns_404_when_not_found(
    client: TestClient,
) -> None:
    response = client.delete(f"/api/v1/submissions/{uuid.uuid4()}")
    assert response.status_code == 404


def test_api_v1_submissions_get_excludes_deleted(
    client: TestClient, db: Session, problem: Problem
) -> None:
    sub = Submission(artifact_uri="gs://bucket/solution.py", problem_id=problem.id)
    db.add(sub)
    db.flush()

    # Delete it
    client.delete(f"/api/v1/submissions/{sub.uuid}")

    # List should not include the deleted submission
    response = client.get("/api/v1/submissions/")
    assert response.status_code == 200
    uuids = [s["uuid"] for s in response.json()]
    assert str(sub.uuid) not in uuids
