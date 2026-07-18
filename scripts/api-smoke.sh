#!/usr/bin/env bash
set -euo pipefail

curl --fail --silent http://127.0.0.1:8000/health | grep -F '"status":"ok"'
curl --fail --silent http://127.0.0.1:8000/api/v1/agents >/dev/null
curl --fail --silent http://127.0.0.1:8000/api/v1/models >/dev/null
