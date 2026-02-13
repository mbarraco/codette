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
    assert body["title"] == problem.title
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


def test_api_v1_problems_post_returns_201_with_problem(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/problems/",
        json={
            "title": "Multiply",
            "statement": "Return the product of two integers.",
            "hints": "Use the * operator.",
            "examples": "mul(2, 3) == 6",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Multiply"
    assert body["statement"] == "Return the product of two integers."
    assert body["hints"] == "Use the * operator."
    assert body["examples"] == "mul(2, 3) == 6"
    assert body["test_cases"] is None
    assert "uuid" in body
    assert "id" not in body


def test_api_v1_problems_post_returns_201_with_test_cases(
    client: TestClient,
) -> None:
    test_cases = [
        {"input": [2, 3], "output": 6},
        {"input": [0, 5], "output": 0},
        {"input": [-1, 4], "output": -4},
    ]
    response = client.post(
        "/api/v1/problems/",
        json={
            "title": "Multiply",
            "statement": "Return the product of two integers.",
            "test_cases": test_cases,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["test_cases"] == test_cases


def test_api_v1_problems_post_returns_422_when_title_missing(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/problems/",
        json={"statement": "Some statement."},
    )
    assert response.status_code == 422


def test_api_v1_problems_post_returns_422_when_statement_missing(
    client: TestClient,
) -> None:
    response = client.post("/api/v1/problems/", json={"title": "Some title"})
    assert response.status_code == 422


def test_api_v1_problems_get_returns_list(client: TestClient, problem: Problem) -> None:
    response = client.get("/api/v1/problems/")
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    assert body[0]["uuid"] == str(problem.uuid)


def test_api_v1_problems_get_returns_empty_list(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/problems/")
    assert response.status_code == 200
    assert response.json() == []


def test_api_v1_problems_uuid_patch_updates_fields(
    client: TestClient, problem: Problem
) -> None:
    response = client.patch(
        f"/api/v1/problems/{problem.uuid}",
        json={"title": "Updated Title", "statement": "Updated statement."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Updated Title"
    assert body["statement"] == "Updated statement."
    assert body["uuid"] == str(problem.uuid)
    # Unchanged fields preserved
    assert body["hints"] == problem.hints


def test_api_v1_problems_uuid_patch_updates_test_cases(
    client: TestClient, problem: Problem
) -> None:
    test_cases = [{"input": [1, 2], "output": 3}]
    response = client.patch(
        f"/api/v1/problems/{problem.uuid}",
        json={"test_cases": test_cases},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["test_cases"] == test_cases
    assert body["statement"] == problem.statement


def test_api_v1_problems_uuid_patch_returns_404_when_not_found(
    client: TestClient,
) -> None:
    response = client.patch(
        f"/api/v1/problems/{uuid.uuid4()}",
        json={"statement": "Does not matter."},
    )
    assert response.status_code == 404


def test_api_v1_problems_uuid_delete_returns_204(
    client: TestClient, problem: Problem
) -> None:
    response = client.delete(f"/api/v1/problems/{problem.uuid}")
    assert response.status_code == 204

    # GET after delete returns 404
    response = client.get(f"/api/v1/problems/{problem.uuid}")
    assert response.status_code == 404


def test_api_v1_problems_uuid_delete_returns_404_when_not_found(
    client: TestClient,
) -> None:
    response = client.delete(f"/api/v1/problems/{uuid.uuid4()}")
    assert response.status_code == 404
