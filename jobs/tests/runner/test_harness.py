"""Unit tests for harness.execute() — pure logic, no subprocess."""

import tempfile

from runner.harness import execute
from runner.schemas import HarnessInput, TestCase


def _write_solution(code: str) -> str:
    """Write solution code to a temp file and return the path."""
    f = tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False)
    f.write(code)
    f.close()
    return f.name


def _make_input(
    solution_code: str,
    test_cases: list[TestCase],
    function_signature: str | None = None,
) -> HarnessInput:
    return HarnessInput(
        solution_path=_write_solution(solution_code),
        test_cases=test_cases,
        function_signature=function_signature,
    )


# --- correct submission ---


def test_execute_correct_submission_passes_all() -> None:
    harness_input = _make_input(
        solution_code="def sum(a, b): return a + b",
        test_cases=[
            TestCase(input=[1, 2], expected=3),
            TestCase(input=[0, 0], expected=0),
            TestCase(input=[-1, 1], expected=0),
        ],
        function_signature="def sum(a, b):",
    )

    output = execute(harness_input)

    assert output.error is None
    assert len(output.results) == 3
    assert all(r.passed for r in output.results)
    assert output.results[0].actual == 3
    assert output.results[1].actual == 0
    assert output.results[2].actual == 0


# --- wrong submission ---


def test_execute_wrong_submission_fails_cases() -> None:
    harness_input = _make_input(
        solution_code="def sum(a, b): return a * b",
        test_cases=[
            TestCase(input=[2, 3], expected=5),
            TestCase(input=[0, 5], expected=5),
        ],
        function_signature="def sum(a, b):",
    )

    output = execute(harness_input)

    assert output.error is None
    assert len(output.results) == 2
    assert not output.results[0].passed
    assert output.results[0].actual == 6
    assert output.results[0].expected == 5
    assert not output.results[1].passed
    assert output.results[1].actual == 0
    assert output.results[1].expected == 5


# --- partially correct ---


def test_execute_partially_correct_submission() -> None:
    harness_input = _make_input(
        solution_code="def sum(a, b): return a + b",
        test_cases=[
            TestCase(input=[1, 2], expected=3),
            TestCase(input=[1, 2], expected=999),
        ],
        function_signature="def sum(a, b):",
    )

    output = execute(harness_input)

    assert output.error is None
    assert output.results[0].passed
    assert not output.results[1].passed


# --- runtime error in submission ---


def test_execute_submission_raises_exception() -> None:
    harness_input = _make_input(
        solution_code="def sum(a, b): raise ValueError('boom')",
        test_cases=[TestCase(input=[1, 2], expected=3)],
        function_signature="def sum(a, b):",
    )

    output = execute(harness_input)

    assert output.error is None
    assert len(output.results) == 1
    assert not output.results[0].passed
    assert "ValueError: boom" in output.results[0].error


# --- wrong function name ---


def test_execute_wrong_function_name_returns_signature_error() -> None:
    harness_input = _make_input(
        solution_code="def add(a, b): return a + b",
        test_cases=[TestCase(input=[1, 2], expected=3)],
        function_signature="def sum(a, b):",
    )

    output = execute(harness_input)

    assert output.results == []
    assert "Expected function 'sum'" in output.error
    assert "'add'" in output.error


# --- wrong parameter count ---


def test_execute_wrong_param_count_returns_signature_error() -> None:
    harness_input = _make_input(
        solution_code="def sum(a): return a",
        test_cases=[TestCase(input=[1, 2], expected=3)],
        function_signature="def sum(a, b):",
    )

    output = execute(harness_input)

    assert output.results == []
    assert "2 parameter(s)" in output.error
    assert "found 1" in output.error


# --- captures stdout ---


def test_execute_captures_stdout_from_solution() -> None:
    harness_input = _make_input(
        solution_code='def sum(a, b):\n    print("debug")\n    return a + b',
        test_cases=[TestCase(input=[1, 2], expected=3)],
        function_signature="def sum(a, b):",
    )

    output = execute(harness_input)

    assert output.results[0].passed
    assert output.results[0].stdout == "debug\n"


# --- bad solution file ---


def test_execute_missing_solution_returns_error() -> None:
    harness_input = HarnessInput(
        solution_path="/nonexistent/solution.py",
        test_cases=[TestCase(input=[1, 2], expected=3)],
        function_signature="def sum(a, b):",
    )

    output = execute(harness_input)

    assert output.results == []
    assert output.error is not None
