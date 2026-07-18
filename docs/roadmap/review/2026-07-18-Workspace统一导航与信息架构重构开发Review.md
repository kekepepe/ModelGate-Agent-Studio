# 2026-07-18 Workspace 统一导航与信息架构重构开发 Review

> 对应计划：`docs/roadmap/2026-07-18-Workspace统一导航与信息架构重构开发计划.md`  
> Review 范围：P0–P7 前端信息架构、Run 聚合接口、状态恢复、跨模块关联与测试  
> Review 日期：2026-07-18  
> 结论：仓库级实现与自动化验收通过，建议合并

## 1. 完成结论

本轮已把原先封闭的 `/workspace?goal=...` 页面重构为统一 ModelGate App Shell 下的两层 Workspace：

```text
/workspace                    Run Overview
/workspace/runs/{runId}       Run Detail
```

Studio、Workspace、Assets、Evolution、Logs 与运行概览现在共享同一全局 Header。Run Detail 的团队、Goal、状态、Token/Quota 与 Pause/Resume/Stop/Export 已迁入独立 Run Header；Card Flow、Pixel Office、Task Tree、Plan、Handoff 与 Console Summary 保留原有真实数据链路。

## 2. Review 方法与逐阶段判定

本 Review 不仅根据页面效果判定完成，而是同时核对路由、API、后端状态机、组件测试、真实浏览器流程与 Docker 构建。判定标准为：代码已落地、关键用例有自动化证据、不破坏旧 Workspace 执行链路。

| 阶段 | 判定 | 主要证据 |
|---|---|---|
| P0 现状梳理与保护 | 完成 | 保留 Goal、Task Tree、Card Flow、Pixel Office、Handoff 与最终输出现有数据链路；原 Workspace E2E 无回归 |
| P1 统一 App Shell | 完成 | `AppShell` 与 `GlobalHeader` 被 Studio、Workspace、Assets、Evolution、Logs 共用，导航激活态有组件测试 |
| P2 Workspace 路由重构 | 完成 | `/workspace`、`/workspace/new`、`/workspace/runs/:runId` 落地；三类旧链接可重定向 |
| P3 Workspace Overview | 完成 | 真实 Run 聚合 API、分组、状态筛选、Goal 搜索、空状态和快速跳转已落地 |
| P4 Workspace Run Header | 完成 | Run 上下文与全局导航分离；Pause、Resume、Stop 确认、Export 及 Token/Quota 显示有测试 |
| P5 跨模块关联 | 完成 | Logs、Evolution、Assets 可传递 runId/goalId，并可返回当前 Run |
| P6 状态恢复与更新 | 完成 | 稳定 Run ID、URL 恢复、视图持久化、EventSource 重连与轮询兜底；规划态暂停/恢复已补齐 |
| P7 测试与回归 | 完成 | Backend、Frontend、Playwright、多视口、Docker build 与 `git diff --check` 均通过 |

## 3. 用户可见变化

1. Workspace 一级入口展示真实 Run 列表，并按 Active、Recent、Completed、Failed/Stopped 分组；支持状态筛选与 Goal 搜索。
2. 创建 Goal 时立即获得稳定 `run_id`，规划、执行、刷新和重新进入使用同一 URL。
3. Run Detail 始终保留 ModelGate 全局导航，并提供返回 Workspace、Studio 面包屑。
4. Card Flow / Pixel Office 使用 `?view=` 与 `workspace:view:{runId}` 持久化，刷新后恢复。
5. Workspace → Logs / Evolution / Assets 自动携带 runId/goalId；三个页面均提供返回当前 Workspace。
6. Stop 增加二次确认；Pause 在规划态、执行态和审查态按后端状态机执行；规划态 Resume 回到 planning。
7. Export 注册真实 `run_snapshot` Artifact，同时下载 JSON；运行中导出明确标记为快照。
8. 无效 Run 展示明确错误状态与重试、返回 Workspace、返回 Studio，不再落入空白页。

## 4. 路由变化

| 旧行为 | 新行为 |
|---|---|
| `/` 直接 Studio | `/` 重定向 `/studio` |
| `/workspace?team=...` 创建与运行混在一页 | `/workspace/new?team=...` 创建 Run |
| `/workspace?goal=...` 运行详情 | `/workspace/runs/{runId}` |
| Workspace 隐藏主导航 | 全部业务页复用 App Shell |
| 历史 `/workspace/{id}` 等失效 | 自动重定向并兼容 goalId 解析 |

完整说明见 `docs/architecture/Workspace统一导航路由与Run-API.md`。

## 5. API 与状态变化

新增：

```text
GET  /api/v1/runs
GET  /api/v1/runs/{runId}
GET  /api/v1/runs/{runId}/workspace
GET  /api/v1/runs/{runId}/assets
POST /api/v1/runs/{runId}/export
```

扩展：

- `POST /api/v1/goals` 与 Goal Start 响应增加 `run_id`。
- `GET /api/v1/logs` 支持 `run_id`。
- `GET /api/v1/knowledge/evolution` 支持 `run_id`。
- RuntimeRun 延迟创建，但复用 Goal 创建时分配的公开 Run ID。
- 状态机补齐 `planning → paused → planning` 与 `reviewing → paused`。

