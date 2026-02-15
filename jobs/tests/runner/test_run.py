"""Unit tests for the runner orchestrator (run.py)."""

import json
import os
import subprocess
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from google.cloud import storage as gcs

from run import (
    _download_request,
    _download_submission_files,
    _prepare_harness_input,
    _run_harness,
    _upload_error,
    _upload_result,
    _validate,
    _validate_artifact_uri,
)


# --- _validate ---


def test_validate_returns_run_uuid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["run.py", "abc-123"])
    assert _validate() == "abc-123"


def test_validate_exits_when_no_args(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["run.py"])
    with pytest.raises(SystemExit) as exc_info:
        _validate()
    assert exc_info.value.code == 1


# --- _validate_artifact_uri ---


def test_validate_artifact_uri_returns_path_on_valid_uri(
    gcs_bucket: gcs.Bucket,
) -> None:
    gcs_prefix = f"gs://{gcs_bucket.name}/"
    result = _validate_artifact_uri(
        gcs_bucket,
        gcs_prefix,
        f"{gcs_prefix}runs/abc/output.json",
        "abc",
        f"{gcs_prefix}submissions/abc/solution.py",
    )
    assert result == "submissions/abc/solution.py"


def test_validate_artifact_uri_returns_none_and_uploads_error_on_bad_uri(
    gcs_bucket: gcs.Bucket,
) -> None:
    gcs_prefix = f"gs://{gcs_bucket.name}/"
    output_uri = f"{gcs_prefix}runs/bad-uri-test/output.json"

    result = _validate_artifact_uri(
        gcs_bucket,
        gcs_prefix,
        output_uri,
        "bad-uri-test",
        "s3://wrong-bucket/submissions/abc/solution.py",
    )

    assert result is None
    uploaded = json.loads(
        gcs_bucket.blob("runs/bad-uri-test/output.json").download_as_text()
    )
    assert uploaded["status"] == "system_error"
    assert "Bad artifact URI" in uploaded["stderr"]


# --- _download_request ---


def test_download_request_parses_json(gcs_bucket: gcs.Bucket) -> None:
    expected = {
        "submission_artifact_uri": f"gs://{gcs_bucket.name}/submissions/dl-test/solution.py",
        "output_uri": f"gs://{gcs_bucket.name}/runs/dl-test/output.json",
        "timeout_s": 30,
    }
    gcs_bucket.blob("runs/dl-test/runner_request.json").upload_from_string(
        json.dumps(expected), content_type="application/json"
    )

    result = _download_request(gcs_bucket, "dl-test")
    assert result == expected


# --- _download_submission_files ---


def test_download_submission_files_downloads_solution_and_test_cases(
    gcs_bucket: gcs.Bucket,
) -> None:
    gcs_bucket.blob("submissions/dl-files/solution.py").upload_from_string(
        "def add(a, b): return a + b"
    )
    gcs_bucket.blob("submissions/dl-files/test_cases.json").upload_from_string(
        json.dumps([{"input": [1, 2], "expected": 3}])
    )

    with tempfile.TemporaryDirectory() as work_dir:
        _download_submission_files(gcs_bucket, "submissions/dl-files", work_dir)

        with open(os.path.join(work_dir, "solution.py")) as f:
            assert "def add" in f.read()

        with open(os.path.join(work_dir, "test_cases.json")) as f:
            assert json.load(f) == [{"input": [1, 2], "expected": 3}]


def test_download_submission_files_creates_empty_test_cases_when_missing(
    gcs_bucket: gcs.Bucket,
) -> None:
    gcs_bucket.blob("submissions/no-tc/solution.py").upload_from_string(
        "def noop(): pass"
    )

    with tempfile.TemporaryDirectory() as work_dir:
        _download_submission_files(gcs_bucket, "submissions/no-tc", work_dir)

        with open(os.path.join(work_dir, "test_cases.json")) as f:
            assert json.load(f) == []


# --- _prepare_harness_input ---


def test_prepare_harness_input_with_wrapped_format() -> None:
    with tempfile.TemporaryDirectory() as work_dir:
        with open(os.path.join(work_dir, "test_cases.json"), "w") as f:
            json.dump(
                {
                    "function_signature": "def add(a, b):",
                    "test_cases": [{"input": [1, 2], "expected": 3}],
                },
                f,
            )

        input_file, output_file = _prepare_harness_input(work_dir)

        with open(input_file) as f:
            data = json.load(f)

        assert data["function_signature"] == "def add(a, b):"
        assert data["test_cases"] == [{"input": [1, 2], "expected": 3}]
        assert data["solution_path"] == os.path.join(work_dir, "solution.py")
        assert output_file == os.path.join(work_dir, "harness_output.json")


def test_prepare_harness_input_with_bare_list_format() -> None:
    with tempfile.TemporaryDirectory() as work_dir:
        with open(os.path.join(work_dir, "test_cases.json"), "w") as f:
            json.dump([{"input": [5], "expected": 25}], f)

        input_file, _ = _prepare_harness_input(work_dir)

        with open(input_file) as f:
            data = json.load(f)

        assert data["function_signature"] is None
        assert data["test_cases"] == [{"input": [5], "expected": 25}]


