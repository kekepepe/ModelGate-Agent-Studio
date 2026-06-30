# Agent Workspace Implementation Plan

> 生成日期：2026-06-30
> 依据：docs/prd/agent-workspace-prd.md、docs/stories/agent-workspace-stories.md、docs/tasks/agent-workspace-tasks.md、docs/ui/agent-workspace-ui-spec.md
> 开发标准：docs/dev/module-development-sop.md

---

## 1. 范围声明

### P0（MVP-A，本轮必须完成）

| Story | 说明 | 后端 | 前端 |
|-------|------|------|------|
| US-AW-01 | 输入 Goal 并启动任务 | POST /goals + start | GoalInputPanel + TopStatusBar |
| US-AW-02 | 实时观察 Task 状态变化 | GET /workspace/:goalId/state | TaskCard + TaskTree（含状态动画） |
| US-AW-03 | 查看 Task 详情和输出 | GET /tasks/:taskId | TaskDetailPanel |
| US-AW-04 | 查看 Agent Station 和 Worker 状态 | GET /workspace/:goalId/state | AgentStationCard + WorkerBadge |
| US-AW-05 | 查看执行日志 | 复用已有 GET /logs | BottomConsole + ExecutionLogPanel（复用 Logs 模块组件） |
| US-AW-06 | Handoff 状态可视化 | 复用已有 GET /handoffs | TaskCard 集成 HandoffStatusIndicator（复用 Handoff 模块组件） |

### P1（延后）

| Story | 说明 |
|-------|------|
| US-AW-07 | 额度风险徽章展示（复用 Quota 模块 RiskBadge） |
| US-AW-08 | 模型路由决策展示（复用 Router 模块 RoutingResultCard） |

### 明确不做

- Goal/Task 的完整 Planning 引擎（用硬编码简化，创建 1 个初始 Task 给 Planner）
- E2E 工作流测试（AW-T7.3，最后执行）
- 拖拽式工作流编辑器
- 多人实时协作

---

## 2. 当前项目状态分析

### 已有可复用资源

| 模块 | 组件/API | 用途 |
|------|----------|------|
| Agent Registry | `GET /agents`、`AgentStation` model | AgentStationCard 数据源 |
| Model Router | `models` 表、`GET /router/rules` | WorkerBadge 模型名显示 |
| Handoff Manager | `HandoffStatusIndicator` 组件、`worker_sessions` 表、`handoff_records` 表 | Handoff 状态可视化、Worker 数据 |
| Quota Manager | `RiskBadge` 组件、`GET /quota/models/:id/status` | P1 额度风险徽章 |
| Logs | `LogListItem`、`LogFilters`、`GET /logs` | ExecutionLogPanel 集成 |

### 需要新增的数据表

| 表 | 说明 | 当前状态 |
|----|------|----------|
| `goals` | Goal 实体 | 不存在，需新建 |
| `tasks` | Task 实体 | 不存在，需新建（与 handoff_tasks 不同，后者是 Handoff 模块的 stub） |
| `worker_sessions` | Worker 实例 | **已存在**于 Handoff Manager，需扩展 `total_tokens_used` 字段 |

### 决策：复用 vs 新建 worker_sessions

当前 `worker_sessions` 表（Handoff Manager 004 migration）已包含：id, agent_id, model_id, goal_id, task_id, inherited_from_handoff_id, status, current_context, final_output, error_message, created_at, updated_at。

需要新增字段：`total_tokens_used`。使用 **ALTER TABLE ADD COLUMN**（SQLite 支持），不重建表。

---

## 3. 文件变更清单

### 3.1 新增文件

#### 后端

| 文件 | 说明 |
|------|------|
| `backend/migrations/006_create_goals_tasks.sql` | 创建 goals + tasks 表，扩展 worker_sessions |
| `backend/src/models/workspace.py` | Goal、Task SQLAlchemy 模型 |
| `backend/src/schemas/workspace.py` | Goal/Task Pydantic schemas + WorkspaceState 聚合 |
| `backend/src/services/goal_service.py` | Goal 创建、启动、状态流转 |
| `backend/src/services/task_service.py` | Task 查询、详情 |
| `backend/src/services/workspace_service.py` | Workspace 状态聚合 |
| `backend/src/routes/goals.py` | POST /goals、POST /goals/:id/start |
| `backend/src/routes/tasks.py` | GET /tasks/:id |
| `backend/src/routes/workspace.py` | GET /workspace/:goalId/state |
| `backend/tests/test_workspace_api.py` | API 集成测试 |

#### 前端

