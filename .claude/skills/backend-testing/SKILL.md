# Backend Testing Skill

Guidelines for writing and running tests in the backend.

## Test structure

```
tests/
  integration/
    conftest.py      # DB engine, session fixture, shared model fixtures
    test_*.py        # Integration tests against real Postgres
  unit/              # (future) Pure logic tests, no DB
    conftest.py
    test_*.py
```

## Database setup

- Tests run against a **separate test database** on the same Postgres instance, not the dev database.
- Test settings use a dedicated settings class (`TestSettings`) that reads from `.env.test`. This exercises the same `pydantic-settings` mechanism as the app — no raw `os.environ` in test code.
- The test database schema is created via `Base.metadata.create_all()` at session start (no Alembic needed for tests).

## Fixtures

- Shared fixtures live in `tests/integration/conftest.py` — pytest auto-discovers them.
- **DB session fixture**: wraps each test in a transaction that rolls back after the test. No data persists between tests.
- **Model fixtures** chain via pytest dependency injection:
  ```python
  @pytest.fixture()
  def problem(db) -> Problem: ...

  @pytest.fixture()
  def submission(db, problem) -> Submission: ...
  ```
- Tests declare what they need in their function signature — no manual setup/teardown.
- Keep fixtures minimal: insert the minimum data needed, use simple hardcoded values.

## Integration tests

- Integration tests hit real infrastructure: Postgres, object storage (fake-gcs-server), etc.
- Test the real adapters (repositories, storage, job runners) — minimize use of fakes and mocks.
- Instantiate the class under test with its real adapter dependencies. The DB session from the fixture provides isolation via rollback.
- Assert intermediate state when testing multi-step flows (e.g. check status after each step).
- Scaffold future steps as comments when the adapter doesn't exist yet — the test serves as a living spec.

## Running tests

- Tests are run via `make test` (or `make test-integration` for just integration tests).
- The Makefile target runs: `cd backend && uv run pytest tests/integration/ -v`

## Conventions

- One test file per domain concept or flow (e.g. `test_sea.py` for the SEA worker flow).
- Test function names: `test_<what>_<scenario>` (e.g. `test_sea_happy_path`).
- No mocks unless testing against an external API that can't be emulated locally.
- Prefer asserting on model attributes directly over re-querying the DB, except for final-state assertions.

## Task: $ARGUMENTS

1. Read existing test files and conftest before making changes.
2. Add fixtures to the appropriate conftest, not inline in test files.
3. Follow the fixture chaining pattern — don't duplicate seed logic.
4. Run `make test` after changes to verify.
