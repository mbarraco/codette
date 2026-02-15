"""Runner orchestrator — handles GCS I/O and launches the harness subprocess.

CLI arguments:
    RUN_UUID        — unique identifier for this execution (sys.argv[1])

Environment variables:
    STORAGE_BUCKET  — GCS bucket name (set at deploy time)
"""

import subprocess
import sys
import tempfile
import time
from os import environ
from pathlib import Path
from typing import Any

from errors import JobErrorCode
from google.cloud import storage
from pydantic import ValidationError

from .schemas import (
    HarnessExecutionResult,
    HarnessInput,
    RunnerOutput,
    RunnerRequest,
    TestCasesConfig,
)


class Harness:
    """Prepares validated harness input and executes the harness subprocess."""

    def __init__(self, work_dir: Path, timeout_s: int) -> None:
        self._work_dir = work_dir
        self._timeout_s = timeout_s

    def run(self) -> HarnessExecutionResult:
        """Prepare input from submission files and execute the harness."""
        self._prepare_input()
        return self._execute()

    def _prepare_input(self) -> None:
        """Parse test_cases.json into a validated HarnessInput and write it to disk."""
        config = TestCasesConfig.model_validate_json(
            (self._work_dir / "test_cases.json").read_bytes()
        )

        harness_input = HarnessInput(
            solution_path=str(self._work_dir / "solution.py"),
            test_cases=config.test_cases,
            function_signature=config.function_signature,
        )

        self._input_file.write_text(harness_input.model_dump_json())

    @property
    def _input_file(self) -> Path:
        return self._work_dir / "harness_input.json"

    def _execute(self) -> HarnessExecutionResult:
        """Execute the harness subprocess and return the validated result."""
        start = time.monotonic()

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "runner.harness",
                    str(self._input_file),
                ],
                capture_output=True,
                text=True,
                timeout=self._timeout_s,
            )
            duration_ms = int((time.monotonic() - start) * 1000)
            return HarnessExecutionResult(
                status="ok" if result.returncode == 0 else "runtime_error",
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                duration_ms=duration_ms,
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            return HarnessExecutionResult(
                status="timeout",
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                exit_code=-1,
                duration_ms=duration_ms,
            )


def main() -> None:
    run_uuid = _validate()
    bucket = _get_bucket()
    gcs_prefix = f"gs://{bucket.name}/"

    output_uri: str | None = None
    try:
        request_data = _download_request(bucket, run_uuid)
        submission_artifact_uri = request_data.submission_artifact_uri
        output_uri = request_data.output_uri
        timeout_s = request_data.timeout_s

        artifact_path = _validate_artifact_uri(
            bucket,
            gcs_prefix,
            output_uri,
            run_uuid,
            submission_artifact_uri,
        )
        if artifact_path is None:
            raise SystemExit(1)

        submission_dir = artifact_path.rsplit("/", 1)[0]

        work_dir = Path(tempfile.mkdtemp(prefix="runner_"))
        _download_submission_files(bucket, submission_dir, work_dir)

        harness = Harness(work_dir, timeout_s)
        result = harness.run()
        _upload_result(bucket, gcs_prefix, output_uri, run_uuid, result)
    except FileNotFoundError as exc:
        _upload_error(
            bucket,
            gcs_prefix,
            output_uri,
            run_uuid,
            str(exc),
            error_code=JobErrorCode.FILE_NOT_FOUND,
        )
        raise SystemExit(1) from exc
    except ValidationError as exc:
        _upload_error(
            bucket,
            gcs_prefix,
            output_uri,
            run_uuid,
            "Payload validation failed",
            error_code=JobErrorCode.VALIDATION_ERROR,
            details={"errors": exc.errors(include_url=False)},
        )
        raise SystemExit(1) from exc
    except Exception as exc:
        _upload_error(
            bucket,
            gcs_prefix,
            output_uri,
            run_uuid,
            f"Unhandled runner error: {exc}",
            error_code=JobErrorCode.INTERNAL_ERROR,
            details={"exception_type": type(exc).__name__},
        )
        raise


def _validate_artifact_uri(
    bucket: storage.Bucket,
    gcs_prefix: str,
    output_uri: str,
    run_uuid: str,
    submission_artifact_uri: str,
) -> str | None:
    """Validate the artifact URI and return the GCS object path, or None on failure."""
    if not submission_artifact_uri.startswith(gcs_prefix):
        _upload_error(
            bucket,
            gcs_prefix,
            output_uri,
            run_uuid,
            f"Bad artifact URI: {submission_artifact_uri}",
            error_code=JobErrorCode.INVALID_ARTIFACT_URI,
            details={"submission_artifact_uri": submission_artifact_uri},
        )
        return None
    return submission_artifact_uri[len(gcs_prefix) :]


def _validate() -> str:
    if len(sys.argv) < 2:
        print("Usage: run.py <RUN_UUID>", file=sys.stderr)
        sys.exit(1)
    return sys.argv[1]


def _get_bucket() -> storage.Bucket:
    bucket_name = environ["STORAGE_BUCKET"]
    client = storage.Client()
    return client.bucket(bucket_name)


def _download_request(bucket: storage.Bucket, run_uuid: str) -> RunnerRequest:
    """Download and parse the runner_request.json from GCS."""
    blob = bucket.blob(f"runs/{run_uuid}/runner_request.json")
    return RunnerRequest.model_validate_json(blob.download_as_text())


def _download_submission_files(
    bucket: storage.Bucket, submission_dir: str, work_dir: Path
) -> None:
    """Download required submission files into the work directory."""
    required_files = ("solution.py", "test_cases.json")
    for file_name in required_files:
        blob_path = f"{submission_dir}/{file_name}"
        blob = bucket.blob(blob_path)
        if not blob.exists():
            raise FileNotFoundError(f"Missing required submission file: {blob_path}")
        blob.download_to_filename(work_dir / file_name)


def _upload_result(
    bucket: storage.Bucket,
    gcs_prefix: str,
    output_uri: str,
    run_uuid: str,
    result: HarnessExecutionResult,
) -> None:
    """Build RunnerOutput from the harness result and upload to the output URI."""
    runner_output = RunnerOutput(
        run_uuid=run_uuid,
        status=result.status,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        duration_ms=result.duration_ms,
    )

    output_path = output_uri[len(gcs_prefix) :]
    bucket.blob(output_path).upload_from_string(
        runner_output.model_dump_json(), content_type="application/json"
    )


def _upload_error(
    bucket: storage.Bucket,
    gcs_prefix: str,
    output_uri: str | None,
    run_uuid: str,
    error: str,
    error_code: JobErrorCode,
    details: dict[str, Any] | None = None,
) -> None:
    """Upload a system_error RunnerOutput."""
    if output_uri is None:
        print(
            f"Runner failed before output_uri was available: {error}", file=sys.stderr
        )
        return

    runner_output = RunnerOutput(
        run_uuid=run_uuid,
        status="system_error",
        stdout="",
        stderr=error,
        exit_code=-1,
        duration_ms=0,
        error={"code": error_code, "message": error, "details": details},
    )
    output_path = output_uri[len(gcs_prefix) :]
    bucket.blob(output_path).upload_from_string(
        runner_output.model_dump_json(), content_type="application/json"
    )
    print(f"Runner failed: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
