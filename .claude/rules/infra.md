# Infrastructure Rules

## Environment Source of Truth
- Keep runtime configuration in `.env` files.
- Never hardcode runtime config in application code or `infra/docker-compose.yml`.
- Use `.env` for Docker-backed app and test runs.
- Use `backend/.env.test` for local non-Docker test runs.
- Do not manipulate `os.environ` in test code.

## Docker Compose Rules
- Compose file path is `infra/docker-compose.yml`.
- Services must load app configuration via `env_file: - ../.env`.
- Do not add regular `environment:` blocks for app services.
- The only allowed override is the `test` service `DATABASE_URL` pointing to `codette_test`.
- Use variable interpolation for ports and healthcheck commands.
- Pin emulator and dependency images to a major version.

## Adding a New Environment Variable
1. Add the variable to `.env` with Docker-internal values.
2. Add the variable to `backend/.env.test` with localhost values when local tests need it.
3. Add fields to `Settings` and `TestSettings` if app code reads the variable.
4. Skip settings fields when only third-party libraries read the variable directly.

## Settings Rule
- Keep `TestSettings` configured with `extra="ignore"` to allow environment-only values used by third-party libraries.
