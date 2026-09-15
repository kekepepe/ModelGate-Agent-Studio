#!/usr/bin/env bash
#
# V1.3 P3 — e2e-mcp.sh
#
# MCP Runtime acceptance against the REAL official filesystem server
# (@modelcontextprotocol/server-filesystem via npx). Proves the full
# external-tool-platform loop:
#   register server -> sync (tools/list discovery into ToolDefinition)
#   -> human-enable a tool -> call it through the debugger endpoint
#   -> health check -> server death soft-disables its tools
#
# Prerequisites: node/npx on PATH (server runs via npx), running backend.
# Usage: bash scripts/e2e-mcp.sh
#
# Exit codes: 0 = PASS; non-zero = failed step printed to stderr.

set -euo pipefail

API="${API:-http://127.0.0.1:8000/api/v1}"
FS_SERVER_PKG="@modelcontextprotocol/server-filesystem"

step() { printf "\n\033[1;34m▸ %s\033[0m\n" "$1"; }
ok()   { printf "  \033[1;32m✓\033[0m %s\n" "$1"; }
die()  { printf "\n\033[1;31m✗ %s\033[0m\n" "$1" >&2; exit 1; }
json_field() { python3 -c "import sys, json; d = json.load(sys.stdin); print($2)" <<<"$1"; }

step "Pre-flight: backend reachable + npx available"
curl -fsS "${API%/api/v1}/health" >/dev/null || die "backend /health unreachable"
command -v npx >/dev/null || die "npx not found on PATH"
ok "backend OK · npx $(npx --version)"

step "1/7 Prepare workspace fixture"
WORKDIR=$(mktemp -d /tmp/modelgate-mcp-XXXX)
echo "modelgate mcp acceptance payload $(date +%s)" > "$WORKDIR/acceptance.txt"
ok "fixture dir: $WORKDIR"

# Warm the npx cache so the first MCP initialize does not race the
# package download against the client timeout.
npx -y "$FS_SERVER_PKG" "$WORKDIR" </dev/null >/dev/null 2>&1 || true
ok "npx package cache warmed"

step "2/7 Register the filesystem MCP server"
SERVER_NAME="e2e-fs-$(date +%s)"
REGISTER=$(curl -fsS -X POST "$API/mcp/servers" -H 'Content-Type: application/json' \
  -d "{\"name\": \"$SERVER_NAME\", \"transport\": \"stdio\", \"command_or_url\": \"npx\", \"args\": [\"-y\", \"$FS_SERVER_PKG\", \"$WORKDIR\"]}")
SERVER_ID=$(json_field "$REGISTER" "d['data']['id']")
[[ -n "$SERVER_ID" ]] || die "server registration failed"
ok "registered: $SERVER_NAME ($SERVER_ID)"

step "3/7 Sync — discover the server's tool catalog"
SYNC=$(curl -fsS -X POST "$API/mcp/servers/$SERVER_ID/sync")
TOOLS_TOTAL=$(json_field "$SYNC" "d['data']['tools_total']")
[[ "$TOOLS_TOTAL" -ge 5 ]] || die "expected ≥5 discovered tools, got $TOOLS_TOTAL"
ok "discovered $TOOLS_TOTAL tools (all disabled by default)"

step "4/7 Human-enable read_file (Model Manager toggle)"
TOOLS=$(curl -fsS "$API/tools?page_size=100")
READ_TOOL_ID=$(json_field "$TOOLS" "next((t['id'] for t in (d['data']['items'] if isinstance(d['data'], dict) else d['data']) if t['name'] == 'mcp__${SERVER_NAME}__read_file'), '')")
[[ -n "$READ_TOOL_ID" ]] || die "mcp__${SERVER_NAME}__read_file not found after sync"
curl -fsS -X PATCH "$API/tools/$READ_TOOL_ID/toggle" >/dev/null
ok "read_file enabled"

step "5/7 Call the MCP tool (debugger endpoint)"
CALL=$(curl -fsS -X POST "$API/mcp/servers/$SERVER_ID/call/read_file" \
  -H 'Content-Type: application/json' \
  -d "{\"path\": \"$WORKDIR/acceptance.txt\"}")
CONTENT=$(json_field "$CALL" "d['data']['content']")
[[ "$CONTENT" == *"modelgate mcp acceptance payload"* ]] \
  || die "unexpected tool content: $CONTENT"
ok "read_file returned the fixture content via MCP"

step "6/7 Health check"
HEALTH=$(curl -fsS "$API/mcp/servers/$SERVER_ID/health")
[[ "$(json_field "$HEALTH" "d['data']['health']")" == "healthy" ]] || die "expected healthy"
ok "server healthy"

step "7/7 Disable the server — tools soft-disable, calls are refused"
# Per-call spawn architecture: 'server death' is not observable (each call
# spawns a fresh process). The real degradation path is server disablement.
curl -fsS -X PATCH "$API/mcp/servers/$SERVER_ID/status" \
  -H 'Content-Type: application/json' -d '{"status": "disabled"}' >/dev/null
TOOLS_AFTER=$(json_field "$(curl -fsS "$API/tools?page_size=100")" "len([t for t in (d['data']['items'] if isinstance(d['data'], dict) else d['data']) if t.get('server_id') == '$SERVER_ID' and t['is_enabled']])")
[[ "$TOOLS_AFTER" -eq 0 ]] || die "expected all tools of the disabled server to be disabled, got $TOOLS_AFTER enabled"
CALL_AFTER=$(curl -s -X POST "$API/mcp/servers/$SERVER_ID/call/read_file" \
  -H 'Content-Type: application/json' -d "{\"path\": \"$WORKDIR/acceptance.txt\"}" -w "\n%{http_code}")
[[ "$CALL_AFTER" == *"400"* ]] || die "expected call on disabled server to be refused, got $CALL_AFTER"
ok "disabled server: tools soft-disabled, call refused (D8 degradation)"

rm -rf "$WORKDIR"
printf "\n\033[1;32m✓ V1.3 MCP acceptance PASSED\033[0m  server=%s\n" "$SERVER_NAME"
