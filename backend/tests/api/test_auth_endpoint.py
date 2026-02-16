"""API-layer tests for /api/v1/auth endpoints."""

from fastapi.testclient import TestClient

from app.models import Invitation, User


def test_api_v1_auth_register_post_returns_201(
    client: TestClient, unused_invitation: Invitation
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": unused_invitation.email, "password": "secret123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == unused_invitation.email
    assert body["role"] == unused_invitation.role.value
    assert "uuid" in body
    assert "password_hash" not in body


def test_api_v1_auth_register_post_returns_400_without_invitation(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "nobody@test.com", "password": "secret123"},
    )
    assert response.status_code == 400


def test_api_v1_auth_login_post_returns_200_with_token(
    client: TestClient, student_user: User
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "student@test.com", "password": "password123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_api_v1_auth_login_post_returns_401_with_bad_credentials(
    client: TestClient, student_user: User
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "student@test.com", "password": "wrong"},
    )
    assert response.status_code == 401


def test_api_v1_auth_me_get_returns_200(
    auth_client: TestClient, student_user: User
) -> None:
    response = auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == student_user.email
    assert body["role"] == "student"


def test_api_v1_auth_me_get_returns_401_without_token(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)
