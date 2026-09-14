#!/usr/bin/env bash
#
# V1.1 e2e-handoff.sh
#
# Handoff business-flow acceptance run against a running ModelGate stack
# (mock mode). Implements the design §8 V1.1 acceptance criteria:
#   - simulate quota exhaustion (LIMITED via a 429 usage record)
#   - observe the automatic handoff (goal stops in status 'handoff')
#   - observe the Handoff event chain in the execution logs
#   - accept the handoff from the API (same call the Workspace button makes)
#   - resume execution and reach 'completed' with handoff_count >= 1
#   - see the interception reflected in GET /quota/overview
#
# Usage:
#   1. Start the stack (mock mode, no real Provider key needed):
#        EXECUTION_MODE=mock docker compose -f docker-compose.dev.yml up -d --build
#   2. Wait ~10s for backend to be ready
#   3. Run this script:
#        bash scripts/e2e-handoff.sh
#   4. Tear down:
#        docker compose -f docker-compose.dev.yml down
#
# Exit codes:
#   0 = all assertions passed
#   non-zero = some assertion failed (printed to stderr)

set -euo pipefail

API="${API:-http://127.0.0.1:8000/api/v1}"
TITLE="${TITLE:-V1.1 e2e handoff $(date +%s)}"
DESCRIPTION="${DESCRIPTION:-quota exhaustion -> auto handoff -> accept -> resume}"
TEAM_PRESET="${TEAM_PRESET:-code-delivery}"

step() { printf "\n\033[1;34m▸ %s\033[0m\n" "$1"; }
ok()   { printf "  \033[1;32m✓\033[0m %s\n" "$1"; }
die()  { printf "\n\033[1;31m✗ %s\033[0m\n" "$1" >&2; exit 1; }

require_json() {
  python3 -c "import sys, json; json.load(sys.stdin)" >/dev/null <<<"$1" \
    || die "response is not valid JSON: $1"
}

json_field() { # json_field <json> <python expression on d>
  python3 -c "import sys, json; d = json.load(sys.stdin); print($2)" <<<"$1"
}

step "Pre-flight: backend reachable"
curl -fsS "${API%/api/v1}/health" >/dev/null \
  || die "backend /health unreachable at ${API%/api/v1}/health — is the stack up?"
ok "backend /health OK"

step "1/8 Find every enabled station's default model"
AGENTS=$(curl -fsS "$API/agents?is_enabled=true&page_size=100")
require_json "$AGENTS"
# Planning can fall back to a single-station plan, so the script blocks the
# default model of EVERY enabled station: whichever station executes first,
# its default-model intercept fires deterministically.
STATION_MODELS=$(json_field "$AGENTS" "' '.join(sorted({a['default_model_id'] for a in d['data']['items'] if a.get('default_model_id')}))")
[[ -n "$STATION_MODELS" ]] || die "no enabled station with a default model found — seed the demo data first"
ok "station default models: $STATION_MODELS"

MODELS=$(curl -fsS "$API/models")
require_json "$MODELS"

step "2/8 Simulate quota exhaustion on: $STATION_MODELS"
for MODEL_ID in $STATION_MODELS; do
  MODEL_PROVIDER=$(json_field "$MODELS" "next((m['provider'] for m in d['data']['items'] if m['id'] == '$MODEL_ID'), 'openai')")
  MODEL_NAME=$(json_field "$MODELS" "next((m['model_name'] for m in d['data']['items'] if m['id'] == '$MODEL_ID'), '$MODEL_ID')")
  USAGE=$(curl -fsS -X POST "$API/quota/record-usage" \
    -H 'Content-Type: application/json' \
    -d "{\"provider\": \"$MODEL_PROVIDER\", \"model_id\": \"$MODEL_ID\", \"model_name\": \"$MODEL_NAME\", \"error_code\": 429, \"error_type\": \"rate_limit_exceeded\"}")
  require_json "$USAGE"
  QUOTA_STATUS=$(json_field "$USAGE" "d['data']['updated_status']")
  # A 429 trip lands in cooldown (rate-limit window) or limited; the runtime
  # intercept treats both as blocking.
  [[ "$QUOTA_STATUS" == "limited" || "$QUOTA_STATUS" == "cooldown" ]] \
    || die "expected quota_status=limited|cooldown after a 429 usage record for $MODEL_ID, got $QUOTA_STATUS"
  INTERCEPT=$(curl -fsS "$API/quota/models/$MODEL_ID/intercept")
  [[ "$(json_field "$INTERCEPT" "d['data']['intercepted']")" == "True" ]] \
    || die "expected the intercept endpoint to report intercepted=True for $MODEL_ID"
  ok "$MODEL_ID -> limited (intercepted)"
