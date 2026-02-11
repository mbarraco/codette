# SEA — Submission Evaluation Architecture

Goal: Prove the SEA "happy path" end-to-end using local scaffold infra:

DB queue row -> Worker claims -> Runner produces artifact -> Grader produces verdict -> Worker writes evaluation.

## Architecture

### Adapter Design

The worker uses two separate adapter protocols instead of a single `ExecutionAdapter`:

- **`RunnerAdapter`** — executes submitted code and writes `runner_output.json`
- **`GraderAdapter`** — evaluates runner output and writes `grader_output.json`

Both share a common `ExecutionOutcome` return type with `execution_ref` and `status`.

### Worker Flow (`SeaWorker.process_next()`)

1. Claim next queue entry
2. Create `Run` record (status `queued`)
3. Build `RunnerRequest`, invoke `RunnerAdapter.execute()`
4. Update run: status `runner_done`, set `runner_output_uri`
5. Build `GraderRequest`, invoke `GraderAdapter.execute()`
6. Update run: set `grader_output_uri`
7. Download grader output, parse verdict, create `SubmissionEvaluation`
8. Update run: status `done`

On error: mark run `failed`, re-raise.

### Adapter Matrix

1. **`FakeRunnerAdapter` / `FakeGraderAdapter`** (integration tests)
   - Deterministic in-process implementations
   - Write minimal valid JSON to storage via `StorageAdapter`
   - No Docker or external runtime required
2. **`LocalExecutionAdapter`** (developer local) — planned
   - Runs local runner/grader entrypoints
   - Writes artifacts to fake GCS (same URI contract)
3. **`GcpTaskRunAdapter`** (production) — planned
   - Submits runner/grader tasks to GCP

## Rollout

- [x] Add `RunRepository` and `SubmissionEvaluationRepository`
- [x] Add `RunnerAdapter` / `GraderAdapter` protocols in `contracts.py`
- [x] Add `FakeRunnerAdapter` / `FakeGraderAdapter` for tests
- [x] Wire `SeaWorker` constructor for full DI
- [x] Complete `process_next()` with full pipeline
- [x] Make `test_sea.py` pass end-to-end
- [ ] Add `LocalExecutionAdapter`
- [ ] Add `GcpTaskRunAdapter` and config switch

## Definition of Done (Phase 1)

- [x] Given a single inserted queue row:
  - [x] `runs` row is created with a valid `run_id`
  - [x] `runner_output.json` exists at `runner_output_uri`
  - [x] `grader_output.json` exists at `grader_output_uri`
  - [x] `submission_evaluations` row exists and matches grader verdict
  - [x] Run status ends as `done`
- [x] Artifacts are inspectable by `run_id` for debugging
