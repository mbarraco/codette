#!/usr/bin/env python3
import os
import sys
import time

from google.cloud import storage
from sqlalchemy import create_engine, text


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}") from exc


def _wait_for_db(retries: int, sleep_seconds: float) -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to wait for Postgres readiness")

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            engine = create_engine(database_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            print(f"[wait] db ready on attempt {attempt}/{retries}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(
                f"[wait] db not ready ({attempt}/{retries}): {exc}",
                file=sys.stderr,
            )
            if attempt < retries:
                time.sleep(sleep_seconds)
    raise RuntimeError(
        f"DB readiness check failed after {retries} attempts"
    ) from last_error


def _wait_for_storage(retries: int, sleep_seconds: float) -> None:
    storage_bucket = os.getenv("STORAGE_BUCKET")
    if not storage_bucket:
        raise RuntimeError(
            "STORAGE_BUCKET is required to validate local storage readiness"
        )

    emulator_host = os.getenv("STORAGE_EMULATOR_HOST")
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            client = storage.Client()
            bucket = client.bucket(storage_bucket)
            if not bucket.exists():
                if emulator_host:
                    client.create_bucket(bucket)
                    print(
                        f"[wait] created missing emulator bucket {storage_bucket!r} "
                        f"on attempt {attempt}/{retries}"
                    )
                else:
                    raise RuntimeError(
                        f"Bucket {storage_bucket!r} does not exist and no "
                        "STORAGE_EMULATOR_HOST is configured."
                    )
            else:
                print(f"[wait] storage ready on attempt {attempt}/{retries}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(
                f"[wait] storage not ready ({attempt}/{retries}): {exc}",
                file=sys.stderr,
            )
            if attempt < retries:
                time.sleep(sleep_seconds)
    raise RuntimeError(
        f"Storage readiness check failed after {retries} attempts"
    ) from last_error


def main() -> int:
    retries = _get_int_env("WAIT_RETRIES", 30)
    sleep_seconds = float(os.getenv("WAIT_SLEEP_SECONDS", "1.0"))

    wait_for_db = os.getenv("WAIT_FOR_DB", "1") == "1"
    wait_for_storage = os.getenv("WAIT_FOR_STORAGE", "1") == "1"

    if wait_for_db:
        _wait_for_db(retries=retries, sleep_seconds=sleep_seconds)
    if wait_for_storage:
        _wait_for_storage(retries=retries, sleep_seconds=sleep_seconds)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
