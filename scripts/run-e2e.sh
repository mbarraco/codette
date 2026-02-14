#!/bin/sh
set -eu

COMPOSE_BASE="docker compose -f infra/docker-compose.yml"
COMPOSE_E2E="$COMPOSE_BASE --profile e2e"
DB_NAME="${E2E_DB_NAME:-codette_e2e}"
MODE="${1:-run}"

cleanup() {
  $COMPOSE_E2E rm -sf api-e2e web-e2e >/dev/null 2>&1 || true
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
$COMPOSE_BASE up -d db gcs
$COMPOSE_BASE exec -T db sh -c '/scripts/wait-for-pg.sh && /scripts/reset-db.sh "$1"' sh "$DB_NAME"

if [ "$MODE" = "build" ]; then
  $COMPOSE_E2E run --rm --build e2e
else
  $COMPOSE_E2E run --rm e2e
fi
