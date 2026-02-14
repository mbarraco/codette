# Infrastructure Rules

## Environment Source of Truth
- Always keep runtime configuration in `.env` files.
- Never hardcode runtime config in application code or `infra/docker-compose.yml`.
- Always use `.env` for Docker-backed app and test runs.
- Always use `backend/.env.test` for local non-Docker test runs.
- Never manipulate `os.environ` in test code.

## Docker Compose Rules
- Compose file path is always `infra/docker-compose.yml`.
- Services must load app configuration via `env_file: - ../.env`.
- `environment:` blocks are allowed on test and e2e services to override database URL, storage bucket, and emulator hosts. Production-like services (`api`, `worker`) must only use `env_file`.
- Always use variable interpolation for ports and healthcheck commands.
- Always pin emulator and dependency images to a major version.

## Adding a New Environment Variable
1. Add the variable to `.env` with Docker-internal values.
2. Add the variable to `backend/.env.test` with localhost values when local tests need it.
3. Add fields to `Settings` and `TestSettings` if app code reads the variable.
4. Skip settings fields when only third-party libraries read the variable directly.

## Settings Classes
- Always define settings in `backend/app/core/settings.py` using `pydantic-settings`.
- Always keep `TestSettings` configured with `extra="ignore"`.
- Always access settings through `get_settings()` — never instantiate `Settings()` directly in application code.

### Settings pattern (from `backend/app/core/settings.py`)
```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    storage_bucket: str
    api_port: int = 8000
    log_level: str = "INFO"

class TestSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.test", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str
    storage_bucket: str

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

## Frontend Development
- Frontend runs locally via `npm run dev` from `web/` — never in Docker for development.
- Vite proxies `/api` to the backend API (auto-detects Docker vs localhost via `vite.config.ts`).
- `web-e2e` Docker service exists only for e2e tests — not for local dev.
- After changing frontend dependencies, run `make e2e-build` to verify the Docker build still works.

## E2E and Makefile
- `make test` runs backend tests in the Docker `test` service.
- `make e2e` runs Playwright e2e tests; must clean up `api-e2e` and `web-e2e` containers after completion.
- The `e2e` runner uses `--rm`; dependency containers (`api-e2e`, `web-e2e`) need explicit stop.
