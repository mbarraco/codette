"""Grader — reads runner output from GCS, evaluates results, writes verdict.

CLI arguments:
    RUN_UUID        — unique identifier for this execution (sys.argv[1])

Environment variables:
    STORAGE_BUCKET  — GCS bucket name (set at deploy time)
"""

import json
import os
import sys

from google.cloud import storage


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: grade.py <RUN_UUID>", file=sys.stderr)
        sys.exit(1)

    run_uuid = sys.argv[1]
    bucket_name = os.environ["STORAGE_BUCKET"]

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # 1. Download grader_request.json
    request_path = f"runs/{run_uuid}/grader_request.json"
    request_blob = bucket.blob(request_path)
    request_data = json.loads(request_blob.download_as_text())

    runner_output_uri: str = request_data["runner_output_uri"]
    output_uri: str = request_data["output_uri"]

    prefix = f"gs://{bucket_name}/"

    # 2. Download runner output
    runner_output_path = runner_output_uri[len(prefix) :]
    runner_output = json.loads(bucket.blob(runner_output_path).download_as_text())

    # 3. Evaluate
    runner_status = runner_output.get("status", "system_error")
    verdict = "fail"
    summary = ""

    if runner_status != "ok":
        summary = f"Runner failed: {runner_status}"
    else:
        # Parse harness results from stdout
        stdout = runner_output.get("stdout", "")
        try:
            harness_result = json.loads(stdout)
            results = harness_result.get("results", [])
            total = len(results)
            passed = sum(1 for r in results if r.get("passed"))

            if total > 0 and passed == total:
                verdict = "pass"
                summary = f"{passed}/{total} tests passed"
            elif total == 0:
                summary = "No test cases found"
            else:
                summary = f"{passed}/{total} tests passed"
        except (json.JSONDecodeError, TypeError):
            summary = "Failed to parse runner output"

    # 4. Build and upload grader output
    grader_output = {
        "schema_version": "grader_output.v1",
        "run_uuid": run_uuid,
        "verdict": verdict,
        "summary": summary,
        "metadata": None,
    }

    output_path = output_uri[len(prefix) :]
    bucket.blob(output_path).upload_from_string(
        json.dumps(grader_output), content_type="application/json"
    )

    print(f"Grader completed: verdict={verdict} summary={summary}")


if __name__ == "__main__":
    main()
