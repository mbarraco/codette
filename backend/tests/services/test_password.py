from app.services.password import hash_password, verify_password


def test_hash_verify_round_trip() -> None:
    password = "my-secret-password"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True


def test_verify_wrong_password_returns_false() -> None:
    hashed = hash_password("correct-password")
    assert verify_password("wrong-password", hashed) is False
