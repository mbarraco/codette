"""Harness — executes submitted code in isolation.

Usage: python -m runner.harness <input_json>

Reads a HarnessInput JSON file, runs the solution against test cases,
and prints HarnessOutput JSON to stdout.
"""

import importlib.util
import inspect
import io
import json
import re
import sys
import traceback

from .schemas import HarnessInput, HarnessOutput, HarnessTestCaseResult


def _load_solution(solution_path: str):
    """Dynamically import solution.py and return the module."""
    spec = importlib.util.spec_from_file_location("solution", solution_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {solution_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _find_callable(module):
    """Find the first user-defined callable function in the module."""
    for name in dir(module):
        if name.startswith("_"):
            continue
        obj = getattr(module, name)
        if callable(obj) and hasattr(obj, "__code__"):
            return obj
    raise RuntimeError("No callable function found in solution module")


def _parse_signature(sig: str) -> tuple[str, list[str]]:
    """Parse a function signature like 'def add(a, b):' into (name, param_names)."""
    match = re.match(r"def\s+(\w+)\s*\(([^)]*)\)\s*:", sig.strip())
    if not match:
        raise ValueError(f"Cannot parse function signature: {sig}")
    name = match.group(1)
    params_str = match.group(2).strip()
    params = (
        [p.strip() for p in params_str.split(",") if p.strip()] if params_str else []
    )
    return name, params


def _validate_signature(
    func, expected_name: str, expected_params: list[str]
) -> str | None:
    """Validate that func matches the expected name and parameter count. Returns error or None."""
    if func.__name__ != expected_name:
        return (
            f"Expected function '{expected_name}' but found '{func.__name__}'. "
            f"Please define a function named '{expected_name}'."
        )
    actual_params = list(inspect.signature(func).parameters.keys())
    if len(actual_params) != len(expected_params):
        return (
            f"Function '{expected_name}' expects {len(expected_params)} parameter(s) "
            f"({', '.join(expected_params)}) but found {len(actual_params)} "
            f"({', '.join(actual_params)})."
        )
    return None


def _serialize(value):
    """Best-effort JSON-serializable conversion."""
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)


def execute(harness_input: HarnessInput) -> HarnessOutput:
    """Pure logic: load solution, validate signature, run test cases."""
    try:
        module = _load_solution(harness_input.solution_path)
        func = _find_callable(module)
    except Exception as exc:
        return HarnessOutput(error=str(exc))

    if harness_input.function_signature:
        try:
            expected_name, expected_params = _parse_signature(
                harness_input.function_signature
            )
        except ValueError as e:
            return HarnessOutput(error=str(e))

        sig_error = _validate_signature(func, expected_name, expected_params)
        if sig_error:
            return HarnessOutput(error=sig_error)

    results: list[HarnessTestCaseResult] = []
    for tc in harness_input.test_cases:
        inputs = tc.input
        expected = tc.expected

        captured_stdout = io.StringIO()
        old_stdout = sys.stdout
        error = None
        actual = None

        try:
            sys.stdout = captured_stdout
            actual = func(*inputs)
        except Exception:
            error = traceback.format_exc()
        finally:
            sys.stdout = old_stdout

        passed = error is None and actual == expected

        results.append(
            HarnessTestCaseResult(
                input=inputs,
                expected=expected,
                actual=_serialize(actual),
                stdout=captured_stdout.getvalue(),
                error=error,
                passed=passed,
            )
        )

    return HarnessOutput(results=results)


def main() -> None:
    from pathlib import Path

    harness_input = HarnessInput.model_validate_json(Path(sys.argv[1]).read_bytes())
    print(execute(harness_input).model_dump_json())


if __name__ == "__main__":
    main()
