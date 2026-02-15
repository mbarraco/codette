"""Unit tests for GCP and Local runner/grader adapters."""

from unittest.mock import MagicMock, Mock, patch

from google.cloud import run_v2

from app.adapters.local_task_run import LocalGraderAdapter, LocalRunnerAdapter
from app.adapters.task_run import GcpGraderAdapter, GcpRunnerAdapter
from app.worker.contracts import ExecutionStatus, GraderRequest, RunnerRequest


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


def _make_grader_request() -> GraderRequest:
    return GraderRequest(
        run_uuid="abc-123",
        submission_id=1,
        problem_id=1,
        runner_output_uri="gs://bucket/runs/abc-123/runner_output.json",
        output_uri="gs://bucket/runs/abc-123/grader_output.json",
        timeout_s=30,
    )


# --- GCP adapter tests ---


@patch("app.adapters.task_run.run_v2.ExecutionsClient")
def test_gcp_runner_adapter_execute_post_returns_succeeded(
    mock_client_cls: MagicMock,
) -> None:
    mock_client = mock_client_cls.return_value
    execution = _make_execution(succeeded=True)
    mock_operation = MagicMock()
    mock_operation.result.return_value = execution
    mock_client.run_job.return_value = mock_operation

    adapter = GcpRunnerAdapter(
        project="my-project", location="us-central1", job_name="codette-runner"
    )
    outcome = adapter.execute(_make_runner_request())

    assert outcome["status"] == ExecutionStatus.SUCCEEDED
    assert outcome["execution_ref"] == execution.name
    assert outcome["error"] is None

    call_args = mock_client.run_job.call_args
    run_job_req = call_args.kwargs["request"]
    args = run_job_req.overrides.container_overrides[0].args
    assert args == ["abc-123"]


@patch("app.adapters.task_run.run_v2.ExecutionsClient")
def test_gcp_grader_adapter_execute_post_returns_failed(
    mock_client_cls: MagicMock,
) -> None:
    mock_client = mock_client_cls.return_value
    execution = _make_execution(succeeded=False)
    mock_operation = MagicMock()
    mock_operation.result.return_value = execution
    mock_client.run_job.return_value = mock_operation

    adapter = GcpGraderAdapter(
        project="my-project", location="us-central1", job_name="codette-grader"
    )
    outcome = adapter.execute(_make_grader_request())

    assert outcome["status"] == ExecutionStatus.FAILED
    assert outcome["execution_ref"] == execution.name
    assert outcome["error"] is not None
    assert "Container exited with code 1" in outcome["error"]


# --- Local adapter tests ---


def test_local_runner_adapter_execute_post_returns_succeeded() -> None:
    mock_client = Mock()
    mock_container = Mock()
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.short_id = "runner123"
    mock_client.containers.run.return_value = mock_container

    adapter = LocalRunnerAdapter(
        image_name="codette-runner",
        network="codette_default",
        storage_bucket="codette",
        storage_emulator_host="http://gcs:4443",
        docker_client=mock_client,
    )

    outcome = adapter.execute(_make_runner_request())

    assert outcome["status"] == ExecutionStatus.SUCCEEDED
    assert outcome["execution_ref"] == "local:runner123"
    assert outcome["error"] is None
    call_kwargs = mock_client.containers.run.call_args.kwargs
    assert call_kwargs["entrypoint"] == ["python", "run.py"]
    assert call_kwargs["command"] == ["abc-123"]
    assert call_kwargs["name"] == "codette-runner-abc-123"
    mock_container.remove.assert_called_once_with(force=True)


def test_local_grader_adapter_execute_post_returns_succeeded() -> None:
    mock_client = Mock()
    mock_container = Mock()
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.short_id = "grader123"
    mock_client.containers.run.return_value = mock_container

    adapter = LocalGraderAdapter(
        image_name="codette-grader",
        network="codette_default",
        storage_bucket="codette",
        storage_emulator_host="http://gcs:4443",
        docker_client=mock_client,
    )

    outcome = adapter.execute(_make_grader_request())

    assert outcome["status"] == ExecutionStatus.SUCCEEDED
    assert outcome["execution_ref"] == "local:grader123"
    assert outcome["error"] is None
    call_kwargs = mock_client.containers.run.call_args.kwargs
    assert call_kwargs["entrypoint"] == ["python", "grade.py"]
    assert call_kwargs["command"] == ["abc-123"]
    assert call_kwargs["name"] == "codette-grader-abc-123"
    mock_container.remove.assert_called_once_with(force=True)


def test_local_runner_adapter_execute_post_returns_failed_when_launch_errors() -> None:
    mock_client = Mock()
    mock_client.containers.run.side_effect = RuntimeError("boom")

    adapter = LocalRunnerAdapter(
        image_name="codette-runner",
        network="codette_default",
        storage_bucket="codette",
        storage_emulator_host="http://gcs:4443",
        docker_client=mock_client,
    )

    outcome = adapter.execute(_make_runner_request())

    assert outcome["status"] == ExecutionStatus.FAILED
    assert outcome["execution_ref"] == "local:codette-runner"
    assert outcome["error"] == "Container launch failed: boom"
