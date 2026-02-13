"""API-layer tests for /api/v1/queue endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Problem, Run, Submission, SubmissionEvaluation, SubmissionQueue


def test_api_v1_queue_get_returns_empty_list(client: TestClient) -> None:
    response = client.get("/api/v1/queue/")
    assert response.status_code == 200
    assert response.json() == []


def test_api_v1_queue_get_returns_entries(
    client: TestClient, db: Session, problem: Problem
) -> None:
    sub = Submission(artifact_uri="gs://bucket/solution.py", problem_id=problem.id)
    db.add(sub)
    db.flush()

    entry = SubmissionQueue(submission_id=sub.id, attempt_count=0)
    db.add(entry)
    db.flush()
    db.expire_all()

    response = client.get("/api/v1/queue/")
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1

    item = next(e for e in body if e["uuid"] == str(entry.uuid))
    assert item["submission_uuid"] == str(sub.uuid)
    assert item["problem_uuid"] == str(problem.uuid)
    assert item["attempt_count"] == 0
    assert item["last_checked_at"] is None
    assert item["last_error"] is None


def test_api_v1_queue_get_includes_runs_and_evaluations(
    client: TestClient, db: Session, problem: Problem
) -> None:
    sub = Submission(artifact_uri="gs://bucket/solution.py", problem_id=problem.id)
    db.add(sub)
    db.flush()

    run = Run(submission_id=sub.id, status="done")
    db.add(run)
    db.flush()

    evaluation = SubmissionEvaluation(run_id=run.id, submission_id=sub.id, success=True)
    entry = SubmissionQueue(submission_id=sub.id, attempt_count=1)
    db.add_all([evaluation, entry])
    db.flush()
    db.expire_all()

    response = client.get("/api/v1/queue/")
    assert response.status_code == 200
    body = response.json()

    item = next(e for e in body if e["uuid"] == str(entry.uuid))
    assert len(item["runs"]) == 1
    assert item["runs"][0]["status"] == "done"
    assert len(item["evaluations"]) == 1
    assert item["evaluations"][0]["success"] is True
