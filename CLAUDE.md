# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ModelGate Agent Studio is a multi-model agent collaboration platform. It organizes different LLMs into role-based agent teams (Planner, Coder, Reviewer, Research, Summarizer, Supervisor) and coordinates them through task decomposition, model routing, quota-aware scheduling, and structured handoffs.

The project is split into:
- **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS v4 + React Router + TanStack Query
- **Backend**: Python 3 + FastAPI + SQLAlchemy + SQLite

## Common Commands

### Frontend

```bash
cd frontend

# Development server (Vite, port 5173)
npm run dev

# Production build
npm run build

# Run all tests (Vitest)
npm run test

# Run tests in watch mode
npm run test:watch

# Run a single test file
npx vitest run src/components/__tests__/AgentList.test.tsx

# Lint (oxlint)
npm run lint
```

### Backend

```bash
cd backend

# Run the API server (uvicorn, port 8000)
./.venv/bin/python -m uvicorn src.main:app --reload

# Run tests (pytest)
./.venv/bin/python -m pytest tests/ -v

# Run a single test file
./.venv/bin/python -m pytest tests/test_agents_api.py -v

# Run a single test
./.venv/bin/python -m pytest tests/test_agents_api.py::TestCreateAgent::test_create_agent_success -v
```

## Architecture

### Module-Based Development

The project follows a strict 7-round module development SOP defined in `docs/dev/module-development-sop.md`. Each module has 4 specification documents:

```
docs/prd/{{module-slug}}-prd.md           # Product requirements
docs/stories/{{module-slug}}-stories.md   # User stories & acceptance criteria
docs/tasks/{{module-slug}}-tasks.md       # Implementation tasks
docs/ui/{{module-slug}}-ui-spec.md        # UI structure, states, interactions
```

Planned modules (in dependency order):
1. **Agent Registry** (completed) — Defines agent stations and role templates
2. **Model Router** — Model capability routing and recommendations
3. **Quota Manager** — Token/quota tracking and risk status
4. **Handoff Manager** — Structured task handoff with summary generation
5. **Logs / Observability** — Execution logging and tracing
6. **Agent Workspace** — Visual workspace with card-flow and pixel-office views

### Backend Structure

```
backend/src/
  main.py                 # FastAPI app, CORS, router registration
  core/
    config.py             # Settings (env-based, SQLite default)
    database.py           # SQLAlchemy engine, SessionLocal, Base, get_db()
  models/                 # SQLAlchemy ORM models
  schemas/                # Pydantic v2 request/response schemas
  services/               # Business logic layer
  routes/                 # FastAPI route handlers
  data/                   # Seed data, templates, fixtures

backend/tests/
  conftest.py             # pytest fixtures: TestClient, clean_database, db_session
```

**Key backend patterns:**
- Database: SQLite via SQLAlchemy 2.0, JSON lists stored as Text columns
- Tests use a separate `test.db` with `Base.metadata.drop_all` / `create_all` per test
- API prefix: `/api/v1`
- Unified response format: `{ success: boolean, data?: object, error?: { code, message } }`
- Error codes: `BAD_REQUEST`, `NOT_FOUND`, `CONFLICT`, `INTERNAL_ERROR`

### Frontend Structure

```
frontend/src/
  main.tsx                # React root, QueryClientProvider, BrowserRouter
  App.tsx                 # Routes (currently `/agents`)
  api/                    # Axios API clients per module
  hooks/                  # TanStack Query hooks per module
  types/                  # TypeScript interfaces per module
  pages/                  # Route-level page components
  components/             # Reusable components + __tests__/
```

**Key frontend patterns:**
- TanStack Query for server state (default: retry 1, refetchOnWindowFocus false)
- Axios base URL: `http://localhost:8000/api/v1`
- Tailwind v4 with `@theme` custom colors (`stone-*`, `lavender-*`, `brick-*`)
- Tests use `jsdom` with `@testing-library/react` and `vitest`
- All test renders must wrap with `QueryClientProvider`

### API Contract

The full API contract is in `docs/architecture/API-Contract.md`. Key conventions:
- Base URL: `http://localhost:8000/api/v1`
- Pagination: `?page=1&page_size=20`
- Paginated response wrapper: `{ items: [], total, page, page_size, total_pages }`
- Agent status enum: `idle | queued | running | waiting | reviewing | handoff | blocked | error | done`
- Valid agent roles: `planner | coder | reviewer | research | summarizer | supervisor`

### Design System

**Visual style** (from `docs/ui/UI状态与交互动效规则.md` and `frontend/src/index.css`):
- Low-saturation, non-dark, Claude-inspired aesthetic
- Background: `stone-50` (#fafaf9)
- Primary text: `stone-800` (#292524)
- Custom palette: stone, lavender, brick
- No complex animations in MVP; CSS transforms and opacity only

**Status colors** (must use consistently across modules):
- idle: gray (#9ca3af)
- running: blue (#3b82f6)
- handoff: purple (#8b5cf6)
- completed/done: green (#10b981)
- failed/error: red (#ef4444)
- waiting/pending: yellow (#fbbf24)

### Mock Data Boundaries

Due to dependent modules not yet implemented, the following mock data is intentionally hardcoded and must be replaced when the respective modules are ready:
- `MOCK_MODELS` in `frontend/src/types/agent.ts` — replace with Model Router `GET /models`
- `MOCK_TOOLS` in `frontend/src/types/agent.ts` — replace with MCP tool list API
- Agent templates in `backend/src/data/agent_templates.py` — migrate to DB if user customization is needed

### Database Schema

The authoritative schema reference is `docs/architecture/数据结构与数据库Schema.md`. It contains:
- All status enums (GoalStatus, TaskStatus, AgentStatus, WorkerStatus, HandoffStatus, QuotaStatus, etc.)
- Core data objects (Goal, Task, AgentStation, WorkerSession, Model, HandoffRecord, QuotaRecord, ExecutionLog)
- Object relationship diagram
- JSON field usage guidance
- Foreign key mapping

## Important Files for Context

| File | Purpose |
|------|---------|
| `docs/dev/module-development-sop.md` | The 7-round development SOP every module follows |
| `docs/architecture/API-Contract.md` | All API request/response formats |
| `docs/architecture/数据结构与数据库Schema.md` | Status enums, data objects, DB schema |
| `docs/dev/implementation-log.md` | Module completion logs |
| `frontend/src/index.css` | Tailwind theme config (custom colors) |
| `backend/tests/conftest.py` | Test fixtures and DB cleanup strategy |

## Development Notes

- **Linting**: Frontend uses `oxlint` (not ESLint). Config in `frontend/.oxlintrc.json`.
- **Python version**: Use `./.venv/bin/python` for all backend commands; system Python may lack pytest.
- **CORS**: Backend allows `http://localhost:5173` for frontend dev server.
- **Backend DB**: Default is `sqlite:///./modelgate.db`. Tests use `sqlite:///./test.db`.
- **Frontend build**: Runs `tsc -b && vite build`. Type errors block the build.
