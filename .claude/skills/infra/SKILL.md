# Infrastructure Skill

Guidelines for Docker Compose configuration and environment variable management.

## Environment files

All runtime configuration lives in `.env` files — never hardcoded in `docker-compose.yml` or application code.

| File | Purpose | Read by |
|---|---|---|
| `.env` | Dev/prod config (docker-internal hostnames) | `docker-compose.yml` via `env_file`, app at runtime |
| `backend/.env.test` | Test config (localhost hostnames) | `TestSettings` via pydantic-settings (for rare local test runs) |

### Rules

- **Single source of truth**: every env var is defined in an `.env` file, not scattered across docker-compose, Makefile, or code.
- **No `environment:` blocks in docker-compose** for regular services: they get all their vars from `env_file: - ../.env`. The only exception is the `test` profile service, which overrides `DATABASE_URL` to point at the test database.
- **No test-specific vars**: the test environment mirrors dev/prod. The only difference is the database name (`codette_test` vs `codette`).
- **No `os.environ` manipulation in test code**.
- **pydantic-settings `extra="ignore"`** on `TestSettings`: the `.env.test` file may contain vars not modeled as settings fields (e.g. `STORAGE_EMULATOR_HOST` is consumed by third-party libraries directly from the environment, not via pydantic).

### Adding a new env var

1. Add it to `.env` with the docker-internal value.
2. Add it to `backend/.env.test` with the localhost value (only needed for local test runs outside Docker).
3. If the app needs to read it, add a field to `Settings` / `TestSettings`.
4. If only a third-party library reads it (e.g. `STORAGE_EMULATOR_HOST` for `google-cloud-storage`), no settings field needed — the library picks it up from the environment.

## Docker Compose

- Compose file: `infra/docker-compose.yml`
- All services that need app config use `env_file: - ../.env`.
- Port mappings use interpolation with defaults: `"${API_PORT:-8000}:8000"`.
- Healthchecks may interpolate vars for commands: `pg_isready -U ${POSTGRES_USER}`.
- Service images for local emulators (Postgres, fake-gcs-server) are pinned to a major version.

### Profiles

- **`test`**: The `test` service runs pytest inside a container. It uses `env_file: - ../.env` for all config and overrides only `DATABASE_URL` via `environment:` to point at the test database (`codette_test`). It depends on `db` (with healthcheck) and `gcs`. Run with: `make test`.
- **`tools`**: Build-only images for runner and grader.

## Task: $ARGUMENTS

1. Read `.env`, `backend/.env.test`, and `infra/docker-compose.yml` before making changes.
2. Follow the rules above — no hardcoded config in compose, no env manipulation in code.
3. After changes, verify with `make test`.
