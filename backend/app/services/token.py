from datetime import UTC, datetime, timedelta

import jwt


def create_access_token(
    user_id: int,
    secret_key: str,
    algorithm: str = "HS256",
    expire_minutes: int = 60,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=expire_minutes),
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_access_token(
    token: str,
    secret_key: str,
    algorithm: str = "HS256",
) -> dict:
    return jwt.decode(token, secret_key, algorithms=[algorithm])
