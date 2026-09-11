#!/usr/bin/env bash
#
# V1.0-7 e2e-demo.sh
#
# End-to-end smoke run against a running ModelGate stack (mock mode).
# Creates a Goal, runs it to completion, asserts that:
#   - the run reaches status 'completed'
#   - the runtime status endpoint returns a final_summary with all
#     7 contract fields (completed / incomplete / quality / risks /
#     models / handoff_count / cost)
#   - tokens were actually consumed (proves the worker loop ran)
#
# Usage:
#   1. Start the stack (mock mode, no real Provider key needed):
#        EXECUTION_MODE=mock docker compose -f docker-compose.dev.yml up -d --build
#   2. Wait ~10s for backend to be ready
#   3. Run this script:
#        bash scripts/e2e-demo.sh
#   4. Tear down:
#        docker compose -f docker-compose.dev.yml down
#
# Exit codes:
#   0 = all assertions passed
#   non-zero = some assertion failed (printed to stderr)

set -euo pipefail

API="${API:-http://127.0.0.1:8000/api/v1}"
TITLE="${TITLE:-V1.0-7 e2e demo $(date +%s)}"
DESCRIPTION="${DESCRIPTION:-docker compose up + mock run}"
TEAM_PRESET="${TEAM_PRESET:-code-delivery}"

step() { printf "\n\033[1;34m▸ %s\033[0m\n" "$1"; }
ok()   { printf "  \033[1;32m✓\033[0m %s\n" "$1"; }
die()  { printf "\n\033[1;31m✗ %s\033[0m\n" "$1" >&2; exit 1; }

require_json() {
  python3 -c "import sys, json; json.load(sys.stdin)" >/dev/null <<<"$1" \
    || die "response is not valid JSON: $1"
}

step "Pre-flight: backend reachable"
curl -fsS "${API%/api/v1}/health" >/dev/null \
  || die "backend /health unreachable at ${API%/api/v1}/health — is the stack up?"
ok "backend /health OK"

step "1/4 Create goal (team_preset=$TEAM_PRESET)"
PAYLOAD=$(python3 - "$TITLE" "$DESCRIPTION" "$TEAM_PRESET" <<'PY'
import json, sys
print(json.dumps({
    "title": sys.argv[1],
    "description": sys.argv[2],
    "team_preset": sys.argv[3],
}))
PY
)
CREATE=$(curl -fsS -X POST "$API/goals" \
  -H 'Content-Type: application/json' \
  -d "$PAYLOAD")
require_json "$CREATE"
GOAL_ID=$(python3 -c "import sys, json; print(json.load(sys.stdin)['data']['goal_id'])" <<<"$CREATE")
ok "goal created: $GOAL_ID"

step "2/4 Start (idle -> planning)"
START=$(curl -fsS -X POST "$API/goals/$GOAL_ID/start")
require_json "$START"
ok "status -> $(python3 -c "import sys, json; print(json.load(sys.stdin)['data']['status'])" <<<"$START")"

step "3/4 Confirm plan v1"
CONFIRM=$(curl -fsS -X POST "$API/goals/$GOAL_ID/plans/1/confirm")
require_json "$CONFIRM"
ok "plan v1 -> $(python3 -c "import sys, json; print(json.load(sys.stdin)['data']['status'])" <<<"$CONFIRM")"

step "4/4 Execute"
EXEC=$(curl -fsS -X POST "$API/runtime/execute/$GOAL_ID")
require_json "$EXEC"
STATUS=$(python3 -c "import sys, json; print(json.load(sys.stdin)['data']['status'])" <<<"$EXEC")
COMPLETED=$(python3 -c "import sys, json; print(json.load(sys.stdin)['data']['tasks_completed'])" <<<"$EXEC")
TOKENS=$(python3 -c "import sys, json; print(json.load(sys.stdin)['data']['total_tokens_used'])" <<<"$EXEC")
ok "status=$STATUS, completed=$COMPLETED, tokens=$TOKENS"

[[ "$STATUS" == "completed" ]] || die "expected status=completed, got $STATUS"
[[ "$COMPLETED" -ge 1 ]]    || die "expected tasks_completed >= 1, got $COMPLETED"
[[ "$TOKENS" -gt 0 ]]       || die "expected total_tokens_used > 0 (worker loop didn't run), got $TOKENS"

step "Final Summary contract (V1.0-4 / V1.0-6d)"
FS=$(curl -fsS "$API/runtime/status/$GOAL_ID" | python3 -c "
import sys, json
d = json.load(sys.stdin)['data'].get('final_summary') or {}
print('|'.join(f'{k}={d.get(k)!r}' for k in ['completed','incomplete','quality','risks','models','handoff_count','cost']))
")
echo "  $FS"
MISSING=$(echo "$FS" | python3 -c "
import sys
required = ['completed','incomplete','quality','risks','models','handoff_count','cost']
have = {line.split('=',1)[0] for line in sys.stdin.read().split('|') if '=' in line}
print(' '.join(k for k in required if k not in have))")
[[ -z "$MISSING" ]] || die "final_summary missing keys: $MISSING"
ok "all 7 final_summary fields present"

printf "\n\033[1;32m✓ V1.0-7 e2e demo PASSED\033[0m  goal=%s\n" "$GOAL_ID"
