# Post-Change Checklist

## After Every Backend Change

1. **Seed script** — Verify `backend/scripts/dev/seed_dev_data.py` still works with the change.
   - New models or endpoints: add seed data and API client methods.
   - Changed schemas or routes: update existing seed payloads and client calls.
   - New auth/permission requirements: update `SeedApiClient` to handle them.
   - The seed script must use API endpoints for data changes — only bootstrap the first admin invitation via direct DB access.

2. **Backend tests** — Run `make test` and confirm all tests pass.

3. **E2E tests** — Verify and update Playwright specs under `e2e/tests/`.
   - New endpoints: add coverage in existing or new spec files.
   - Changed response shapes or auth requirements: update specs and fixtures.
   - All API calls in e2e must use `authRequest` (from `e2e/tests/fixtures.ts`) — never bare `request`.
   - All browser navigation to protected pages must use `authedPage` — never bare `page`.
   - Run `make e2e-build` after changes and confirm all tests pass.

4. **Healthchecks** — If adding auth to previously-public endpoints, check that no healthcheck or readiness probe depends on them.
   - `infra/docker-compose.yml` api-e2e healthcheck must hit `/health` (unauthenticated).
   - `e2e/scripts/wait-for-web.sh` must hit `/api/health` (proxied, unauthenticated).

## After Every Frontend Change

1. **Build** — Run `cd web && npm run build` and confirm zero TypeScript errors.
2. **E2E tests** — Run `make e2e-build` and confirm all tests pass.

## After Every E2E Change

1. **Verify locally** — Use `make e2e E2E_GREP="test name"` to run a single test before running the full suite.
2. **Full suite** — Run `make e2e-build` and confirm all tests pass.
