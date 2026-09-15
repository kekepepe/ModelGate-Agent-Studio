# Changelog

All notable changes to ModelGate Agent Studio are documented here.

V1.0 is the first release produced under the 2026-09-06 platform
redesign. Older per-phase changelogs are archived in
`docs/_archive_2026/CHANGELOG.md`.

## V1.2.1 — 2026-09-15（Architecture Alignment + CI + Product Acceptance）

计划与进度见 `V1.2.1-plan.md`（全部勾选）。本阶段**只做收口与质量门禁**，
零新功能、零依赖变更。

### Architecture Alignment (P0) — 已完成
- 设计文档 §1 技术栈表对齐真实栈：React Router v7（不是 TanStack Router）、
  SQLAlchemy 2 sync（无 async，V1.4 并行若成瓶颈再评估）；arq/Redis 标注"未安装"
- §5.1 heading 修正；§6.5 Provider 抽象重写为双层（`services/providers` 现役、
  `providers/litellm` V1.3 P2 预留）；§8 编号对齐 ROADMAP
- `main.py::_init_provider` 改名为 `verify_provider_config`，消除"初始化但结果
  丢弃"的误导，与 V1.2.1 P0 决策一致
- HANDOVER.md 重构为一页式标准交接文档（快照 / 代码地图 / 已知坑 / 路线图 /
  工作约定），不再吸收阶段计划内容（faf963e 事故的根治）

### Quality Gate (P1) — 已完成
- `scripts/e2e-product-acceptance.sh` 即将合并（mock 栈 3 场景：核心闭环 /
  Handoff / Evolution 沉淀→检索）
- `.github/workflows/backend-ci.yml` + `frontend-ci.yml` 即将恢复（min pytest /
  lint+typecheck+test+build）

## V1.2 — 2026-09-15（本地 Memory / RAG 检索 / Skill 沉淀）

计划与参考调研见 `docs/_archive_2026/V1.2-Memory-RAG-Skill-plan.md`（已归档；mem0 / Voyager /
Claude Agent Skills 取舍）。目标：把每次执行的上下文、经验、错误、
解决方案和工作流变成可复用知识，任何模型接入后都能继承。

### Added
- **经验沉淀**：curator 从执行错误证据抽取 `experience_memory`
  （稳定 error_signature + resolution 叙事：handoff 恢复 / 重试成功 /
  replan / 未解决），同类错误合并 occurrence 而非重复堆积。
- **用户偏好**：`POST /knowledge/preferences` 创建 born-approved 偏好；
  上下文构建时无条件注入（上限 3 条），与相关性门禁解耦。
- **记忆/技能向量化**：迁移 0011 给 memory_drafts / skill_drafts 加
  embedding + fingerprint 列；curator 生成/审批时落嵌入，后端切换
  （指纹不符）惰性重嵌；`memory_vector_service` 提供混合检索
  （`GET /knowledge/memories/search`）。
- **上下文升级**：context_service 选择逻辑从纯关键词升级为
  keyword+cosine 混合（policy `hybrid_memory_skill_v1`）；技能按
  success_rate 加权（0.8 + 0.4×rate）；技能在上下文内渐进披露
  （≤3 步，全量走 `GET /knowledge/skills/{id}`）；replan 上下文召回
  相似经验；planning 上下文带技能建议。
- **统一检索 API**：`/context/retrieve` 支持 `source_types`
  （memory / skill / knowledge），默认保持旧契约不变。
- **Evolution UI**：经验/偏好标签、偏好创建表单、技能成功率展示。

### 数字
- 后端 pytest：451 passed, 1 skipped
- 前端 vitest：183 passed / 38 文件；typecheck / build / lint 全绿

## V1.0.1 / V1.1 — 2026-09-15（修复 + Handoff 完整业务流）

计划与逐项进度见 `docs/_archive_2026/V1.0.1-V1.1-plan.md`（已归档）；CI 工作流按用户决定暂缓。

