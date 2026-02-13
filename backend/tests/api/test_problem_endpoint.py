import uuid

from fastapi.testclient import TestClient

from app.models import Problem


def test_api_v1_problems_uuid_get_returns_problem(
    client: TestClient, problem: Problem
) -> None:
    response = client.get(f"/api/v1/problems/{problem.uuid}")
    assert response.status_code == 200
    body = response.json()
    assert body["uuid"] == str(problem.uuid)
    assert body["statement"] == problem.statement
    assert body["hints"] == problem.hints
    assert body["examples"] == problem.examples
    assert "created_at" in body
    assert "id" not in body


def test_api_v1_problems_uuid_get_returns_404_when_not_found(
    client: TestClient,
) -> None:
    response = client.get(f"/api/v1/problems/{uuid.uuid4()}")
    assert response.status_code == 404
