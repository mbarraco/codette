#!/bin/sh
set -eu

COMPOSE_BASE="docker compose -f infra/docker-compose.yml"
COMPOSE_E2E="$COMPOSE_BASE --profile e2e"
COMPOSE_JOBS="$COMPOSE_BASE --profile jobs"
DB_NAME="${E2E_DB_NAME:-codette_e2e}"
MODE="${1:-run}"

cleanup() {
  $COMPOSE_E2E rm -sf api-e2e web-e2e worker-e2e >/dev/null 2>&1 || true
}

case "$MODE" in
  run|build) ;;
  *)
    echo "Usage: $0 [run|build]" >&2
    exit 2
    ;;
esac

trap cleanup EXIT

cleanup

# Build runner and grader images needed by the worker's sibling containers
$COMPOSE_JOBS build runner grader

$COMPOSE_BASE up -d db gcs
$COMPOSE_BASE exec -T db sh -c '/scripts/wait-for-pg.sh && /scripts/reset-db.sh "$1"' sh "$DB_NAME"

if [ -n "${E2E_GREP:-}" ]; then
  if [ "$MODE" = "build" ]; then
    $COMPOSE_E2E run --rm --build -e "E2E_GREP=$E2E_GREP" e2e
  else
    $COMPOSE_E2E run --rm -e "E2E_GREP=$E2E_GREP" e2e
  fi
else
  if [ "$MODE" = "build" ]; then
    $COMPOSE_E2E run --rm --build e2e
  else
    $COMPOSE_E2E run --rm e2e
  fi
fi
