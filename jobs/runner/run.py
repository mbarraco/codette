"""Runner orchestrator — handles GCS I/O and launches the harness subprocess.

Environment variables:
    RUN_UUID        — unique identifier for this execution
    STORAGE_BUCKET  — GCS bucket name (set at deploy time)
"""

import json
import os
import subprocess
import sys
import tempfile
import time

from google.cloud import storage


def main() -> None:
    run_uuid = os.environ["RUN_UUID"]
    bucket_name = os.environ["STORAGE_BUCKET"]

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # 1. Download runner_request.json
    request_path = f"runs/{run_uuid}/runner_request.json"
    request_blob = bucket.blob(request_path)
    request_data = json.loads(request_blob.download_as_text())

    submission_artifact_uri: str = request_data["submission_artifact_uri"]
    output_uri: str = request_data["output_uri"]
    timeout_s: int = request_data["timeout_s"]

    # 2. Derive submission base path from artifact_uri
    #    artifact_uri is gs://bucket/submissions/{uuid}/solution.py
    prefix = f"gs://{bucket_name}/"
    if not submission_artifact_uri.startswith(prefix):
        _fail(
            bucket, output_uri, run_uuid, f"Bad artifact URI: {submission_artifact_uri}"
        )
        return

    artifact_path = submission_artifact_uri[len(prefix) :]
    submission_dir = artifact_path.rsplit("/", 1)[0]  # submissions/{uuid}

    # 3. Download solution.py and test_cases.json into a work directory
    work_dir = tempfile.mkdtemp(prefix="runner_")
    solution_local = os.path.join(work_dir, "solution.py")
    test_cases_local = os.path.join(work_dir, "test_cases.json")

    bucket.blob(f"{submission_dir}/solution.py").download_to_filename(solution_local)

    test_cases_blob = bucket.blob(f"{submission_dir}/test_cases.json")
    if test_cases_blob.exists():
        test_cases_blob.download_to_filename(test_cases_local)
    else:
        # No test cases — write empty list
        with open(test_cases_local, "w") as f:
            json.dump([], f)

    # 4. Prepare harness input
    with open(test_cases_local) as f:
        test_cases = json.load(f)

    harness_input = {
        "solution_path": solution_local,
        "test_cases": test_cases,
    }

    harness_input_file = os.path.join(work_dir, "harness_input.json")
    harness_output_file = os.path.join(work_dir, "harness_output.json")

    with open(harness_input_file, "w") as f:
        json.dump(harness_input, f)

    # 5. Run harness as subprocess
    harness_script = os.path.join(os.path.dirname(__file__), "harness.py")
    start = time.monotonic()

    try:
        result = subprocess.run(
            [sys.executable, harness_script, harness_input_file, harness_output_file],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        status = "ok" if result.returncode == 0 else "runtime_error"
        stdout = result.stdout
        stderr = result.stderr
        exit_code = result.returncode
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        status = "timeout"
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        exit_code = -1

    # 6. Build RunnerOutput
    runner_output = {
        "schema_version": "runner_output.v1",
        "run_uuid": run_uuid,
        "status": status,
        "stdout": stdout
        if isinstance(stdout, str)
        else stdout.decode(errors="replace"),
        "stderr": stderr
        if isinstance(stderr, str)
        else stderr.decode(errors="replace"),
        "exit_code": exit_code,
        "duration_ms": duration_ms,
    }

    # 7. Upload to output_uri
    output_path = output_uri[len(prefix) :]
    bucket.blob(output_path).upload_from_string(
        json.dumps(runner_output), content_type="application/json"
    )

    print(f"Runner completed: status={status} duration_ms={duration_ms}")


def _fail(bucket, output_uri: str, run_uuid: str, error: str) -> None:
    """Upload a system_error RunnerOutput."""
    prefix = f"gs://{bucket.name}/"
    output_path = output_uri[len(prefix) :]
    runner_output = {
        "schema_version": "runner_output.v1",
        "run_uuid": run_uuid,
        "status": "system_error",
        "stdout": "",
        "stderr": error,
        "exit_code": -1,
        "duration_ms": 0,
    }
    bucket.blob(output_path).upload_from_string(
        json.dumps(runner_output), content_type="application/json"
    )
    print(f"Runner failed: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
