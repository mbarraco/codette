"""Integration tests for the grader orchestrator (run.py)."""

import json
from unittest.mock import MagicMock, patch

import pytest
from google.cloud import storage as gcs
from grader.run import (
    _download_request,
    _download_runner_output,
    _evaluate,
    _upload_error,
    _upload_result,
    _validate,
    main,
)
from grader.schemas import GraderRequest, RunnerOutput
from pydantic import ValidationError

from errors import JobErrorCode


# --- _validate ---


def test_validate_returns_run_uuid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["run.py", "abc-123"])
    assert _validate() == "abc-123"


def test_validate_exits_when_no_args(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["run.py"])
    with pytest.raises(SystemExit) as exc_info:
        _validate()
    assert exc_info.value.code == 1


# --- _download_request ---


def test_download_request_parses_json(gcs_bucket: gcs.Bucket) -> None:
    expected = {
        "runner_output_uri": f"gs://{gcs_bucket.name}/runs/dl-test/runner_output.json",
        "output_uri": f"gs://{gcs_bucket.name}/runs/dl-test/grader_output.json",
    }
    gcs_bucket.blob("runs/dl-test/grader_request.json").upload_from_string(
        json.dumps(expected), content_type="application/json"
    )

    result = _download_request(gcs_bucket, "dl-test")
    assert result.runner_output_uri == expected["runner_output_uri"]
    assert result.output_uri == expected["output_uri"]


def test_download_request_rejects_missing_fields(gcs_bucket: gcs.Bucket) -> None:
    gcs_bucket.blob("runs/bad-req/grader_request.json").upload_from_string(
        json.dumps({"runner_output_uri": "gs://bucket/path"}),
        content_type="application/json",
    )

    with pytest.raises(ValidationError):
        _download_request(gcs_bucket, "bad-req")


# --- _download_runner_output ---


def test_download_runner_output_parses_json(gcs_bucket: gcs.Bucket) -> None:
    runner_output = {
        "schema_version": "runner_output.v1",
        "run_uuid": "ro-test",
        "status": "ok",
        "stdout": '{"results": [{"passed": true}]}',
        "stderr": "",
        "exit_code": 0,
        "duration_ms": 100,
    }
    gcs_bucket.blob("runs/ro-test/runner_output.json").upload_from_string(
        json.dumps(runner_output), content_type="application/json"
    )

    gcs_prefix = f"gs://{gcs_bucket.name}/"
    result = _download_runner_output(
        gcs_bucket, gcs_prefix, f"{gcs_prefix}runs/ro-test/runner_output.json"
    )
    assert result.status == "ok"
    assert result.stdout == '{"results": [{"passed": true}]}'


# --- _evaluate ---


def test_evaluate_pass_all_tests() -> None:
    stdout = json.dumps({"results": [{"passed": True}, {"passed": True}]})
    ro = RunnerOutput(status="ok", stdout=stdout)
    verdict, summary = _evaluate(ro)
    assert verdict == "pass"
    assert summary == "2/2 tests passed"


def test_evaluate_fail_some_tests() -> None:
    stdout = json.dumps({"results": [{"passed": True}, {"passed": False}]})
    ro = RunnerOutput(status="ok", stdout=stdout)
    verdict, summary = _evaluate(ro)
    assert verdict == "fail"
    assert summary == "1/2 tests passed"


def test_evaluate_no_tests() -> None:
    stdout = json.dumps({"results": []})
    ro = RunnerOutput(status="ok", stdout=stdout)
    verdict, summary = _evaluate(ro)
    assert verdict == "fail"
    assert summary == "No test cases found"


def test_evaluate_unparseable_stdout() -> None:
    ro = RunnerOutput(status="ok", stdout="not json at all")
    verdict, summary = _evaluate(ro)
    assert verdict == "fail"
    assert summary == "Failed to parse runner output"


def test_evaluate_non_ok_runner_status() -> None:
    ro = RunnerOutput(status="timeout", stdout="")
    verdict, summary = _evaluate(ro)
    assert verdict == "fail"
    assert summary == "Runner failed: timeout"


def test_evaluate_non_ok_runner_status_with_structured_error() -> None:
    ro = RunnerOutput(
        status="system_error",
        stdout="",
        error={
            "code": JobErrorCode.FILE_NOT_FOUND,
            "message": "Missing required submission file: submissions/x/test_cases.json",
        },
    )
    verdict, summary = _evaluate(ro)
    assert verdict == "fail"
    assert "Runner failed (file_not_found): Missing required submission file" in summary


