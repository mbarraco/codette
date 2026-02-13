"""API-layer tests for /api/v1/runs endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Problem, Run, Submission


def test_api_v1_runs_get_returns_empty_list(client: TestClient) -> None:
    response = client.get("/api/v1/runs/")
    assert response.status_code == 200
    assert response.json() == []


def test_api_v1_runs_get_returns_runs(
    client: TestClient, db: Session, problem: Problem
) -> None:
    sub = Submission(artifact_uri="gs://bucket/solution.py", problem_id=problem.id)
    db.add(sub)
    db.flush()

    run = Run(submission_id=sub.id, status="queued")
    db.add(run)
    db.flush()
    db.expire_all()

    response = client.get("/api/v1/runs/")
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1

    item = next(r for r in body if r["uuid"] == str(run.uuid))
    assert item["submission_uuid"] == str(sub.uuid)
    assert item["status"] == "queued"
    assert item["execution_ref"] is None
