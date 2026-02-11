# Backend Testing Skill

Guidelines for writing and running tests in the backend.

## Test structure

```
tests/
  conftest.py        # Shared fixtures: engine, db session, problem, storage
  integration/
    conftest.py      # Integration-specific fixtures: submission, queue_entry
    test_*.py        # Integration tests (full worker flows, multi-adapter)
  unit/              # (future) Pure logic tests, no DB
    conftest.py
    test_*.py
```

Non-integration test files must follow the same directory structure as the module they test, e.g. `backend/app/services/submission.py` → `tests/services/test_submission.py`.

## How tests run

Tests run inside a Docker container via `make test`. The `test` service in `infra/docker-compose.yml` (under the `test` profile):

- Builds from the `test` target in the backend Dockerfile (includes dev deps like pytest).
- Loads all env vars from `.env` via `env_file`.
- Overrides only `DATABASE_URL` to point at the test database (`codette_test`).
- Depends on `db` (Postgres with healthcheck) and `gcs` (fake-gcs-server).

The container command is `pytest tests/ -v`.

## Database setup

- Tests run against a **separate test database** (`codette_test`) on the same Postgres instance, not the dev database.
- Settings use `TestSettings` which reads from `.env.test` for local runs. Inside Docker, env vars come from `.env` with the `DATABASE_URL` override.
- The test database schema is created via `Base.metadata.create_all()` at session start (no Alembic needed for tests).

## Fixtures

- **Shared fixtures** live in `tests/conftest.py` — available to all test directories: `engine`, `db`, `problem`, `solution_file`, `storage`, `_gcs_bucket`.
- **Directory-specific fixtures** live in their own `conftest.py` (e.g. `tests/integration/conftest.py` has `submission`, `queue_entry`).
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

- `make test` — runs all tests inside a Docker container (default).
- Tests can also be run locally for debugging: `cd backend && set -a && . .env.test && set +a && uv run pytest tests/ -v` (requires Postgres and fake-gcs on localhost).

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