| 文件 | 说明 |
|------|------|
| `frontend/src/types/workspace.ts` | Goal、Task、WorkspaceState 等 TypeScript 类型 |
| `frontend/src/api/workspace.ts` | API 封装 |
| `frontend/src/hooks/useWorkspace.ts` | TanStack Query hooks + 轮询 |
| `frontend/src/pages/WorkspacePage.tsx` | Workspace 主页面（三栏布局） |
| `frontend/src/components/GoalInputPanel.tsx` | 左侧 Goal 输入区 |
| `frontend/src/components/TopStatusBar.tsx` | 顶部状态栏 |
| `frontend/src/components/TaskCard.tsx` | Task 状态卡片（含动画） |
| `frontend/src/components/AgentStationCard.tsx` | Agent Station 卡片 |
| `frontend/src/components/WorkerBadge.tsx` | Worker 状态徽章 |
| `frontend/src/components/TaskTree.tsx` | 左侧任务树 |
| `frontend/src/components/TaskDetailPanel.tsx` | 右侧 Task 详情面板 |
| `frontend/src/components/BottomConsole.tsx` | 底部日志控制台（集成 Logs 模块） |
| `frontend/src/styles/animations.css` | 状态动画 keyframes |
| `frontend/src/components/__tests__/GoalInputPanel.test.tsx` | |
| `frontend/src/components/__tests__/TopStatusBar.test.tsx` | |
| `frontend/src/components/__tests__/TaskCard.test.tsx` | |
| `frontend/src/components/__tests__/AgentStationCard.test.tsx` | |
| `frontend/src/components/__tests__/WorkerBadge.test.tsx` | |
| `frontend/src/components/__tests__/TaskTree.test.tsx` | |
| `frontend/src/components/__tests__/TaskDetailPanel.test.tsx` | |
| `frontend/src/components/__tests__/BottomConsole.test.tsx` | |

### 3.2 修改文件

| 文件 | 修改内容 |
|------|----------|
| `backend/src/models/handoff.py` | `WorkerSession` 新增 `total_tokens_used` 列 |
| `backend/src/main.py` | 注册 goals/tasks/workspace 路由 |
| `frontend/src/App.tsx` | 新增 `/workspace` 路由和导航链接 |

---

## 4. 数据模型

### Goal

```python
id: str (UUID PK)
title: str (required, max 255)
description: str (optional)
status: str (default "idle")  # idle/planning/running/waiting/handoff/reviewing/completed/failed
created_at: datetime
updated_at: datetime
```

### Task

```python
id: str (UUID PK)
goal_id: str (FK -> goals.id)
title: str (required)
description: str (optional)
status: str (default "pending")  # pending/assigned/running/completed/failed/handoff
assigned_agent_id: str (nullable, FK -> agent_stations.id)
assigned_worker_id: str (nullable)
output: str (nullable)
tokens_used: int (default 0)
duration_ms: int (nullable)
priority: int (default 0)
created_at: datetime
updated_at: datetime
```

### WorkerSession 扩展

```python
# 在现有 worker_sessions 表上新增：
total_tokens_used: int (default 0)
```

---

## 5. API 设计

### 5.1 POST /goals

- 请求：`{ title: str, description?: str }`
- 响应：`{ goal_id: str, status: "idle" }`

### 5.2 POST /goals/:goalId/start

- 逻辑：校验 goal.status=idle → 更新为 planning → 创建 1 个初始 Task（分配给 Planner Agent）→ 返回 goal 状态
- 响应：`{ goal_id: str, status: "planning" }`
- 错误：404（Goal 不存在）、400（非 idle 状态）

### 5.3 GET /tasks/:taskId

- 响应：完整 Task + agent_name + agent_role + model_name + worker_status

### 5.4 GET /workspace/:goalId/state

- 聚合接口，返回：`{ goal: Goal, tasks: Task[], agents: AgentStation[], workers: WorkerSession[] }`
- 供前端 2 秒轮询使用

---

## 6. 前端布局