done

step "3/8 Create goal + start + confirm plan (team_preset=$TEAM_PRESET)"
PAYLOAD="{\"title\": \"$TITLE\", \"description\": \"$DESCRIPTION\", \"team_preset\": \"$TEAM_PRESET\"}"
CREATE=$(curl -fsS -X POST "$API/goals" -H 'Content-Type: application/json' -d "$PAYLOAD")
GOAL_ID=$(json_field "$CREATE" "d['data']['goal_id']")
ok "goal created: $GOAL_ID"
curl -fsS -X POST "$API/goals/$GOAL_ID/start" >/dev/null
CONFIRM=$(curl -fsS -X POST "$API/goals/$GOAL_ID/plans/1/confirm")
ok "plan v1 -> $(json_field "$CONFIRM" "d['data']['status']")"

step "4/8 Execute — pipeline must stop with an automatic handoff"
EXEC=$(curl -fsS -X POST "$API/runtime/execute/$GOAL_ID")
require_json "$EXEC"
GOAL_STATUS=$(json_field "$EXEC" "d['data']['status']")
TASKS_HANDOFF=$(json_field "$EXEC" "d['data'].get('tasks_handoff', 0)")
[[ "$GOAL_STATUS" == "handoff" ]] || die "expected goal status=handoff after quota intercept, got $GOAL_STATUS"
[[ "$TASKS_HANDOFF" -ge 1 ]] || die "expected tasks_handoff >= 1, got $TASKS_HANDOFF"
ok "goal status=handoff, tasks_handoff=$TASKS_HANDOFF"

step "5/8 Handoff record: reason=quota_exceeded, summary ready with provenance"
LIST=$(curl -fsS "$API/handoffs?goal_id=$GOAL_ID")
require_json "$LIST"
HANDOFF_ID=$(json_field "$LIST" "d['data']['items'][0]['id'] if d['data']['items'] else ''")
[[ -n "$HANDOFF_ID" ]] || die "no handoff record found for the goal"
REASON=$(json_field "$LIST" "d['data']['items'][0]['reason']")
HSTATUS=$(json_field "$LIST" "d['data']['items'][0]['status']")
[[ "$REASON" == "quota_exceeded" ]] || die "expected handoff reason=quota_exceeded, got $REASON"
[[ "$HSTATUS" == "ready" ]] || die "expected handoff status=ready, got $HSTATUS"
DETAIL=$(curl -fsS "$API/handoffs/$HANDOFF_ID")
SUMMARY_FIELDS=$(json_field "$DETAIL" "'|'.join(sorted((d['data'].get('handoff_summary') or {}).keys()))")
python3 - "$SUMMARY_FIELDS" <<'PY' || die "handoff_summary is missing required fields"
import sys
have = set(sys.argv[1].split('|'))
required = {"original_goal", "current_task", "completed_work", "unfinished_work", "important_constraints",
            "key_decisions", "errors_and_risks", "next_suggested_steps", "context_needed"}
missing = required - have
sys.exit(1 if missing else 0)
PY
GENERATED_BY=$(json_field "$DETAIL" "(d['data'].get('handoff_summary') or {}).get('generated_by', '')")
[[ "$GENERATED_BY" == "fallback" || "$GENERATED_BY" == "llm" ]] || die "expected summary generated_by=fallback|llm, got '$GENERATED_BY'"
ok "handoff $HANDOFF_ID ready (generated_by=$GENERATED_BY)"

