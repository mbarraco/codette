#!/bin/sh
set -eu

URL="${BASE_URL:-http://web-e2e:5173}"
RETRIES="${WAIT_RETRIES:-40}"
SLEEP="${WAIT_SLEEP_SECONDS:-2}"

attempt=1
while [ "$attempt" -le "$RETRIES" ]; do
  # Check both web server and API health (proxied through web)
  if curl -so /dev/null "$URL" 2>/dev/null && \
     curl -sf "$URL/api/health" >/dev/null 2>&1; then
    echo "[wait] web ready on attempt $attempt/$RETRIES"
    exit 0
  fi
  echo "[wait] web not ready (attempt $attempt/$RETRIES), retrying in ${SLEEP}s..."
  sleep "$SLEEP"
  attempt=$((attempt + 1))
done

echo "[wait] web did not become ready after $RETRIES attempts"
exit 1