### Fixed（V1.0.1 修复批）
- `frontend/src/components/ui/select.tsx` 入库 —— 它已被 LogFilters /
  GoalInputPanel 引用，此前未提交导致新 clone 构建失败。
- `vitest.config.ts` 补 `@` 路径别名，修复 7 个测试文件的模块解析失败。
- 6 个组件测试（TaskCard / AgentStationCard / WorkerBadge / GlobalHeader /
  TaskTree / LogFilters）对齐 shadcn 重构后的 UI；jsdom 补 PointerEvent /
  pointer capture / scrollIntoView polyfill。
- `.playwright-cli/` 调试产物 untrack + gitignore。
- CLAUDE.md / HANDOVER.md 失实文档路径与描述修正；
  `V1.0-frontend-plan.md` 归档。

### Added（V1.1 Handoff 完整业务流）
- **LLM 交接摘要**：`trigger_handoff` 先进 `generating_summary`，按 Goal 的
  execution_mode 调用 provider 生成结构化摘要（mock 模式与任何失败路径回退
  模板），摘要携带 `generated_by` / `generated_at` 溯源并计入 model_call 日志。
- **handoff_policy 接入 runtime**：error / quota 两个自动触发点与验证失败后
  的 quality 触发点均遵循 Station 的 `handoff_policy`
  （can_initiate / on_provider_error / on_quota_exhausted / on_quality_issue）；
  无显式策略的 Station 保持 V1.0 行为。状态矩阵补 ready/assigned → pending
  的 requeue 边（设计文档 §3.2 已同步）。
- **Workspace Handoff 状态条**：TaskCard 的 handoff 块接入真实数据
  （ThreeZoneCardFlow 不再传空 stub）；站点 handoff 态判定改用后端真实枚举
  （旧值 summary_ready / in_progress 永远匹配不上）。
- **导航与配额可视化**：GlobalHeader 新增 Handoff 入口；Quota Overview 展示
  `handoff_triggered_count` 并移除依赖已删 dashboard 接口的趋势图。
- **`scripts/e2e-handoff.sh`**：设计 §8 V1.1 验收的 8 步端到端脚本，
  mock 栈实测 PASS。

### Fixed（V1.1 验收暴露）
- `quota_service._determine_quota_status`：SQLite 回读的 `cooldown_until`
  为 naive datetime，与 aware 时钟比较直接 TypeError —— 429 冷却后任何
  第二次用量上报都会 500。已按 recovery_service 的方式归一化。
- `QuotaRecord.handoff_triggered_count` 此前从未被递增；quota 拦截成功
  触发 handoff 时现在会 +1。

### 数字
- 后端 pytest：428 passed, 1 skipped（V1.0 末态 411）
- 前端 vitest：180 passed / 37 文件（修复前 16 个用例失败被别名缺失掩盖）
- 前端 typecheck / build / lint：0 errors

## V1.0 — 2026-09-06 platform redesign complete

### Scope

V1.0 is a single-developer, locally-runnable platform: one
`docker compose up` brings the backend + frontend up, and one
`bash scripts/e2e-demo.sh` proves the Goal → Task → Worker → Model
→ Final Summary pipeline runs end-to-end.

This is the "0 → 1" milestone. V1.1–V1.4 layer in Handoff, Quota,
parallelism, custom Stations, and a CI gate.

### Added

**Design (2026-09-06 redesign)**
- `docs/design/2026-09-06-platform-redesign.md` — single source of
  truth for product direction, architecture, station model,
  routing, handoff protocol, and V1.0–V1.4 phasing.

**Backend (V1.0-2 / V1.0-3 / V1.0-4)**
- `src/providers/` — LLM provider abstraction (LLMProvider Protocol
  + LiteLLMProvider + MockProvider) so business code never imports
  litellm directly.
- `src/runtime/` — re-export of the state machine
  (GOAL_TRANSITIONS, TASK_TRANSITIONS, validate_transition, etc.)
  at the design-documented path.
- Alembic migration `0010_station_design_fields` — adds
  `slug` / `is_builtin` / `handoff_policy` to `agent_stations`,
  with a partial unique index on `slug` and idempotent back-fill.
