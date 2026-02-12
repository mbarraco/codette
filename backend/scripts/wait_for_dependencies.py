#!/usr/bin/env python3
import os
import sys
from collections.abc import Callable

from google.cloud import storage
from sqlalchemy import create_engine, text
from tenacity import RetryCallState, Retrying, stop_after_attempt, wait_fixed


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}") from exc


def _run_with_retry(
    *, label: str, retries: int, sleep_seconds: float, check: Callable[[], None]
) -> None:
    def _before_sleep(retry_state: RetryCallState) -> None:
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        print(
            f"[wait] {label} not ready ({retry_state.attempt_number}/{retries}): {exc}",
            file=sys.stderr,
        )

    retrying = Retrying(
        stop=stop_after_attempt(retries),
        wait=wait_fixed(sleep_seconds),
        before_sleep=_before_sleep,
        reraise=True,
    )

    for attempt in retrying:
        with attempt:
            check()
        print(
            f"[wait] {label} ready on attempt "
            f"{attempt.retry_state.attempt_number}/{retries}"
        )
        return


def _wait_for_db(retries: int, sleep_seconds: float) -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to wait for Postgres readiness")

    engine = create_engine(database_url)
    try:

        def _check_db() -> None:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        _run_with_retry(
            label="db",
            retries=retries,
            sleep_seconds=sleep_seconds,
            check=_check_db,
        )
    finally:
        engine.dispose()


def _wait_for_storage(retries: int, sleep_seconds: float) -> None:
    storage_bucket = os.getenv("STORAGE_BUCKET")
    if not storage_bucket:
        raise RuntimeError(
            "STORAGE_BUCKET is required to validate local storage readiness"
        )

    emulator_host = os.getenv("STORAGE_EMULATOR_HOST")

    def _check_storage() -> None:
        client = storage.Client()
        bucket = client.bucket(storage_bucket)
        if not bucket.exists():
            if emulator_host:
                client.create_bucket(bucket)
                print(f"[wait] created missing emulator bucket {storage_bucket!r}")
            else:
                raise RuntimeError(
                    f"Bucket {storage_bucket!r} does not exist and no "
                    "STORAGE_EMULATOR_HOST is configured."
                )

    _run_with_retry(
        label="storage",
        retries=retries,
        sleep_seconds=sleep_seconds,
        check=_check_storage,
    )


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
