from types import SimpleNamespace
from uuid import uuid4

from app.worker.request_factory import ExecutionRequestFactory


def test_builds_runner_and_grader_requests_with_single_source_of_truth() -> None:
    run_uuid = uuid4()
    run = SimpleNamespace(uuid=run_uuid)
    submission = SimpleNamespace(
        id=10,
        problem_id=20,
        artifact_uri="gs://codette-test/submissions/10/solution.py",
    )

    factory = ExecutionRequestFactory(
        storage_bucket="codette-test",
        runner_timeout_s=45,
        grader_timeout_s=60,
    )

    runner_request = factory.build_runner_request(run=run, submission=submission)
    grader_request = factory.build_grader_request(
        run=run,
        submission=submission,
        runner_output_uri=runner_request["output_uri"],
    )

    run_uuid_str = str(run_uuid)

    assert runner_request["run_uuid"] == run_uuid_str
    assert grader_request["run_uuid"] == run_uuid_str
    assert (
        runner_request["output_uri"]
        == f"gs://codette-test/runs/{run_uuid_str}/runner_output.json"
    )
    assert (
        grader_request["output_uri"]
        == f"gs://codette-test/runs/{run_uuid_str}/grader_output.json"
    )
    assert runner_request["timeout_s"] == 45
    assert grader_request["timeout_s"] == 60