def test_prepare_harness_input_with_empty_list() -> None:
    with tempfile.TemporaryDirectory() as work_dir:
        with open(os.path.join(work_dir, "test_cases.json"), "w") as f:
            json.dump([], f)

        input_file, _ = _prepare_harness_input(work_dir)

        with open(input_file) as f:
            data = json.load(f)

        assert data["test_cases"] == []
        assert data["function_signature"] is None


# --- _run_harness ---


@patch("run.subprocess.run")
@patch("run.time.monotonic")
def test_run_harness_returns_ok_on_success(
    mock_time: MagicMock, mock_subprocess: MagicMock
) -> None:
    mock_time.side_effect = [0.0, 0.5]
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="output", stderr="")

    result = _run_harness("/tmp/input.json", "/tmp/output.json", timeout_s=30)

    assert result["status"] == "ok"
    assert result["stdout"] == "output"
    assert result["stderr"] == ""
    assert result["exit_code"] == 0
    assert result["duration_ms"] == 500


@patch("run.subprocess.run")
@patch("run.time.monotonic")
def test_run_harness_returns_runtime_error_on_nonzero_exit(
    mock_time: MagicMock, mock_subprocess: MagicMock
) -> None:
    mock_time.side_effect = [0.0, 1.0]
    mock_subprocess.return_value = MagicMock(
        returncode=1, stdout="", stderr="NameError: x"
    )

    result = _run_harness("/tmp/input.json", "/tmp/output.json", timeout_s=30)

    assert result["status"] == "runtime_error"
    assert result["exit_code"] == 1
    assert result["stderr"] == "NameError: x"
    assert result["duration_ms"] == 1000


@patch("run.subprocess.run")
@patch("run.time.monotonic")
def test_run_harness_returns_timeout_on_timeout(
    mock_time: MagicMock, mock_subprocess: MagicMock
) -> None:
    mock_time.side_effect = [0.0, 30.0]
    exc = subprocess.TimeoutExpired(cmd="python harness.py", timeout=30)
    exc.stdout = "partial"
    exc.stderr = "err"
    mock_subprocess.side_effect = exc

    result = _run_harness("/tmp/input.json", "/tmp/output.json", timeout_s=30)

    assert result["status"] == "timeout"
    assert result["exit_code"] == -1
    assert result["stdout"] == "partial"
    assert result["stderr"] == "err"
    assert result["duration_ms"] == 30000


@patch("run.subprocess.run")
@patch("run.time.monotonic")
def test_run_harness_handles_none_stdout_stderr_on_timeout(
    mock_time: MagicMock, mock_subprocess: MagicMock
) -> None:
    mock_time.side_effect = [0.0, 5.0]
    mock_subprocess.side_effect = subprocess.TimeoutExpired(
        cmd="python harness.py", timeout=5
    )

    result = _run_harness("/tmp/input.json", "/tmp/output.json", timeout_s=5)

    assert result["stdout"] == ""
    assert result["stderr"] == ""


# --- _upload_result ---


def test_upload_result_uploads_runner_output(gcs_bucket: gcs.Bucket) -> None:
    gcs_prefix = f"gs://{gcs_bucket.name}/"
    output_uri = f"{gcs_prefix}runs/upload-test/runner_output.json"

    _upload_result(
        gcs_bucket,
        gcs_prefix,
        output_uri,
        "upload-test",
        {
            "status": "ok",
            "stdout": "hello",
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 500,
        },
    )

    uploaded = json.loads(
        gcs_bucket.blob("runs/upload-test/runner_output.json").download_as_text()
    )
    assert uploaded["schema_version"] == "runner_output.v1"
    assert uploaded["run_uuid"] == "upload-test"
    assert uploaded["status"] == "ok"
    assert uploaded["stdout"] == "hello"
    assert uploaded["exit_code"] == 0
    assert uploaded["duration_ms"] == 500


def test_upload_result_decodes_bytes_stdout_stderr(
    gcs_bucket: gcs.Bucket,
) -> None:
    gcs_prefix = f"gs://{gcs_bucket.name}/"
    output_uri = f"{gcs_prefix}runs/bytes-test/output.json"

    _upload_result(
        gcs_bucket,
        gcs_prefix,
        output_uri,
        "bytes-test",
        {
            "status": "ok",
            "stdout": b"binary output",
            "stderr": b"binary error",
            "exit_code": 0,
            "duration_ms": 100,
        },
    )

    uploaded = json.loads(
        gcs_bucket.blob("runs/bytes-test/output.json").download_as_text()
    )
    assert uploaded["stdout"] == "binary output"
    assert uploaded["stderr"] == "binary error"


# --- _upload_error ---


def test_upload_error_uploads_system_error(gcs_bucket: gcs.Bucket) -> None:
    gcs_prefix = f"gs://{gcs_bucket.name}/"
    output_uri = f"{gcs_prefix}runs/err-test/output.json"

    _upload_error(
        gcs_bucket,
        gcs_prefix,
        output_uri,
        "err-test",
        "Something went wrong",
    )

    uploaded = json.loads(
        gcs_bucket.blob("runs/err-test/output.json").download_as_text()
    )
    assert uploaded["schema_version"] == "runner_output.v1"
    assert uploaded["status"] == "system_error"
    assert uploaded["stderr"] == "Something went wrong"
    assert uploaded["exit_code"] == -1
    assert uploaded["duration_ms"] == 0
