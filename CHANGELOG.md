# Changelog

All notable changes to ModelGate Agent Studio are documented here.

## Unreleased RC candidate — 2026-07-18

### Added

- Reproducible backend, frontend, integration, and security GitHub Actions workflows.
- Alembic revision chain `0001` through `0008`, including runtime recovery and worktree audit state.
- OpenAI-compatible live Provider configuration, error taxonomy, stream validation, and role-to-model mapping.
- Runtime state transition guards, transactional replan/handoff behavior, lease recovery, and idempotency controls.
- Real Worktree isolation, merge/conflict evidence, capacity downgrade, Playwright core flows, and 100-task UI regression.
- RAG evaluation dataset, embedding adapters, scoped candidate retrieval, and quality/latency report.
- Workspace/path/shell/prompt-injection/secret controls, fault injection suite, request-boundary protections, and dependency VEX.
- PostgreSQL load baseline for 1000 tasks, 500 logs, and 50 concurrent requests.

### Changed

- Live execution is the default; Mock is explicit test/demo mode.
- Provider credentials are environment-only and cannot be written through Model APIs or the frontend.
- Docker, Python, Node, Playwright, PostgreSQL, and dependency versions are pinned for CI reproducibility.

### Known release blockers

- Six live-provider E2E scenarios and five-run three-mode Multi-Agent benchmark require a real Provider key.
- GitHub branch protection, hosted Checks, and the GitHub Gitleaks action require repository administration/CI execution.
- A compatible fixed Starlette/Click dependency set is not available from the configured package index; exact VEX controls apply.
- No RC Git tag or image tag is created while these gates remain open.

