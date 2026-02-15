"""Grader — reads runner output from GCS, evaluates results, writes verdict.

CLI arguments:
    RUN_UUID        — unique identifier for this execution (sys.argv[1])

Environment variables:
    STORAGE_BUCKET  — GCS bucket name (set at deploy time)
"""

import sys
from os import environ
from typing import Any

from errors import JobErrorCode
from google.cloud import storage
from pydantic import ValidationError
from .schemas import GraderOutput, GraderRequest, HarnessResult, RunnerOutput


def main() -> None:
    run_uuid = _validate()
    bucket = _get_bucket()
    gcs_prefix = f"gs://{bucket.name}/"

    output_uri: str | None = None
    try:
        request_data = _download_request(bucket, run_uuid)
        output_uri = request_data.output_uri

        runner_output = _download_runner_output(
            bucket, gcs_prefix, request_data.runner_output_uri
        )

        verdict, summary = _evaluate(runner_output)

        _upload_result(bucket, gcs_prefix, output_uri, run_uuid, verdict, summary)

        print(f"Grader completed: verdict={verdict} summary={summary}")
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
            f"Unhandled grader error: {exc}",
            error_code=JobErrorCode.INTERNAL_ERROR,
            details={"exception_type": type(exc).__name__},
        )
        raise


def _validate() -> str:
    if len(sys.argv) < 2:
        print("Usage: run.py <RUN_UUID>", file=sys.stderr)
        sys.exit(1)
    return sys.argv[1]


def _get_bucket() -> storage.Bucket:
    bucket_name = environ["STORAGE_BUCKET"]
    client = storage.Client()
    return client.bucket(bucket_name)


def _download_request(bucket: storage.Bucket, run_uuid: str) -> GraderRequest:
    """Download and parse the grader_request.json from GCS."""
    blob = bucket.blob(f"runs/{run_uuid}/grader_request.json")
    return GraderRequest.model_validate_json(blob.download_as_text())


def _download_runner_output(
    bucket: storage.Bucket, gcs_prefix: str, runner_output_uri: str
) -> RunnerOutput:
    """Download and parse the runner output JSON from GCS."""
    runner_output_path = runner_output_uri[len(gcs_prefix) :]
    raw = bucket.blob(runner_output_path).download_as_text()
    return RunnerOutput.model_validate_json(raw)


def _evaluate(runner_output: RunnerOutput) -> tuple[str, str]:
    """Evaluate the runner output and return (verdict, summary)."""
    if runner_output.status != "ok":
        if runner_output.error is not None:
            return (
                "fail",
                f"Runner failed ({runner_output.error.code}): {runner_output.error.message}",
            )
        return "fail", f"Runner failed: {runner_output.status}"

    try:
        harness = HarnessResult.model_validate_json(runner_output.stdout)
    except ValidationError:
        return "fail", "Failed to parse runner output"

    total = len(harness.results)
    passed = sum(1 for r in harness.results if r.passed)

    if total == 0:
        return "fail", "No test cases found"

    if passed == total:
        return "pass", f"{passed}/{total} tests passed"

    return "fail", f"{passed}/{total} tests passed"


def _upload_result(
    bucket: storage.Bucket,
    gcs_prefix: str,
    output_uri: str,
    run_uuid: str,
    verdict: str,
    summary: str,
) -> None:
    """Build GraderOutput and upload to the output URI."""
    grader_output = GraderOutput(
        run_uuid=run_uuid,
        verdict=verdict,
        summary=summary,
    )

    output_path = output_uri[len(gcs_prefix) :]
    bucket.blob(output_path).upload_from_string(
        grader_output.model_dump_json(), content_type="application/json"
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
    """Upload a system_error GraderOutput."""
    if output_uri is None:
        print(
            f"Grader failed before output_uri was available: {error}", file=sys.stderr
        )
        return

    grader_output = GraderOutput(
        run_uuid=run_uuid,
        verdict="system_error",
        summary=error,
        error={"code": error_code, "message": error, "details": details},
    )
    output_path = output_uri[len(gcs_prefix) :]
    bucket.blob(output_path).upload_from_string(
        grader_output.model_dump_json(), content_type="application/json"
    )
    print(f"Grader failed: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
