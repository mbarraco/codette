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
- Never add regular `environment:` blocks for app services.
- The only allowed environment override is the `test` service `DATABASE_URL` pointing to `codette_test`.
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