```
┌──────────────────────────────────────────────────────────┐
│ TopStatusBar (Goal 名称、状态、进度、统计)                │
├──────────┬────────────────────────┬──────────────────────┤
│ 左侧 280px│ 中间 弹性               │ 右侧 360px            │
│          │                        │                      │
│ GoalInput│ AgentStationBoard      │ TaskDetailPanel      │
│ Panel    │ ┌──────────────────┐   │ (点击 TaskCard 展开)  │
│          │ │ AgentStationCard │   │                      │
│ TaskTree │ │ ┌──────────────┐ │   │ Tab: Overview/Task/  │
│          │ │ │ TaskCard     │ │   │       Context/Logs   │
│          │ │ │ TaskCard     │ │   │                      │
│          │ │ │ TaskCard     │ │   │                      │
│          │ │ └──────────────┘ │   │                      │
│          │ │ AgentStationCard │   │                      │
│          │ │ ...              │   │                      │
│          │ └──────────────────┘   │                      │
├──────────┴────────────────────────┴──────────────────────┤
│ BottomConsole (可展开/收起)                               │
│ 收起: "运行中 · 3 次模型调用 · 5 个 Task · 1 次 Handoff"  │
│ 展开: ExecutionLogPanel (复用 Logs 模块)                  │
└──────────────────────────────────────────────────────────┘
```

---

## 7. 开发顺序

### Phase 1 — 数据模型 + 后端 API（Round 2）

1. Migration 006: goals + tasks 表 + worker_sessions 扩展
2. Model: `backend/src/models/workspace.py`
3. Schema: `backend/src/schemas/workspace.py`
4. Services: goal_service + task_service + workspace_service
5. Routes: goals + tasks + workspace
6. Update main.py
7. Backend tests

### Phase 2 — 前端组件（Round 3）

1. Types: `frontend/src/types/workspace.ts`
2. API: `frontend/src/api/workspace.ts`
3. Hooks: `frontend/src/hooks/useWorkspace.ts`
4. Animations: `frontend/src/styles/animations.css`
5. Components:
   - TopStatusBar → GoalInputPanel → TaskCard → AgentStationCard → WorkerBadge → TaskTree → TaskDetailPanel → BottomConsole
6. Page: WorkspacePage（整合三栏布局）
7. Update App.tsx

### Phase 3 — 数据对接 + 集成（Round 3 后续）

1. useWorkspaceState hook 轮询对接
2. BottomConsole 集成 LogListItem 组件
3. TaskCard 集成 HandoffStatusIndicator

---

## 8. 复用策略

| 依赖 | 复用方式 |
|------|----------|
| AgentStation 列表 | 查询已有 `agent_stations` 表 |
| WorkerBadge 模型 | 查询已有 `worker_sessions` 表 + `models` 表 |
| ExecutionLogPanel | 复用 `LogListItem` + `LogFilters` 组件 |
| HandoffStatusIndicator | 复用 `HandoffStatusIndicator` 组件，传入 handoff_id |
| RiskBadge (P1) | 复用 `RiskBadge` 组件，传入 model_id |
| RoutingResultCard (P1) | 复用 `RoutingResultCard` 组件 |

---

## 9. 风险点

| 风险 | 应对 |
|------|------|
| worker_sessions 表已存在但缺少字段 | 新建 migration 006，ALTER TABLE ADD COLUMN total_tokens_used |
| handoff_tasks 与 tasks 表概念重叠 | tasks 作为正规 Task 表，handoff_tasks 保留给 Handoff 模块内部 stub |
| Workspace 多组件动画同时触发性能 | 仅使用 CSS transform/opacity 动画，React.memo 包裹卡片 |
| ExecutionLogPanel 依赖 Logs 模块组件 | Logs 模块已完成，直接 import 复用 |
| Agent 数量可能为空导致页面空白 | Workspace 以 Task 为中心展示，Agent Station Board 显示所有已注册 Agent |

---

## 10. 验收检查单（Round 5 审计用）

- [ ] `POST /goals` 创建 Goal 返回 201
- [ ] `POST /goals/:id/start` 启动后 status=planning，自动创建 Task
- [ ] `GET /tasks/:id` 返回完整 Task + 关联 Agent/Worker 信息
- [ ] `GET /workspace/:goalId/state` 返回 goal + tasks + agents + workers
- [ ] Workspace 页面三栏布局正确，`/workspace` 可访问
- [ ] GoalInputPanel 空输入禁用按钮
- [ ] TopStatusBar 8 种 GoalStatus 颜色正确
- [ ] TaskCard 5 种状态边框/颜色/图标/动画正确
- [ ] WorkerBadge 5 种状态灯颜色 + running 呼吸动画
- [ ] TaskTree 层级展示 + 状态图标同步
- [ ] TaskDetailPanel Tab 切换 + 输出复制
- [ ] BottomConsole 展开/收起 + ExecutionLogPanel 渲染
- [ ] TaskCard 集成 HandoffStatusIndicator（handoff 状态时可见）
- [ ] 前端构建通过 + 类型检查通过
- [ ] 后端测试全部通过
- [ ] 前端组件测试全部通过
