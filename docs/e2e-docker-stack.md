# Docker Compose + E2E 运维指南

> 原名 `V1.0-7-e2e.md`（V1.0-7 阶段产物，2026-09-15 随仓库结构整理移入 docs/ 并更名）。
> 除本指南描述的核心流程外，另有两条验收脚本：
> `scripts/e2e-handoff.sh`（V1.1 Handoff）与 `scripts/e2e-product-acceptance.sh`
> （V1.2.1 三场景产品验收，README 能力声明的自动证据）。

This file documents how to bring the stack up locally and prove
the full Goal → Task → Worker → Model → Final Summary pipeline works.

## 1. One-time prerequisites

- Docker 24+ (with Compose v2)
- `git` (used by the Agent runtime; already a dep of the backend image)

That's it. **No real Provider key required** for the demo — we use
`EXECUTION_MODE=mock` so a deterministic mock model answers every LLM
call.

## 2. Start the stack (mock mode, hot-reload)

```bash
EXECUTION_MODE=mock docker compose -f docker-compose.dev.yml up -d --build
```

This builds two images and starts them:

| Container | Port | Purpose |
|---|---|---|
| `modelgate-backend-dev` | 8000 | FastAPI + uvicorn, SQLite, all V1.0-3 default Stations seeded |
| `modelgate-frontend-dev` | 5173 | Vite dev server, HMR enabled |

Wait ~10 seconds for the backend to be ready (it runs all 9 Alembic
migrations on first boot, including the V1.0-3 station fields migration).

Verify both:

```bash
curl http://127.0.0.1:8000/health                # → {"status":"ok"}
curl -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5173/   # → 200
```

## 3. Run the e2e demo

```bash
bash scripts/e2e-demo.sh
```

Expected output (abridged):

```
▸ Pre-flight: backend reachable
  ✓ backend /health OK
▸ 1/4 Create goal (team_preset=code-delivery)
  ✓ goal created: <uuid>
▸ 2/4 Start (idle -> planning)
  ✓ status -> planning
▸ 3/4 Confirm plan v1
  ✓ plan v1 -> active
▸ 4/4 Execute
  ✓ status=completed, completed=1, tokens=121
▸ Final Summary contract (V1.0-4 / V1.0-6d)
  ✓ all 7 final_summary fields present

✓ V1.0-7 e2e demo PASSED
```

What the demo verifies:

1. **Backend health** is up.
2. **POST /goals** creates a Goal and returns its `goal_id`.
3. **POST /goals/{id}/start** transitions Goal to `planning`.
4. **POST /goals/{id}/plans/1/confirm** activates the plan.
5. **POST /runtime/execute/{id}** runs the worker loop, transitions to
   `completed`, returns tokens consumed.
6. **GET /runtime/status/{id}** returns a `final_summary` with all 7
   V1.0-4 / V1.0-6d contract fields (completed / incomplete / quality /
   risks / models / handoff_count / cost).

## 4. Tear down

```bash
docker compose -f docker-compose.dev.yml down          # keep data
docker compose -f docker-compose.dev.yml down -v       # also wipe SQLite
```

## 5. Real Provider mode (optional)

The same `docker-compose.dev.yml` works with a real Provider key:

```bash
PROVIDER_API_BASE=https://api.openai.com/v1 \
PROVIDER_API_KEY=sk-... \
PLANNER_MODEL_NAME=gpt-4o \
WORKER_MODEL_NAME=gpt-4o \
VERIFIER_MODEL_NAME=gpt-4o \
docker compose -f docker-compose.dev.yml up -d --build
```

The runtime will refuse to start mock-fallback once a live model is
configured (per design §2.2 / runtime_service `_get_provider`); an
invalid key is the loudest possible failure.

## 6. What the e2e does NOT cover

This is a **smoke** test, not a full E2E suite. It validates:

- Service reachability, JSON contracts, basic state transitions,
  final_summary shape.

It does NOT validate:

- Streaming output (V1.0-2)
- SSE events (V1.0-2)
- Long-running goal recovery (V1.0-2 / V1.0-3.7)
- Handoff with real quota pressure (V1.1)
- WebSocket / live UI streaming (V1.0-2 → V1.0-2 SSE)

For those, the V1.0 test suite (`backend/tests/`, `frontend/tests/`)
is the canonical signal.
