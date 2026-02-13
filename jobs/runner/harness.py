"""Harness — executes submitted code in isolation.

Usage: python harness.py <input_json> <output_json>

Input JSON format:
    {
        "solution_path": "/tmp/work/solution.py",
        "test_cases": [
            {"input": [1, 2], "expected": 3},
            ...
        ]
    }

Output JSON format:
    {
        "results": [
            {
                "input": [1, 2],
                "expected": 3,
                "actual": 3,
                "stdout": "",
                "error": null,
                "passed": true
            },
            ...
        ]
    }
"""

import importlib.util
import io
import json
import sys
import traceback


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


def main() -> None:
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path) as f:
        config = json.load(f)

    solution_path = config["solution_path"]
    test_cases = config["test_cases"]

    # Load solution module once
    module = _load_solution(solution_path)
    func = _find_callable(module)

    results = []
    for tc in test_cases:
        inputs = tc.get("input", [])
        expected = tc.get("expected")

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
            {
                "input": inputs,
                "expected": expected,
                "actual": _serialize(actual),
                "stdout": captured_stdout.getvalue(),
                "error": error,
                "passed": passed,
            }
        )

    with open(output_path, "w") as f:
        json.dump({"results": results}, f)


def _serialize(value):
    """Best-effort JSON-serializable conversion."""
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)


if __name__ == "__main__":
    main()
