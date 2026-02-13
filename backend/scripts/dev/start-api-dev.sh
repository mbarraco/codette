#!/bin/sh
set -eu

python /app/scripts/dev/wait_for_dependencies.py

exec uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app/app
