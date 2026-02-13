"""Unit tests for GcpTaskRunAdapter."""

from unittest.mock import MagicMock, patch

from google.cloud import run_v2

from app.adapters.task_run import GcpTaskRunAdapter
from app.worker.contracts import ExecutionStatus, RunnerRequest


def _make_runner_request() -> RunnerRequest:
    return RunnerRequest(
        run_uuid="abc-123",
        submission_id=1,
        problem_id=1,
        submission_artifact_uri="gs://bucket/submissions/abc/solution.py",
        output_uri="gs://bucket/runs/abc-123/runner_output.json",
        timeout_s=30,
    )


def _make_execution(succeeded: bool) -> MagicMock:
    execution = MagicMock(spec=run_v2.Execution)
    execution.name = "projects/p/locations/us-central1/jobs/runner/executions/exec-1"

    condition = MagicMock(spec=run_v2.Condition)
    condition.type_ = "Completed"
    if succeeded:
        condition.state = run_v2.Condition.State.CONDITION_SUCCEEDED
        condition.message = ""
    else:
        condition.state = run_v2.Condition.State.CONDITION_FAILED
        condition.message = "Container exited with code 1"

    execution.conditions = [condition]
    return execution


@patch("app.adapters.task_run.run_v2.ExecutionsClient")
def test_gcp_task_run_adapter_execute_succeeded(mock_client_cls: MagicMock) -> None:
    mock_client = mock_client_cls.return_value
    execution = _make_execution(succeeded=True)
    mock_operation = MagicMock()
    mock_operation.result.return_value = execution
    mock_client.run_job.return_value = mock_operation

    adapter = GcpTaskRunAdapter(
        project="my-project", location="us-central1", job_name="codette-runner"
    )
    request = _make_runner_request()
    outcome = adapter.execute(request)

    assert outcome["status"] == ExecutionStatus.SUCCEEDED
    assert outcome["execution_ref"] == execution.name
    assert outcome["error"] is None

    # Verify the job was called with correct env override
    call_args = mock_client.run_job.call_args
    run_job_req = call_args.kwargs["request"]
    env_vars = run_job_req.overrides.container_overrides[0].env
    assert len(env_vars) == 1
    assert env_vars[0].name == "RUN_UUID"
    assert env_vars[0].value == "abc-123"


@patch("app.adapters.task_run.run_v2.ExecutionsClient")
def test_gcp_task_run_adapter_execute_failed(mock_client_cls: MagicMock) -> None:
    mock_client = mock_client_cls.return_value
    execution = _make_execution(succeeded=False)
    mock_operation = MagicMock()
    mock_operation.result.return_value = execution
    mock_client.run_job.return_value = mock_operation

    adapter = GcpTaskRunAdapter(
        project="my-project", location="us-central1", job_name="codette-runner"
    )
    request = _make_runner_request()
    outcome = adapter.execute(request)

    assert outcome["status"] == ExecutionStatus.FAILED
    assert outcome["execution_ref"] == execution.name
    assert outcome["error"] is not None
    assert "Container exited with code 1" in outcome["error"]
