# Codette Codex Instructions

## Source of Truth
- Claude rule docs in `.claude/rules/*.md` are canonical. Keep them as the single source of truth.
- `CLAUDE.md` contains shared backend conventions that apply across backend tasks.

## Rule Loading Map
Load and follow the matching rule file(s) before editing code in that area:

- API routes, handlers, schemas, endpoint contracts:
  - `.claude/rules/api-layer.md`
- Backend package architecture and dependency direction:
  - `.claude/rules/backend.md`
- SQLAlchemy models, relationships, and migrations:
  - `.claude/rules/models.md`
- Services, repositories, and external adapters:
  - `.claude/rules/services-and-adapters.md`
- Docker Compose, env wiring, and settings/config:
  - `.claude/rules/infra.md`
- Pytest layout, fixtures, naming, and integration coverage:
  - `.claude/rules/testing.md`

## Conflict Resolution
- Apply all relevant rule files for a change.
- If rules appear to conflict, prefer the most specific rule document for the files being edited.
- Preserve architectural dependency direction defined in `CLAUDE.md` and `.claude/rules/backend.md`.
