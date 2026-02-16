"""API-layer tests for /api/v1/invitations endpoints."""

from fastapi.testclient import TestClient

from app.models import Invitation


def test_api_v1_invitations_post_returns_201_as_admin(
    admin_client: TestClient,
) -> None:
    response = admin_client.post(
        "/api/v1/invitations/",
        json={"email": "newuser@test.com", "role": "student"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "newuser@test.com"
    assert body["role"] == "student"
    assert body["used_at"] is None


def test_api_v1_invitations_post_returns_403_as_student(
    auth_client: TestClient,
) -> None:
    response = auth_client.post(
        "/api/v1/invitations/",
        json={"email": "newuser@test.com", "role": "student"},
    )
    assert response.status_code == 403


def test_api_v1_invitations_post_returns_401_without_auth(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/invitations/",
        json={"email": "newuser@test.com", "role": "student"},
    )
    assert response.status_code in (401, 403)


def test_api_v1_invitations_get_returns_list_as_admin(
    admin_client: TestClient, unused_invitation: Invitation
) -> None:
    response = admin_client.get("/api/v1/invitations/")
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1


def test_api_v1_invitations_post_returns_409_on_duplicate_email(
    admin_client: TestClient, unused_invitation: Invitation
) -> None:
    response = admin_client.post(
        "/api/v1/invitations/",
        json={"email": unused_invitation.email, "role": "student"},
    )
    assert response.status_code == 409
