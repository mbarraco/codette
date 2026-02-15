"""Runner orchestrator — handles GCS I/O and launches the harness subprocess.

CLI arguments:
    RUN_UUID        — unique identifier for this execution (sys.argv[1])

Environment variables:
    STORAGE_BUCKET  — GCS bucket name (set at deploy time)
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from typing import Any

from google.cloud import storage


def main() -> None:
    run_uuid = _validate()
    bucket = _get_bucket()
    gcs_prefix = f"gs://{bucket.name}/"

    request_data = _download_request(bucket, run_uuid)
    submission_artifact_uri: str = request_data["submission_artifact_uri"]
    output_uri: str = request_data["output_uri"]
    timeout_s: int = request_data["timeout_s"]

    artifact_path = _validate_artifact_uri(
        bucket,
        gcs_prefix,
        output_uri,
        run_uuid,
        submission_artifact_uri,
    )
    if artifact_path is None:
        return

    submission_dir = artifact_path.rsplit("/", 1)[0]

    work_dir = tempfile.mkdtemp(prefix="runner_")
    _download_submission_files(bucket, submission_dir, work_dir)

    harness_input_file, harness_output_file = _prepare_harness_input(work_dir)

    result = _run_harness(harness_input_file, harness_output_file, timeout_s)

    _upload_result(bucket, gcs_prefix, output_uri, run_uuid, result)


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
        )
        return None
    return submission_artifact_uri[len(gcs_prefix) :]


def _validate() -> str:
    if len(sys.argv) < 2:
        print("Usage: run.py <RUN_UUID>", file=sys.stderr)
        sys.exit(1)
    run_uuid = sys.argv[1]
    return run_uuid


def _get_bucket() -> storage.Bucket:
    bucket_name = os.environ["STORAGE_BUCKET"]
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    return bucket


def _download_request(bucket: storage.Bucket, run_uuid: str) -> dict[str, Any]:
    """Download and parse the runner_request.json from GCS."""
    blob = bucket.blob(f"runs/{run_uuid}/runner_request.json")
    return json.loads(blob.download_as_text())


def _download_submission_files(
    bucket: storage.Bucket, submission_dir: str, work_dir: str
) -> None:
    """Download solution.py and test_cases.json into the work directory."""
    bucket.blob(f"{submission_dir}/solution.py").download_to_filename(
        os.path.join(work_dir, "solution.py")
    )

    test_cases_blob = bucket.blob(f"{submission_dir}/test_cases.json")
    test_cases_path = os.path.join(work_dir, "test_cases.json")
    if test_cases_blob.exists():
        test_cases_blob.download_to_filename(test_cases_path)
    else:
        with open(test_cases_path, "w") as f:
            json.dump({"test_cases": []}, f)


def _prepare_harness_input(work_dir: str) -> tuple[str, str]:
    """Parse test cases and write the harness input file.

    Expects wrapped format {"function_signature": ..., "test_cases": [...]}.

    Returns (harness_input_path, harness_output_path).
    """
    test_cases_path = os.path.join(work_dir, "test_cases.json")
    with open(test_cases_path) as f:
        raw = json.load(f)

    if not isinstance(raw, dict) or "test_cases" not in raw:
        raise ValueError(
            "test_cases.json must be an object containing a 'test_cases' key"
        )

    test_cases = raw["test_cases"]
    function_signature = raw.get("function_signature")

    harness_input = {
        "solution_path": os.path.join(work_dir, "solution.py"),
        "test_cases": test_cases,
        "function_signature": function_signature,
    }

    harness_input_file = os.path.join(work_dir, "harness_input.json")
    harness_output_file = os.path.join(work_dir, "harness_output.json")

    with open(harness_input_file, "w") as f:
        json.dump(harness_input, f)

    return harness_input_file, harness_output_file


def _run_harness(input_file: str, output_file: str, timeout_s: int) -> dict[str, Any]:
    """Execute the harness subprocess and return raw result fields."""
    harness_script = os.path.join(os.path.dirname(__file__), "harness.py")
    start = time.monotonic()

    try:
        result = subprocess.run(
            [sys.executable, harness_script, input_file, output_file],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        return {
            "status": "ok" if result.returncode == 0 else "runtime_error",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "duration_ms": duration_ms,
        }
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        return {
            "status": "timeout",
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "exit_code": -1,
            "duration_ms": duration_ms,
        }


def _upload_result(
    bucket: storage.Bucket,
    gcs_prefix: str,
    output_uri: str,
    run_uuid: str,
    result: dict[str, Any],
) -> None:
    """Build RunnerOutput and upload to the output URI."""
    stdout = result["stdout"]
    stderr = result["stderr"]

    runner_output = {
        "schema_version": "runner_output.v1",
        "run_uuid": run_uuid,
        "status": result["status"],
        "stdout": stdout
        if isinstance(stdout, str)
        else stdout.decode(errors="replace"),
        "stderr": stderr
        if isinstance(stderr, str)
        else stderr.decode(errors="replace"),
        "exit_code": result["exit_code"],
        "duration_ms": result["duration_ms"],
    }

    output_path = output_uri[len(gcs_prefix) :]
    bucket.blob(output_path).upload_from_string(
        json.dumps(runner_output), content_type="application/json"
    )


def _upload_error(
    bucket: storage.Bucket,
    gcs_prefix: str,
    output_uri: str,
    run_uuid: str,
    error: str,
) -> None:
    """Upload a system_error RunnerOutput."""
    runner_output = {
        "schema_version": "runner_output.v1",
        "run_uuid": run_uuid,
        "status": "system_error",
        "stdout": "",
        "stderr": error,
        "exit_code": -1,
        "duration_ms": 0,
    }
    output_path = output_uri[len(gcs_prefix) :]
    bucket.blob(output_path).upload_from_string(
        json.dumps(runner_output), content_type="application/json"
    )
    print(f"Runner failed: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