step "6/8 Logs show the Handoff event chain"
LOGS=$(curl -fsS "$API/logs?goal_id=$GOAL_ID&event_type=handoff_created")
HANDOFF_LOGS=$(json_field "$LOGS" "d['data'].get('total', len(d['data'].get('items', [])))")
[[ "$HANDOFF_LOGS" -ge 1 ]] || die "expected at least one handoff_created log, got $HANDOFF_LOGS"
ALL_LOGS=$(curl -fsS "$API/logs?goal_id=$GOAL_ID&event_type=model_call")
SUMMARY_LOGS=$(json_field "$ALL_LOGS" "d['data'].get('total', len(d['data'].get('items', [])))")
[[ "$SUMMARY_LOGS" -ge 1 ]] || die "expected the handoff summary model_call log in the event chain"
ok "handoff_created + summary model_call logs present"

step "7/8 Accept the handoff, clear the quota, resume the inherited worker"
ACCEPT=$(curl -fsS -X POST "$API/handoffs/$HANDOFF_ID/accept" -H 'Content-Type: application/json' -d '{}')
require_json "$ACCEPT"
[[ "$(json_field "$ACCEPT" "d['data']['status']")" == "accepted" ]] || die "handoff accept did not reach status=accepted"
ok "handoff accepted, task reassigned"

RESET_OK=1
for MODEL_ID in $STATION_MODELS; do
  RESET=$(curl -fsS -X PATCH "$API/quota/models/$MODEL_ID/status" \
    -H 'Content-Type: application/json' \
    -d '{"quota_status": "normal", "reason": "e2e-handoff: quota restored"}')
  require_json "$RESET" || RESET_OK=0
done
[[ "$RESET_OK" == "1" ]] || die "failed to restore quota status"
ok "quota_status -> normal for all coder models"

TASK_ID=$(json_field "$DETAIL" "d['data']['task_id']")
RESUME=$(curl -fsS -X POST "$API/runtime/execute-step/$TASK_ID")
require_json "$RESUME"
TASK_STATUS=$(json_field "$RESUME" "d['data']['status']")
case "$TASK_STATUS" in
  completed|completed_verified|completed_unverified) ok "resumed task -> $TASK_STATUS" ;;
  *) die "expected the resumed task to complete, got $TASK_STATUS" ;;
esac

# Running the pipeline again evaluates the Completion Gate (and executes any
# remaining plan tasks), flipping the goal to its terminal status.
EXEC2=$(curl -fsS -X POST "$API/runtime/execute/$GOAL_ID")
require_json "$EXEC2"
FINAL_STATUS=$(json_field "$EXEC2" "d['data']['status']")
[[ "$FINAL_STATUS" == "completed" ]] || die "expected goal status=completed after resume, got $FINAL_STATUS"
ok "goal status=completed"

step "8/8 Runtime + quota visibility"
STATUS=$(curl -fsS "$API/runtime/status/$GOAL_ID")
HANDOFF_COUNT=$(json_field "$STATUS" "(d['data'].get('final_summary') or {}).get('handoff_count', 0)")
[[ "$HANDOFF_COUNT" -ge 1 ]] || die "expected final_summary.handoff_count >= 1, got $HANDOFF_COUNT"
ok "final_summary.handoff_count=$HANDOFF_COUNT"

OVERVIEW=$(curl -fsS "$API/quota/overview")
TRIGGERED=$(json_field "$OVERVIEW" "max((m['handoff_triggered_count'] for m in d['data']['models'] if m['model_id'] in '$STATION_MODELS'.split()), default=0)")
[[ "$TRIGGERED" -ge 1 ]] || die "expected handoff_triggered_count >= 1 on a coder model in quota overview, got $TRIGGERED"
ok "quota overview shows handoff_triggered_count=$TRIGGERED"

printf "\n\033[1;32m✓ V1.1 e2e handoff PASSED\033[0m  goal=%s handoff=%s\n" "$GOAL_ID" "$HANDOFF_ID"
