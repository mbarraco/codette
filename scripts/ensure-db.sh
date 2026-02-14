#!/bin/sh
# Usage: ensure-db.sh <db_name>
# Creates a Postgres database if it doesn't exist.
# Expects to run inside the db container (via docker compose exec).
set -eu

DB_NAME="${1:?Usage: ensure-db.sh <db_name>}"
PG_USER="${POSTGRES_USER:-codette}"

if ! psql -U "$PG_USER" -d postgres -tAc \
  "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" | grep -q 1; then
  psql -v ON_ERROR_STOP=1 -U "$PG_USER" -d postgres \
    -c "CREATE DATABASE ${DB_NAME}"
  echo "[ensure-db] created database ${DB_NAME}"
else
  echo "[ensure-db] database ${DB_NAME} already exists"
fi
