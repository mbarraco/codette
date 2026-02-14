#!/bin/sh
# Waits for Postgres to accept connections.
# Expects to run inside the db container (via docker compose exec).
set -eu

PG_USER="${POSTGRES_USER:-codette}"
PG_DB="${POSTGRES_DB:-codette}"

until pg_isready -U "$PG_USER" -d "$PG_DB" >/dev/null 2>&1; do
  sleep 1
done

echo "[wait-for-pg] ready"
