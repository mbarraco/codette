#!/bin/sh
# Usage: reset-db.sh <db_name>
# Drops and recreates a Postgres database.
# Expects to run inside the db container (via docker compose exec).
set -eu

DB_NAME="${1:?Usage: reset-db.sh <db_name>}"
PG_USER="${POSTGRES_USER:-codette}"

psql -v ON_ERROR_STOP=1 -U "$PG_USER" -d postgres \
  -c "DROP DATABASE IF EXISTS ${DB_NAME}" \
  -c "CREATE DATABASE ${DB_NAME}"

echo "[reset-db] recreated database ${DB_NAME}"
