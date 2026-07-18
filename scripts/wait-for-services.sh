#!/usr/bin/env bash
set -euo pipefail

for attempt in {1..60}; do
  if curl --fail --silent http://127.0.0.1:8000/health >/dev/null \
    && curl --fail --silent http://127.0.0.1:5173/ >/dev/null; then
    exit 0
  fi
  sleep 1
done

echo "Services did not become ready within 60 seconds" >&2
exit 1
