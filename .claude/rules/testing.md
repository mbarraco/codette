# Testing Rules

## Test Layout
- Always keep shared fixtures in `backend/tests/conftest.py`.
- Always keep directory-scoped fixtures in local `conftest.py` files (e.g. `backend/tests/api/conftest.py`).
- Mirror module paths for non-integration tests: `backend/app/services/submission.py` -> `backend/tests/services/test_submission.py`.

## Execution Rules
- Default test command is `make test`.
- `make test` must execute pytest in the Docker `test` service defined in `infra/docker-compose.yml`.
- Local debug runs must use `backend/.env.test` and `uv run pytest tests/ -v` from `backend/`.

## Database and Fixture Rules
- Always use the dedicated `codette_test` database for tests.
- Always create the test schema with `Base.metadata.create_all()` at session start.
- Always wrap each test in a transaction and roll it back after the test.
- Never seed test data inline in test functions when a fixture is appropriate.

### Engine and rollback fixtures (from `backend/tests/conftest.py`)
```python
@pytest.fixture(scope="session")
def engine():
    engine = create_engine(test_settings.database_url)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture()
def db(engine) -> Session:
    """Yields a DB session that rolls back after each test."""
    conn = engine.connect()
    txn = conn.begin()
    session = Session(bind=conn)
    yield session
    session.close()
    txn.rollback()
    conn.close()
```

### API client fixture (from `backend/tests/api/conftest.py`)
```python
@pytest.fixture()
def client(db: Session):
    """TestClient whose DB dependency is the transactional test session."""
    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    yield TestClient(app)
    app.dependency_overrides.clear()
```

### Data fixtures must use db session
```python
@pytest.fixture()
def problem(db: Session) -> Problem:
    p = Problem(
        statement="Return the sum of two integers.",
        hints="Think about the + operator.",
        examples="add(1, 2) == 3",
    )
    db.add(p)
    db.flush()
    return p
```

## Integration Test Rules
- Always use real adapters and infrastructure (Postgres, fake-gcs-server) — never mock them.
- Instantiate classes under test with real adapter dependencies.
- Always assert intermediate state in multi-step flows, not only final state.
- Only use mocks when the dependency cannot be emulated locally.

## Style Rules
- Always use function-based tests (`test_*`) — never class-based tests.
- Name non-API tests as `test_<what>_<scenario>`.
- Name API endpoint tests as `test_<resource_path>_<http_verb>_<behavior>`.
- Always keep the HTTP verb immediately before the behavior suffix.
- Always convert route segments to snake_case in `<resource_path>`.

### Correct API test naming
```python
# backend/tests/api/test_submission_endpoint.py

def test_api_v1_submissions_post_returns_201_with_submission(
    client: TestClient, problem: Problem
) -> None:
    response = client.post(
        "/api/v1/submissions/",
        json={"problem_id": problem.id, "code": "def add(a, b): return a + b"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["problem_id"] == problem.id
    assert body["uuid"] is not None

def test_api_v1_submissions_get_returns_empty_list(client: TestClient) -> None:
    response = client.get("/api/v1/submissions/")
    assert response.status_code == 200
    assert response.json() == []
```

### Wrong — class-based test
```python
class TestSubmissions:  # NEVER
    def test_create(self): ...
```

### Wrong — naming without HTTP verb position
```python
def test_submissions_returns_201_post(): ...  # NEVER — verb must precede behavior
```
