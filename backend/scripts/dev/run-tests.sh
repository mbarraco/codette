#!/bin/sh
set -eu

python /app/scripts/dev/wait_for_dependencies.py

exec pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml "$@"