# --- _upload_result ---


def test_upload_result_uploads_grader_output(gcs_bucket: gcs.Bucket) -> None:
    gcs_prefix = f"gs://{gcs_bucket.name}/"
    output_uri = f"{gcs_prefix}runs/upload-test/grader_output.json"

    _upload_result(
        gcs_bucket,
        gcs_prefix,
        output_uri,
        "upload-test",
        "pass",
        "3/3 tests passed",
    )

    uploaded = json.loads(
        gcs_bucket.blob("runs/upload-test/grader_output.json").download_as_text()
    )
    assert uploaded["schema_version"] == "grader_output.v1"
    assert uploaded["run_uuid"] == "upload-test"
    assert uploaded["verdict"] == "pass"
    assert uploaded["summary"] == "3/3 tests passed"
    assert uploaded["metadata"] is None
    assert uploaded["error"] is None


# --- _upload_error ---


def test_upload_error_uploads_system_error(gcs_bucket: gcs.Bucket) -> None:
    gcs_prefix = f"gs://{gcs_bucket.name}/"
    output_uri = f"{gcs_prefix}runs/err-test/grader_output.json"

    _upload_error(
        gcs_bucket,
        gcs_prefix,
        output_uri,
        "err-test",
        "Something went wrong",
        error_code=JobErrorCode.INTERNAL_ERROR,
    )

    uploaded = json.loads(
        gcs_bucket.blob("runs/err-test/grader_output.json").download_as_text()
    )
    assert uploaded["schema_version"] == "grader_output.v1"
    assert uploaded["verdict"] == "system_error"
    assert uploaded["summary"] == "Something went wrong"
    assert uploaded["error"]["code"] == JobErrorCode.INTERNAL_ERROR
    assert uploaded["error"]["message"] == "Something went wrong"


# --- main error handling ---


@patch("grader.run._upload_error")
@patch("grader.run._download_runner_output")
@patch("grader.run._download_request")
@patch("grader.run._get_bucket")
@patch("grader.run._validate")
def test_main_exits_on_validation_error(
    mock_validate: MagicMock,
    mock_get_bucket: MagicMock,
    mock_download_request: MagicMock,
    mock_download_runner_output: MagicMock,
    mock_upload_error: MagicMock,
) -> None:
    mock_validate.return_value = "run-val-err"
    bucket = MagicMock()
    bucket.name = "codette-test"
    mock_get_bucket.return_value = bucket
    mock_download_request.return_value = GraderRequest(
        runner_output_uri="gs://codette-test/runs/run-val-err/runner_output.json",
        output_uri="gs://codette-test/runs/run-val-err/grader_output.json",
    )
    mock_download_runner_output.side_effect = ValidationError.from_exception_data(
        title="RunnerOutput",
        line_errors=[
            {
                "type": "missing",
                "loc": ("status",),
                "msg": "Field required",
                "input": {},
            }
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    kwargs = mock_upload_error.call_args.kwargs
    assert kwargs["error_code"] == JobErrorCode.VALIDATION_ERROR


@patch("grader.run._upload_error")
@patch("grader.run._download_runner_output")
@patch("grader.run._download_request")
@patch("grader.run._get_bucket")
@patch("grader.run._validate")
def test_main_uploads_error_on_unhandled_exception(
    mock_validate: MagicMock,
    mock_get_bucket: MagicMock,
    mock_download_request: MagicMock,
    mock_download_runner_output: MagicMock,
    mock_upload_error: MagicMock,
) -> None:
    mock_validate.return_value = "run-unhandled"
    bucket = MagicMock()
    bucket.name = "codette-test"
    mock_get_bucket.return_value = bucket
    mock_download_request.return_value = GraderRequest(
        runner_output_uri="gs://codette-test/runs/run-unhandled/runner_output.json",
        output_uri="gs://codette-test/runs/run-unhandled/grader_output.json",
    )
    mock_download_runner_output.side_effect = RuntimeError("connection reset")

    with pytest.raises(RuntimeError, match="connection reset"):
        main()
    kwargs = mock_upload_error.call_args.kwargs
    assert kwargs["error_code"] == JobErrorCode.INTERNAL_ERROR
    assert kwargs["details"]["exception_type"] == "RuntimeError"
