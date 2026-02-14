#!/usr/bin/env python3
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.adapters.db import SessionLocal
from app.models import Problem


@dataclass(frozen=True)
class ProblemSeed:
    uuid: uuid.UUID
    title: str
    statement: str
    hints: str | None
    examples: str | None
    test_cases: list[dict] | None
    function_signature: str


SEED_PROBLEMS: tuple[ProblemSeed, ...] = (
    ProblemSeed(
        uuid=uuid.UUID("3f5d9e88-95e0-4f30-a3e0-2e0f2fbf5bd3"),
        title="Two Sum",
        statement=(
            "Given two integers, return their sum as an integer. "
            "Assume inputs are always valid numbers."
        ),
        hints="You only need the + operator and to return the result.",
        examples="add(2, 3) == 5\nadd(-1, 4) == 3",
        test_cases=[
            {"input": [2, 3], "output": 5},
            {"input": [-1, 4], "output": 3},
            {"input": [0, 0], "output": 0},
        ],
        function_signature="def add(a, b):",
    ),
    ProblemSeed(
        uuid=uuid.UUID("0ecf2d34-5f0c-45ce-a83a-bf1063f4042a"),
        title="FizzBuzz",
        statement=(
            "Return a list of strings from 1 to n. "
            "Use Fizz for multiples of 3, Buzz for multiples of 5, "
            "and FizzBuzz for multiples of both."
        ),
        hints="Check divisibility by 15 before 3 or 5.",
        examples='fizz_buzz(5) == ["1", "2", "Fizz", "4", "Buzz"]',
        test_cases=[
            {"input": [3], "output": ["1", "2", "Fizz"]},
            {"input": [5], "output": ["1", "2", "Fizz", "4", "Buzz"]},
            {
                "input": [15],
                "output": [
                    "1",
                    "2",
                    "Fizz",
                    "4",
                    "Buzz",
                    "Fizz",
                    "7",
                    "8",
                    "Fizz",
                    "Buzz",
                    "11",
                    "Fizz",
                    "13",
                    "14",
                    "FizzBuzz",
                ],
            },
        ],
        function_signature="def fizzbuzz(n):",
    ),
    ProblemSeed(
        uuid=uuid.UUID("8a57bcd1-0709-4b95-8db3-02f2ec2cf278"),
        title="Palindrome Number",
        statement=(
            "Given an integer x, return true if x reads the same forward and backward. "
            "Negative numbers are not palindromes."
        ),
        hints="Convert to string and compare with its reverse.",
        examples="is_palindrome(121) == True\nis_palindrome(-121) == False",
        test_cases=[
            {"input": [121], "output": True},
            {"input": [-121], "output": False},
            {"input": [10], "output": False},
        ],
        function_signature="def is_palindrome(x):",
    ),
)


def _upsert_problem(db: Session, seed: ProblemSeed) -> bool:
    problem = db.query(Problem).filter(Problem.uuid == seed.uuid).one_or_none()
    if problem is None:
        db.add(
            Problem(
                uuid=seed.uuid,
                title=seed.title,
                statement=seed.statement,
                hints=seed.hints,
                examples=seed.examples,
                test_cases=seed.test_cases,
                function_signature=seed.function_signature,
                deleted_at=None,
            )
        )
        db.flush()
        return True

    problem.title = seed.title
    problem.statement = seed.statement
    problem.hints = seed.hints
    problem.examples = seed.examples
    problem.test_cases = seed.test_cases
    problem.function_signature = seed.function_signature
    problem.deleted_at = None
    db.flush()
    return False


def main() -> int:
    db = SessionLocal()
    try:
        created = 0
        updated = 0
        for seed in SEED_PROBLEMS:
            if _upsert_problem(db, seed):
                created += 1
            else:
                updated += 1

        db.commit()
        print(
            "[seed] development data seeded successfully "
            f"(problems_total={len(SEED_PROBLEMS)}, "
            f"created={created}, updated={updated})"
        )
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