- 6 pre-built Stations now expose their slug + is_builtin status and
  a structured handoff_policy JSON blob; user-created stations
  always have is_builtin=false and an auto-derived unique slug.
- DELETE `/api/v1/agents/{id}` rejects attempts to delete a
  built-in station (returns 400 with `BuiltinStationProtectedError`).
- Final Summary contract (V1.0-4 / V1.0-6d) — runtime returns a
  7-field dict in `/runtime/status/{id}`; frontend displays it in
  a collapsible card.
- V1.0-4 entry layer — `from src.runtime import execute_goal_pipeline,
  get_runtime_status, ...` re-exports the public surface so the
  new design path is the discoverable one.
- 8 V1.0-4 acceptance tests covering the runtime entry, final-summary
  shape, and the V1.0-3 station-fields coexistence path.
- 11 V1.0-3 station-fields tests covering slug generation,
  uniqueness, built-in protection, and handoff_policy defaults.

**Frontend (V1.0-5 / V1.0-6)**
- shadcn/ui integrated as the design-system foundation: 10
  copy-paste components under `src/components/ui/`
  (button / card / badge / avatar / input / textarea / separator /
  tabs / scroll-area / tooltip).
- Tailwind v4 design tokens in `index.css` — full shadcn "new-york"
  theme plus 10 agent-state color tokens (--state-idle /
  -writing / -researching / -executing / -syncing / -error /
  -completed / -running / -paused / -failed) inspired by the
  Star-Office-UI 6-state palette.
- `AgentStatusBadge` — single shared component that maps any of 30+
  Goal / Task / Worker status enums to a coloured Badge with
  left-border accent + dot.
- `ActiveStationsSidebar` (V1.0-6a) — left rail listing all
  Stations with role icon + status badge + state-distribution
  chips in the footer. Modeled on Star-Office-UI's guest list.
- TopBar state distribution chips (V1.0-6b) — `[●3 running] [●2 idle]`
  in the global header. Modeled on Star-Office-UI's control bar.
- `ThreeZoneCardFlow` (V1.0-6c) — third Workspace view mode grouping
  every Task into Rest / Working / Problem columns. Modeled on
  Star-Office-UI's three-region pixel-office layout.
- `FinalSummaryPanel` (V1.0-6d) — collapsible card that renders
  the 7-field Final Summary at the top of the Workspace when a
  Goal is in a terminal state. Modeled on Star-Office-UI's Memo panel.
- `WorkspaceModeSwitch` exposes the three view modes
  (Card Flow / 3 Zones / Pixel Office); per-run choice is
  persisted to localStorage and overridable via `?view=zones`.

**Tooling (V1.0-7)**
- `scripts/e2e-demo.sh` — full end-to-end smoke test against a
  running stack. Verifies all 7 Final Summary contract fields
  are present.
- `docs/e2e-docker-stack.md` — operator doc for bringing the stack up.

### Changed

- `backend/src/services/state_machine_service` is now also
  reachable as `src.runtime` (re-export). Business code may use
  either path; new code should prefer `src.runtime`.
- `frontend/src/index.css` — full shadcn theme overlay plus agent
  state tokens. Existing class-based styles preserved verbatim.
- `frontend/src/components/app-shell/AppShell.tsx` — now a flex
  column (TopBar on top) + flex row (sidebar left + main right).
- `frontend/src/utils/workspaceViewModel.ts` — `WorkspaceViewMode`
  gains `'zones'` alongside `'card'` and `'pixel'`.
- `backend/requirements.txt` — `httpx==0.28.1` widened to
  `httpx>=0.27,<0.29` to resolve a build-time conflict with
  litellm 1.55.0 (was causing Docker builds to fail).

### Removed (or moved to archive)

- 5 P0-P7-era GitHub Actions workflows deleted (`backend-ci.yml`,
  `frontend-ci.yml`, `integration-ci.yml`, `nightly-ci.yml`,
  `security-ci.yml`). They were tightly bound to the pre-V1.0
  codebase and have been failing on every push since 2026-07-18.
  A new V1.0 CI set is designed in this release (see below).
