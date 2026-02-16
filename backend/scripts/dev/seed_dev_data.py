#!/usr/bin/env python3
"""Seed strategy: use API endpoints for data changes, assume API is already up,
keep flow simple, and fall back to direct DB access only for admin bootstrap invitation.
"""

import json
import os
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any
from urllib import error, request

from app.adapters.db import SessionLocal
from app.adapters.repository.invitation import InvitationRepository
from app.api.v1.schemas.auth import TokenResponse, UserResponse
from app.api.v1.schemas.invitation import InvitationResponse
from app.api.v1.schemas.problem import ProblemResponse
from app.models.user import UserRole


@dataclass(frozen=True)
class ProblemSeed:
    title: str
    statement: str
    hints: str | None
    examples: str | None
    test_cases: list[dict] | None
    function_signature: str


@dataclass(frozen=True)
class UserSeed:
    email: str
    password: str
    role: UserRole


@dataclass(frozen=True)
class InvitationSeed:
    email: str
    role: UserRole


SEED_PROBLEMS: tuple[ProblemSeed, ...] = (
    ProblemSeed(
        title="Two Sum",
        statement=(
            "Given two integers, return their sum as an integer. "
            "Assume inputs are always valid numbers."
        ),
        hints="You only need the + operator and to return the result.",
        examples="add(2, 3) == 5\nadd(-1, 4) == 3",
        test_cases=[
            {"input": [2, 3], "output": 5},
            {"input": [-1, 4], "output": 3},
            {"input": [0, 0], "output": 0},
        ],
        function_signature="def add(a, b):",
    ),
    ProblemSeed(
        title="FizzBuzz",
        statement=(
            "Return a list of strings from 1 to n. "
            "Use Fizz for multiples of 3, Buzz for multiples of 5, "
            "and FizzBuzz for multiples of both."
        ),
        hints="Check divisibility by 15 before 3 or 5.",
        examples='fizz_buzz(5) == ["1", "2", "Fizz", "4", "Buzz"]',
        test_cases=[
            {"input": [3], "output": ["1", "2", "Fizz"]},
            {"input": [5], "output": ["1", "2", "Fizz", "4", "Buzz"]},
            {
                "input": [15],
                "output": [
                    "1",
                    "2",
                    "Fizz",
                    "4",
                    "Buzz",
                    "Fizz",
                    "7",
                    "8",
                    "Fizz",
                    "Buzz",
                    "11",
                    "Fizz",
                    "13",
                    "14",
                    "FizzBuzz",
                ],
            },
        ],
        function_signature="def fizzbuzz(n):",
    ),
    ProblemSeed(
        title="Palindrome Number",
        statement=(
            "Given an integer x, return true if x reads the same forward and backward. "
            "Negative numbers are not palindromes."
        ),
        hints="Convert to string and compare with its reverse.",
        examples="is_palindrome(121) == True\nis_palindrome(-121) == False",
        test_cases=[
            {"input": [121], "output": True},
            {"input": [-121], "output": False},
            {"input": [10], "output": False},
        ],
        function_signature="def is_palindrome(x):",
    ),
)


SEED_USERS: tuple[UserSeed, ...] = (
    UserSeed(email="admin@codette.dev", password="password", role=UserRole.ADMIN),
    UserSeed(email="teacher@codette.dev", password="password", role=UserRole.TEACHER),
    UserSeed(email="student@codette.dev", password="password", role=UserRole.STUDENT),
)


SEED_INVITATIONS: tuple[InvitationSeed, ...] = (
    InvitationSeed(email="test@test.com", role=UserRole.STUDENT),
)


class SeedError(RuntimeError):
    pass


def _response_detail(body_text: str) -> str:
    detail = body_text
    try:
        payload = json.loads(body_text)
        if isinstance(payload, dict):
            raw_detail = payload.get("detail")
            if isinstance(raw_detail, str):
                detail = raw_detail
            else:
                detail = str(raw_detail)
    except Exception:
        return body_text
    return detail


