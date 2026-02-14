#!/bin/sh
set -eu

python /app/scripts/dev/wait_for_dependencies.py

exec python -m app.worker.main