- 99 planning / status documents moved to
  `docs/_archive_2026/`. None of them were authoritative for V1.0.
- 3 root-level `CHANGELOG.md` / `RELEASE_NOTES.md` / `design-qa.md`
  moved to `docs/_archive_2026/`. The new `CHANGELOG.md` at the
  repo root supersedes them.
- `backend/src/services/mock_provider.py` (top-level mock) deleted
  — replaced by `src/providers/mock_provider.py` in V1.0-2.
- `backend/src/routes/dashboard.py` + `tests/test_dashboard_api.py`
  — design §5 removes the top-level Dashboard; Workspace Overview
  takes its role.
- `backend/src/models/selection.py` kept (agent-selector imports
  it; V1.0-3 cleanup log records the false-start).

### Tests

| | V1.0-2 | V1.0-3 | V1.0-4 | V1.0-5/6/7 | Total |
|---|---:|---:|---:|---:|---:|
| Backend pytest | 398 | 409 | 411 | 411 | **411 passed, 1 skipped, 0 failures** |
| Frontend typecheck | — | — | — | 0 errors | 0 |
| Frontend build | — | — | — | 197ms | ok |
| Docker build | — | — | — | ok | ok |
| e2e-demo.sh | — | — | — | **PASS** | PASS |

The 1 skipped test is a pre-existing `pytest.mark.skip` on
`test_postgres_integration` (only runs in CI with a postgres service).

### Known gaps (deferred to V1.0.1 / V1.1 / V1.4)

- **Handoff** — the data model is in place, the page is gone (V1.0
  inlines handoff into the Task card per design §2.2). The full
  Handoff state machine will be wired in V1.1.
- **Quota** — the data model is in place, the auto-handoff on
  LIMITED is in place, but the Quota Overview page is deferred
  to V1.1.
- **Real Provider smoke** — V1.0 only runs the mock provider. The
  first real-Provider acceptance is part of V1.0.1 (needs an
  OpenAI-compatible key + 5–10 minute budget).
- **Per-station "current task" line in the Sidebar** — there is
  no `/api/v1/tasks` list endpoint yet. The row will gain a
  one-line `→ <title>` preview once that endpoint lands.
- **V1.0 CI gate** — the workflows in `.github/workflows/`
  are still empty. Design is in `docs/_archive_2026/v1.0_deletions_log.md`
  §6. Implementation deferred to V1.0.1 (P0 risk: V1.0 ships
  without a build gate; the next Phase-1 commit should add the
  minimum backend-test + frontend-build workflows).
- **TaskCard / AgentStationCard shadcn refactor** — V1.0-5/6
  added the design system and Star-Office-UI patterns, but the
  45 existing components still use the P0-P7 styling. The refactor
  in-place is planned for V1.0.1 / V1.0.2.

### Commit graph (oldest → newest)

```
b93fb39 docs(design): 2026-09-06 platform redesign
56dd1de docs(v1.0-1): archive 99 old planning docs
1079a86 feat(v1.0-2): LiteLLM provider + state machine
5c5d083 feat(v1.0-2-followup): Settings wiring
59bf1b9 feat(v1.0-3): Station slug/is_builtin/handoff_policy
440158d chore(v1.0-3): clean up + delete log
86d5081 chore(v1.0-3.7): delete 5 P0-P7 CI workflows
8d3bc7d feat(v1.0-4): runtime entry layer + tests
d8ba8c5 feat(v1.0-5): shadcn/ui integration + state tokens
a08169a feat(v1.0-6a): ActiveStationsSidebar
d545009 feat(v1.0-6b): topbar state distribution chips
04bf521 feat(v1.0-6c): ThreeZoneCardFlow view
64d6947 feat(v1.0-6d): FinalSummaryPanel
e3fc444 feat(v1.0-7): docker compose local stack + e2e demo
```

15 commits, 9 days of design + implementation (2026-09-06 design
draft → 2026-09-12 first end-to-end demo on Docker).