def _is_expected_register_conflict(detail: str) -> bool:
    return "already exists" in detail or "already been used" in detail


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._access_token: str | None = None

    def set_access_token(self, access_token: str) -> None:
        self._access_token = access_token

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        expected: set[int],
        payload: dict | None = None,
        auth: bool = False,
    ) -> dict | list:
        status_code, body_text = self._request_raw(
            method,
            path,
            payload=payload,
            auth=auth,
        )
        if status_code not in expected:
            detail = _response_detail(body_text)
            raise SeedError(f"{method} {path} failed with {status_code}: {detail}")

        if status_code == HTTPStatus.NO_CONTENT:
            return {}
        if not body_text:
            return {}

        parsed_payload = json.loads(body_text)
        if not isinstance(parsed_payload, dict | list):
            raise SeedError(f"{method} {path} returned unexpected JSON payload")
        return parsed_payload

    def try_login(self, email: str, password: str) -> str | None:
        status_code, body_text = self._request_raw(
            "POST",
            "/api/v1/auth/login",
            payload={"email": email, "password": password},
        )
        if status_code == HTTPStatus.UNAUTHORIZED:
            return None
        if status_code != HTTPStatus.OK:
            detail = _response_detail(body_text)
            raise SeedError(
                "POST /api/v1/auth/login failed for "
                f"{email} with {status_code}: {detail}"
            )

        try:
            body = TokenResponse.model_validate_json(body_text)
        except Exception as exc:
            raise SeedError(
                f"POST /api/v1/auth/login returned invalid payload for {email}"
            ) from exc
        return body.access_token

    def register_user(self, email: str, password: str) -> bool:
        status_code, body_text = self._request_raw(
            "POST",
            "/api/v1/auth/register",
            payload={"email": email, "password": password},
        )
        if status_code == HTTPStatus.CREATED:
            try:
                UserResponse.model_validate_json(body_text)
            except Exception as exc:
                raise SeedError(
                    f"POST /api/v1/auth/register returned invalid payload for {email}"
                ) from exc
            return True
        if status_code == HTTPStatus.BAD_REQUEST:
            detail = _response_detail(body_text)
            if _is_expected_register_conflict(detail):
                return False
            raise SeedError(
                "POST /api/v1/auth/register failed for "
                f"{email} with {status_code}: {detail}"
            )

        detail = _response_detail(body_text)
        raise SeedError(
            "POST /api/v1/auth/register failed for "
            f"{email} with {status_code}: {detail}"
        )

    def list_invitations(self) -> list[InvitationResponse]:
        body = self._request_json(
            "GET",
            "/api/v1/invitations/",
            expected={HTTPStatus.OK},
            auth=True,
        )
        if not isinstance(body, list):
            raise SeedError("GET /api/v1/invitations/ did not return a list")

        invitations: list[InvitationResponse] = []
        for item in body:
            try:
                invitations.append(InvitationResponse.model_validate(item))
            except Exception as exc:
                raise SeedError(
                    "GET /api/v1/invitations/ returned an invalid item payload"
                ) from exc
        return invitations

    def create_invitation(self, email: str, role: UserRole) -> InvitationResponse:
        body = self._request_json(
            "POST",
            "/api/v1/invitations/",
            expected={HTTPStatus.CREATED},
            payload={"email": email, "role": role.value},
            auth=True,
        )
        if not isinstance(body, dict):
            raise SeedError("POST /api/v1/invitations/ did not return an object")
        try:
            return InvitationResponse.model_validate(body)
        except Exception as exc:
            raise SeedError(
                "POST /api/v1/invitations/ returned invalid payload"
            ) from exc

    def list_problems(self) -> list[ProblemResponse]:
        body = self._request_json(
            "GET",
            "/api/v1/problems/",
            expected={HTTPStatus.OK},
            auth=True,
        )
        if not isinstance(body, list):
            raise SeedError("GET /api/v1/problems/ did not return a list")

        problems: list[ProblemResponse] = []
        for item in body:
            try:
                problems.append(ProblemResponse.model_validate(item))
            except Exception as exc:
                raise SeedError(
                    "GET /api/v1/problems/ returned an invalid item payload"
                ) from exc
        return problems

    def create_problem(self, payload: dict[str, Any]) -> ProblemResponse:
        body = self._request_json(
            "POST",
            "/api/v1/problems/",
            expected={HTTPStatus.CREATED},
            payload=payload,
            auth=True,
        )
        if not isinstance(body, dict):
            raise SeedError("POST /api/v1/problems/ did not return an object")
        try:
            return ProblemResponse.model_validate(body)
        except Exception as exc:
            raise SeedError("POST /api/v1/problems/ returned invalid payload") from exc

    def update_problem(
        self, problem_uuid: str, payload: dict[str, Any]
    ) -> ProblemResponse:
        body = self._request_json(
            "PATCH",
            f"/api/v1/problems/{problem_uuid}",
            expected={HTTPStatus.OK},
            payload=payload,
            auth=True,
        )
        if not isinstance(body, dict):
            raise SeedError(
                f"PATCH /api/v1/problems/{problem_uuid} did not return an object"
            )
        try:
            return ProblemResponse.model_validate(body)
        except Exception as exc:
            raise SeedError(
                f"PATCH /api/v1/problems/{problem_uuid} returned invalid payload"
            ) from exc

    def _request_raw(
        self,
        method: str,
        path: str,
        *,
        payload: dict | None = None,
        auth: bool = False,
    ) -> tuple[int, str]:
        headers: dict[str, str] | None = None
        if auth:
            if self._access_token is None:
                raise SeedError(
                    f"{method} {path} requested auth without an access token"
                )
            headers = {"Authorization": f"Bearer {self._access_token}"}

        body: bytes | None = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers = {**(headers or {}), "Content-Type": "application/json"}
        req = request.Request(
            url=f"{self._base_url}{path}",
            data=body,
            method=method,
            headers=headers or {},
        )

        try:
            with request.urlopen(req, timeout=10.0) as response:
                return response.getcode(), response.read().decode("utf-8")
        except error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8")
        except error.URLError as exc:
            raise SeedError(f"{method} {path} failed to connect: {exc}") from exc