Run Overview 数据来自数据库聚合，不使用前端静态样例；包括状态、Task 进度、活跃 Agent、Token/Quota、Handoff、错误与 Artifact 数量。

## 6. 关键修改范围

### 前端

- `frontend/src/App.tsx`
- `frontend/src/components/app-shell/*`
- `frontend/src/components/workspace/*`
- `frontend/src/pages/WorkspaceOverviewPage.tsx`
- `frontend/src/pages/CreateRunPage.tsx`
- `frontend/src/pages/WorkspacePage.tsx`
- `frontend/src/pages/AssetsPage.tsx`
- `frontend/src/pages/LogsPage.tsx`
- `frontend/src/pages/EvolutionReviewPage.tsx`
- `frontend/src/api/runs.ts`、`frontend/src/hooks/useRuns.ts`

### 后端

- `backend/src/routes/workspace.py`
- `backend/src/services/workspace_service.py`
- `backend/src/services/goal_service.py`
- `backend/src/services/runtime_service.py`
- `backend/src/services/state_machine_service.py`
- Logs / Knowledge 路由与服务的 runId 解析

### 测试与文档

- `backend/tests/test_workspace_runs_api.py`
- GlobalHeader、WorkspaceRunHeader、Run 状态映射单元测试
- `frontend/e2e/smoke.spec.ts`
- `frontend/e2e/workspace-flow.spec.ts`
- Workspace 路由与 API 架构说明、文档索引

## 7. 验收证据

| Gate | 结果 |
|---|---|
| Backend 全量测试 | `398 passed, 1 skipped` |
| Frontend 单元/组件测试 | `36 files, 175 passed` |
| Frontend lint | 通过，无 warning |
| Frontend production build | 通过 |
| Playwright 全套多视口 | `9 passed, 15 intentionally skipped` |
| Workspace 1440 核心流程 | 4/4 通过 |
| Docker Compose build | backend、frontend images 均 Built |
| `git diff --check` | 通过 |

Playwright 覆盖：Studio 创建 Run、稳定 URL、统一导航、Overview 返回、离开不停止、刷新恢复、Card/Pixel 持久化、Logs/Evolution/Assets 上下文、规划态 Pause/Resume、Stop 确认、无效 Run、100 Task DAG 与完成态输出。响应式 smoke 在 1280、1440、1920 和小屏项目运行。

应用内 Browser 插件在本次环境返回 `No browser is available`，因此按计划中的 Playwright 要求回退至仓库自带 Playwright。该限制只影响浏览器控制入口，不影响真实 Chromium E2E 结果。

## 8. QA 中发现并修复的问题

1. 新导航导致旧 smoke 定位同时匹配品牌、主导航与 CTA；测试已改为精确可访问名称。
2. 规划态 Pause UI 可用，但后端状态机最初缺少 `planning → paused`；已补齐并增加真实 E2E。
3. Global Header 的 Evolution 链接最初只携带 runId；现通过 Run summary 补齐 goalId。
4. Run Not Found 容器在 flex shell 下横向收缩；已补 `w-full` 并重新截图验证居中。
5. QA 后端若从 `backend/` 启动会把该目录误作 Workspace Root，Knowledge Source 的根 README 测试返回 400；最终全套 E2E 使用仓库根 `WORKSPACE_ROOT`，9 个实际执行用例全部通过。

## 9. 边界与剩余风险

- 本轮没有重写 Runtime、Planner、Router、Handoff 或 Supervisor 算法。
- EventSource 使用浏览器原生重连，轮询作为恢复兜底；未新增 WebSocket。
- 旧 Goal 没有预分配 runId 时仍可用 goalId 旧链接打开；首次执行后 Runtime 会创建正式 runId。
- `/handoffs` 旧路由仍作为兼容/调试入口保留，但已从主产品导航移除；用户主流程中的 Handoff 仍属于 Workspace Task 内操作。
- 小屏项目用于 smoke；计划非目标明确不要求完整移动端体验。
- Playwright 运行产生的截图、视频和 trace 位于 gitignore 的 `frontend/test-results/`，不作为源码提交。

## 10. Review Findings

| 级别 | 数量 | 结论 |
|---|---:|---|
| Blocker / Critical | 0 | 未发现会导致 Workspace 主流程不可用、数据丢失或无法恢复的问题 |
| Major | 0 | 稳定路由、Run API、运行控制和跨页上下文已经闭环 |
| Minor | 0 | QA 中发现的定位、状态机、链接上下文和错误页宽度问题均已修复 |
| Observation | 4 | EventSource/轮询策略、旧 Goal 兼容、旧 Handoff 路由和完整移动端适配属于已记录的非阻塞边界 |

从代码结构看，本轮将全局导航、Run 上下文、业务视图和后端聚合的职责分开，没有把新逻辑继续堆入单一 `WorkspacePage`。从产品逻辑看，Workspace 已经从“某个 Goal 的封闭执行页”转为“可浏览、可返回、可恢复的一级运行模块”。

## 11. Go / No-Go

**仓库合并：Go。** 路由、API、状态机、组件、构建、Docker 与多视口自动化证据一致，未发现本轮范围内的原则性 blocker。

合并后建议只做运行观察：关注旧 Workspace URL 重定向命中率、Run Overview 在大数据量下的聚合耗时，以及 EventSource 重连频率。这些不影响本轮上线判定。
