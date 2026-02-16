import pytest

from app.services.token import create_access_token, decode_access_token


def test_create_decode_round_trip() -> None:
    token = create_access_token(42, "secret", "HS256", expire_minutes=60)
    payload = decode_access_token(token, "secret", "HS256")
    assert payload["sub"] == "42"
    assert "exp" in payload
    assert "iat" in payload


def test_expired_token_raises() -> None:
    token = create_access_token(1, "secret", "HS256", expire_minutes=-1)
    with pytest.raises(Exception):
        decode_access_token(token, "secret", "HS256")


def test_invalid_token_raises() -> None:
    with pytest.raises(Exception):
        decode_access_token("not-a-valid-token", "secret", "HS256")


def test_wrong_secret_raises() -> None:
    token = create_access_token(1, "secret-a", "HS256", expire_minutes=60)
    with pytest.raises(Exception):
        decode_access_token(token, "secret-b", "HS256")