def _bootstrap_admin_invitation(email: str) -> None:
    """Create the first admin invitation directly so API registration can bootstrap."""
    db = SessionLocal()
    try:
        repo = InvitationRepository()
        invitation = repo.get_by_email(db, email)
        if invitation is not None:
            return

        repo.create(db, email=email, role=UserRole.ADMIN, created_by_id=None)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _bootstrap_admin(api: ApiClient, admin_seed: UserSeed) -> tuple[str, bool]:
    token = api.try_login(admin_seed.email, admin_seed.password)
    if token is not None:
        api.set_access_token(token)
        return token, False

    _bootstrap_admin_invitation(admin_seed.email)
    created = api.register_user(admin_seed.email, admin_seed.password)
    token = api.try_login(admin_seed.email, admin_seed.password)
    if token is None:
        raise SeedError(
            "Admin user exists but cannot log in with seeded password: "
            f"{admin_seed.email}"
        )
    api.set_access_token(token)
    return token, created


def _seed_users(api: ApiClient) -> int:
    users_created = 0
    invitation_emails: set[str] = set()
    for item in api.list_invitations():
        invitation_emails.add(item.email)

    for seed in SEED_INVITATIONS:
        if seed.email in invitation_emails:
            continue
        api.create_invitation(seed.email, seed.role)
        invitation_emails.add(seed.email)

    for seed in SEED_USERS:
        if seed.role == UserRole.ADMIN:
            continue

        if seed.email not in invitation_emails:
            api.create_invitation(seed.email, seed.role)
            invitation_emails.add(seed.email)

        if api.register_user(seed.email, seed.password):
            users_created += 1

        token = api.try_login(seed.email, seed.password)
        if token is None:
            raise SeedError(
                f"User {seed.email} exists but cannot log in with seeded password."
            )

    return users_created


def _seed_problems(api: ApiClient) -> tuple[int, int]:
    existing_by_title: dict[str, ProblemResponse] = {}
    for problem in api.list_problems():
        existing_by_title.setdefault(problem.title, problem)

    created = 0
    updated = 0
    for seed in SEED_PROBLEMS:
        payload = {
            "title": seed.title,
            "statement": seed.statement,
            "hints": seed.hints,
            "examples": seed.examples,
            "test_cases": seed.test_cases,
            "function_signature": seed.function_signature,
        }
        existing = existing_by_title.get(seed.title)
        if existing is None:
            existing_by_title[seed.title] = api.create_problem(payload)
            created += 1
            continue

        api.update_problem(str(existing.uuid), payload)
        updated += 1

    return created, updated


def main() -> int:
    admin_seed = next(seed for seed in SEED_USERS if seed.role == UserRole.ADMIN)
    base_url = os.getenv("SEED_API_BASE_URL", "http://127.0.0.1:8000")
    api = ApiClient(base_url)

    _, admin_created = _bootstrap_admin(api, admin_seed)
    users_created = _seed_users(api)
    created, updated = _seed_problems(api)

    print(
        "[seed] development data seeded successfully "
        f"(problems_total={len(SEED_PROBLEMS)}, "
        f"created={created}, updated={updated}, "
        f"users_created={users_created + int(admin_created)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
