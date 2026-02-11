# Testing Rules

## Test Layout
- Keep shared fixtures in `backend/tests/conftest.py`.
- Keep directory-scoped fixtures in local `conftest.py` files, such as `backend/tests/integration/conftest.py`.
- Mirror module paths for non-integration tests.
- Example mapping: `backend/app/services/submission.py` -> `backend/tests/services/test_submission.py`.

## Execution Rules
- Default test command is `make test`.
- `make test` must execute pytest in the Docker `test` service defined in `infra/docker-compose.yml`.
- Local debug runs may use `backend/.env.test` and `uv run pytest tests/ -v` from `backend/`.

## Database and Fixture Rules
- Use the dedicated `codette_test` database for tests.
- Create the test schema with `Base.metadata.create_all()` at session start.
- Wrap each test in a transaction and roll it back after the test.
- Keep fixtures minimal and compose data through fixture dependency injection.
- Do not seed test data inline in test functions when a fixture is appropriate.

## Integration Test Rules
- Prefer real adapters and infrastructure (Postgres, fake-gcs-server) over mocks.
- Instantiate classes under test with real adapter dependencies.
- Assert intermediate state in multi-step flows, not only final state.
- Use comments to scaffold future assertions when an adapter is not implemented yet.

## Style Rules
- Use function-based tests only (`test_*`).
- Do not use class-based tests.
- Name tests with `test_<what>_<scenario>`.
- Avoid mocks unless the dependency cannot be emulated locally.
