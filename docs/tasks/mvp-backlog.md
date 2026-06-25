# ModelGate Agent Studio — MVP 开发 Backlog

> 整合自 6 个模块任务文件，仅保留 P0 任务，按 Sprint 编排以优先实现可演示闭环。
>
> 生成时间：2026-06-25

---

## 1. 概览

### 1.1 模块与任务来源

| 模块 | 来源文件 | P0 任务数 |
|------|---------|----------|
| Agent Registry | `docs/tasks/agent-registry-tasks.md` | 15 |
| Model Router | `docs/tasks/model-router-tasks.md` | 15 |
| Quota Manager | `docs/tasks/quota-manager-tasks.md` | 18 |
| Handoff Manager | `docs/tasks/handoff-manager-tasks.md` | 20 |
| Logs / Observability | `docs/tasks/logs-observability-tasks.md` | 14 |
| Agent Workspace | `docs/tasks/agent-workspace-tasks.md` | 20 |
| **合计** | — | **102** |

### 1.2 Sprint 目标与交付物

| Sprint | 主题 | 核心交付物 |
|--------|------|-----------|
| **Sprint 0** | 基础设施 + 核心后端 API | 全部数据表就绪，各模块核心 API 可返回 200，可通过 HTTP 工具独立验证 |
| **Sprint 1** | 前端骨架 + 功能后端补全 | Workspace / Registry / Logs / Quota 页面可运行（mock 数据），Handoff Accept、完整路由评分、自动拦截等后端功能就绪 |
| **Sprint 2** | 真实数据对接 + 手动闭环 | 用户可完整演示：创建 Goal → Task 运行 → 实时日志 → 手动触发 Handoff → 接受交接 → Task 恢复运行 |
| **Sprint 3** | 自动 Handoff + E2E + 打磨 | 额度 LIMITED 自动触发 Handoff 并在 Workspace 展示，全部 E2E 测试通过 |

### 1.3 跨模块依赖总览

```
Agent Registry (AR)
  └── 被依赖：Workspace (AgentStation), Model Router (候选 Agent), Handoff (from/to Agent)

Model Router (MR)
  └── 依赖：AR (Agent 角色), Quota (额度状态过滤)
  └── 被依赖：Workspace (RoutingResultCard), Quota (auto-handoff 选备用模型)

Quota Manager (QM)
  └── 依赖：MR (选备用模型), Logs (记录额度事件)
  └── 被依赖：Workspace (RiskBadge, 预警条), Handoff (LIMITED 触发 auto-handoff)

Handoff Manager (HM)
  └── 依赖：AR (Agent), Workspace (Task/Worker), Logs (记录 Handoff 事件), MR (accept 时可选模型)
  └── 被依赖：Workspace (HandoffStatusIndicator)

Logs / Observability (LO)
  └── 被依赖：ALL 模块（统一写入执行日志）

Agent Workspace (AW)
  └── 依赖：ALL 模块（集成展示层）
```

> **图例**：`→` 表示任务依赖；模块名前缀表示跨模块依赖（如 `LO-T1.2` 表示依赖 Logs 模块任务）。

---

## 2. Sprint 0 — 基础设施与核心后端 API

**周期**：第 1-2 周

**目标**：完成全部数据库迁移、领域模型定义、核心 CRUD / 查询 API，使各模块的后端能力可通过 curl/Postman 独立验证。

**交付物清单**：
1. 7 张核心数据表创建完毕（agent_stations, goals, tasks, worker_sessions, handoff_records, quota_records, execution_logs）
2. 全部模块核心 API 可返回 200（Agent CRUD、Goal 创建与启动、Task 查询、Workspace 聚合状态、日志查询、Handoff 触发与查询、额度记录与概览、模型路由选择）
3. 基础单元测试覆盖枚举、状态机、计算逻辑

---

### 2.1 数据模型与数据库（Foundation Layer）

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| AG-T1.1 | AR | US-AR-01~05 | 创建 agent_stations 数据库表 | database | 无 | — |
| AW-T1.1 | AW | US-AW-01/02 | 创建 goals 数据库表 | database | 无 | — |
| AW-T1.2 | AW | US-AW-01/02/03 | 创建 tasks 数据库表 | database | AW-T1.1 | — |
| AW-T1.3 | AW | US-AW-04 | 创建 worker_sessions 数据库表 | database | AW-T1.2 | — |
| HM-T1.1 | HM | US-HM-01~07 | 创建 handoff_records 数据库表 | database | 无 | — |
| QM-T1.1 | QM | US-QM-01~05 | 创建 quota_records 数据库表 | database | 无 | — |
| LO-T1.1 | LO | US-LO-01~06 | 创建 execution_logs 数据库表 | database | 无 | — |

### 2.2 领域枚举与状态机（Domain Layer）

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| AG-T1.2 | AR | US-AR-01~04 | 定义 AgentStatus / AgentRole 枚举与校验规则 | backend | AG-T1.1 | — |
| AW-T1.4 | AW | US-AW-01/02/04 | 定义 Goal / Task / Worker / Agent 状态枚举与流转规则 | backend | AW-T1.1/1.2/1.3 | 需与 AR 枚举对齐 |
| HM-T1.2 | HM | US-HM-02/04/05/07 | 定义 HandoffStatus 状态机与转换规则 | backend | HM-T1.1 | — |
| HM-T1.3 | HM | US-HM-03 | 定义 HandoffSummary 数据结构与兜底生成 | backend | HM-T1.1 | — |
| QM-T1.2 | QM | US-QM-03/04/05 | 定义 QuotaStatus 状态机与额度计算逻辑 | backend | QM-T1.1 | — |
| LO-T1.2 | LO | US-LO-01~06 | 定义 LogEventType / LogEventStatus 枚举与日志写入服务 | backend | LO-T1.1 | 被 HM / QM / MR 依赖写入 |
| MR-T1.1 | MR | US-MR-01/05/06 | 定义模型能力标签与 Routing 核心数据结构 | backend | 无 | — |
| MR-T1.2 | MR | US-MR-01/05/06 | 定义路由规则配置（权重 + 硬约束） | backend | MR-T1.1 | — |

### 2.3 核心后端 API（API Layer）

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| AG-T2.1 | AR | US-AR-01 | GET /agents 列表查询 API | backend | AG-T1.1/1.2 | — |
| AG-T2.2 | AR | US-AR-02 | POST /agents 创建 API | backend | AG-T1.1/1.2 | — |
| AG-T2.3 | AR | US-AR-03 | PATCH /agents/:id 编辑 API | backend | AG-T2.2 | — |
| AG-T2.4 | AR | US-AR-04 | PATCH /agents/:id/status 启用禁用 API | backend | AG-T2.1/2.2 | — |
| AG-T3.1 | AR | US-AR-05 | 实现 Agent 模板数据与 GET /agents/templates API | backend | AG-T1.2 | — |
| AG-T3.2 | AR | US-AR-05 | 模板创建集成（POST /agents 支持 template_id） | backend | AG-T2.2/3.1 | — |
| AW-T2.1 | AW | US-AW-01 | POST /goals + POST /goals/:goalId/start API | backend | AW-T1.1/1.2/1.4 | — |
| AW-T2.2 | AW | US-AW-03 | GET /tasks/:taskId 详情 API | backend | AW-T1.2/1.3 | — |
| AW-T2.3 | AW | US-AW-02/04 | GET /workspace/:goalId/state 聚合状态查询 API | backend | AW-T1.1/1.2/1.3/1.4 | — |
| LO-T2.1 | LO | US-LO-01/02/05 | GET /logs 列表 + 筛选 API | backend | LO-T1.1/1.2 | — |
| LO-T2.2 | LO | US-LO-03 | GET /logs/:logId 单条详情 API | backend | LO-T1.1/1.2 | — |
| LO-T3.1 | LO | US-LO-04 | GET /logs/task/:taskId/timeline API | backend | LO-T1.1/1.2 | — |
| HM-T2.1 | HM | US-HM-01/07 | POST /tasks/:taskId/handoff（手动触发 + 防重复） | backend | HM-T1.1/1.2 | — |
| HM-T2.2 | HM | US-HM-02/03 | GET /handoffs/:handoffId（查询单条 + 完整摘要） | backend | HM-T1.1/1.3 | — |
| HM-T2.4 | HM | US-HM-05 | PATCH /handoffs/:handoffId/result（记录结果） | backend | HM-T1.2/2.1 | — |
| QM-T2.1 | QM | US-QM-01 | POST /quota/record-usage API | backend | QM-T1.1 | — |
| QM-T2.2 | QM | US-QM-01/04 | Usage 记录后触发额度重算 | backend | QM-T1.2/2.1 | — |
| QM-T3.1 | QM | US-QM-02 | GET /quota/overview 概览 API | backend | QM-T1.1/1.2 | — |
| QM-T3.2 | QM | US-QM-03 | PATCH /quota/models/:modelId/quota 手动设置额度 API | backend | QM-T1.2/3.1 | — |
| QM-T3.3 | QM | US-QM-04 | GET /quota/models/:modelId/status 单模型状态查询 API | backend | QM-T1.1/1.2 | — |
| MR-T2.1 | MR | US-MR-04 | 模型候选池筛选（硬约束过滤） | backend | MR-T1.1/1.2 | 依赖 QM 额度状态查询（可用 mock） |
| MR-T2.2 | MR | US-MR-01 | 简单评分实现（规则匹配优先，让 API 先跑通） | backend | MR-T2.1 | — |
| MR-T3.1 | MR | US-MR-01/04/05 | POST /router/select-model API（先接入简单评分） | backend | MR-T2.1/2.2 | — |

### 2.4 单元测试（与开发并行）

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| AG-T6.1 | AR | US-AR-01~05 | 后端 API 单元 + 集成测试 | test | AG-T2.x | — |
| QM-T8.1 | QM | US-QM-01/03/04 | 额度计算与状态机单元测试 | test | QM-T1.2 | — |
| LO-T8.1 | LO | US-LO-01/02/05 | 日志枚举与写入服务单元测试 | test | LO-T1.2 | — |
| MR-T6.1 | MR | US-MR-01/04/05 | 评分引擎单元测试 | test | MR-T2.x | — |
| HM-T7.1 | HM | US-HM-02/03/07 | 状态机与领域逻辑单元测试 | test | HM-T1.2/1.3 | — |

### 2.5 前端骨架（与后端并行）

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| AW-T3.1 | AW | US-AW-01/02/04 | Workspace 页面框架 + 三栏布局（mock 数据） | frontend | 无 | — |
| AG-T4.1 | AR | US-AR-01 | AgentRegistryPage 页面框架 + AgentList 列表（含 mock 数据） | frontend | 无 | — |

---

## 3. Sprint 1 — 前端组件与功能后端补全

**周期**：第 3-4 周

**目标**：Workspace / Registry / Logs / Quota / Handoff / Router 的前端组件全部可独立运行（mock 数据）；后端补全 Handoff Accept、Summary 生成、完整路由评分、额度自动拦截等关键能力。

**交付物清单**：
1. Workspace 页面完整 mock：Goal 输入、Task 卡片（5 种状态动画）、Agent Station、Task Tree、Task Detail、底部日志面板
2. Agent Registry 页面完整 mock + 真实 API：列表、创建/编辑表单、模板创建、启禁用开关
3. Handoff 触发面板、状态指示器（mock）、Summary mock 生成器
4. Quota 预警条、RiskBadge、Overview 页面（mock）
5. RoutingResultCard（mock）
6. ExecutionLogPanel、LogDetailDrawer、TaskTimeline（mock）
7. 后端：Handoff Accept API、Summary 异步生成、完整 6 维度评分、额度 LIMITED 拦截 + auto-handoff 触发

---

### 3.1 后端功能补全

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| HM-T2.3 | HM | US-HM-04 | POST /handoffs/:handoffId/accept（接受交接 + 创建 Worker） | backend | HM-T2.1/2.2 | — |
| HM-T3.1 | HM | US-HM-03 | Summary Prompt 模板 + 简单 mock 生成 | backend | HM-T1.3 | — |
| HM-T3.2 | HM | US-HM-03 | 上下文数据收集服务 | backend | HM-T3.1 | 依赖 LO-T1.2（日志读取） |
| HM-T3.3 | HM | US-HM-03 | 集成 Summary 生成到 Handoff 工作流（异步） | backend | HM-T2.1/3.1/3.2 | — |
| HM-T4.1 | HM | US-HM-06 | Handoff 事件写入 ExecutionLog | backend | HM-T1.2/2.1 | **依赖 LO-T1.2（日志写入服务）** |
| MR-T2.3 | MR | US-MR-01/05 | 完整 6 维度评分算法 | backend | MR-T2.2 | 依赖 QM-T1.2（额度状态）可用 mock |
| MR-T3.2 | MR | US-MR-01/05 | POST /router/select-model API（升级为完整 6 维度评分） | backend | MR-T2.3/3.1 | — |
| MR-T3.3 | MR | US-MR-03 | POST /router/override-model API（手动覆盖） | backend | MR-T3.1 | — |
| QM-T5.1 | QM | US-QM-05 | LIMITED 模型拦截 + 自动 Handoff 触发 | backend | QM-T1.2/2.2 | **依赖 MR-T3.1（选备用模型）+ HM-T2.1（Handoff 创建）** |

### 3.2 Workspace 前端组件（mock 数据）

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| AW-T3.2 | AW | US-AW-01 | GoalInputPanel 组件 | frontend | AW-T2.1/3.1 | — |
| AW-T3.3 | AW | US-AW-01/02 | TopStatusBar 组件 | frontend | AW-T3.1 | — |
| AW-T4.1 | AW | US-AW-02 | TaskCard 组件 + 状态颜色/图标/动画（mock 数据） | frontend | AW-T3.1 | — |
| AW-T4.2 | AW | US-AW-04 | AgentStationCard + WorkerBadge 组件（mock 数据） | frontend | AW-T3.1 | — |
| AW-T4.3 | AW | US-AW-02 | TaskTree 组件 | frontend | AW-T4.1/3.1 | — |
| AW-T5.1 | AW | US-AW-03 | TaskDetailPanel 组件（mock 数据） | frontend | AW-T3.1 | — |

### 3.3 第三方模块前端组件（mock 数据，可被 Workspace 集成）

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| LO-T4.1 | LO | US-LO-01/02/05 | ExecutionLogPanel 组件（mock 数据） | frontend | 无 | — |
| LO-T5.1 | LO | US-LO-03 | LogDetailDrawer 组件 | frontend | LO-T2.2 | — |
| LO-T6.1 | LO | US-LO-04 | TaskTimeline 组件（mock 数据） | frontend | 无 | — |
| HM-T5.1 | HM | US-HM-02 | TaskCard Handoff 状态展示 + HandoffStatusIndicator（mock 数据） | frontend | 无 | — |
| HM-T5.2 | HM | US-HM-01/07 | Handoff 触发面板（选择 Agent + 填写原因） | frontend | HM-T2.1/5.1 | — |
| QM-T4.1 | QM | US-QM-04 | Workspace TopStatusBar 额度预警条（mock 数据） | frontend | 无 | — |
| QM-T4.2 | QM | US-QM-04 | WorkerBadge RiskBadge 组件（mock 数据） | frontend | 无 | — |
| QM-T6.1 | QM | US-QM-02 | QuotaOverviewPage 页面框架 + 模型列表（mock 数据） | frontend | 无 | — |
| MR-T4.1 | MR | US-MR-02 | RoutingResultCard 组件（mock 数据） | frontend | 无 | — |

### 3.4 Agent Registry 前端页面

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| AG-T4.2 | AR | US-AR-01 | 对接真实 API（AgentList 数据层） | frontend | AG-T2.1/4.1 | — |
| AG-T4.3 | AR | US-AR-02/03 | AgentConfigForm 组件（创建 + 编辑共用） | frontend | AG-T2.2/2.3/4.2 | — |
| AG-T4.4 | AR | US-AR-04 | 启用/禁用开关 + 状态变更反馈 | frontend | AG-T2.4/4.2 | — |
| AG-T4.5 | AR | US-AR-05 | 模板创建 UI（模板卡片 + 快速创建） | frontend | AG-T3.1/3.2/4.3 | — |

### 3.5 API 集成测试（与开发并行）

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| AW-T7.1 | AW | US-AW-01~04 | API 集成测试 | test | AW-T2.x | — |
| LO-T8.2 | LO | US-LO-01~04/06 | API 集成测试 | test | LO-T2/3.x | — |
| HM-T7.2 | HM | US-HM-01~07 | API 集成测试 | test | HM-T2/3.x | — |
| MR-T6.2 | MR | US-MR-01/03/04 | API 集成测试 | test | MR-T3.1/3.3 | — |
| QM-T8.2 | QM | US-QM-01~04 | API 集成测试 | test | QM-T2/3.x | — |

---

## 4. Sprint 2 — 真实数据对接与手动闭环

**周期**：第 5-6 周

**目标**：将前端 mock 切换为真实 API，实现第一个可演示的端到端闭环：创建 Goal → Task 运行 → 实时日志 → 手动触发 Handoff → 接受交接 → Task 恢复运行。Quota Overview 和 Logs Timeline 页面展示真实数据。

**交付物清单**：
1. Workspace 实时同步后端状态（2 秒轮询），TaskCard 动画随真实状态触发
2. ExecutionLogPanel 显示真实日志，错误自动展开
3. Handoff 完整流程可手动触发、查看 Summary、接受交接、WorkerBadge 平滑切换
4. Quota Overview 展示真实额度数据，RiskBadge 与预警条随状态变化
5. RoutingResultCard 对接真实 API，支持接受 / 切换模型
6. Logs 页面可查看 Task 完整执行时间线
7. 前端组件测试覆盖

---

### 4.1 Workspace 真实数据对接

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| AW-T5.2 | AW | US-AW-02/03/04 | 对接真实 Workspace 状态数据（轮询） | frontend | AW-T2.3/5.1/4.x | — |
| AW-T6.1 | AW | US-AW-05 | ExecutionLogPanel 集成（Logs 模块组件） | frontend | AW-T3.1/LO-T4.1 | **依赖 LO-T4.1（Logs 组件）** |
| AW-T6.2 | AW | US-AW-06 | HandoffStatusIndicator 集成（Handoff 模块组件） | frontend | AW-T4.1/HM-T5.1 | **依赖 HM-T5.1（Handoff 组件）** |

### 4.2 Logs / Observability 真实数据

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| LO-T4.2 | LO | US-LO-01/02 | 日志筛选 UI + 对接真实 API | frontend | LO-T2.1/4.1 | — |
| LO-T4.3 | LO | US-LO-05 | 错误日志自动展开与高亮 | frontend | LO-T4.1/4.2 | — |
| LO-T6.2 | LO | US-LO-04 | LogsPage Task 时间线页面 + 对接真实 API | frontend | LO-T3.1/6.1/5.1 | — |

### 4.3 Handoff 完整流程对接

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| HM-T5.3 | HM | US-HM-03/05 | Handoff Detail Drawer | frontend | HM-T2.2/2.4/3.3 | — |
| HM-T5.4 | HM | US-HM-04 | 接受交接 UI + Worker 切换展示 | frontend | HM-T2.3/5.1 | — |
| HM-T4.2 | HM | US-HM-06 | ExecutionLogPanel Handoff 日志渲染 | frontend | HM-T4.1 | **依赖 LO-T4.1/4.2（日志面板）** |

### 4.4 Quota 真实数据对接

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| QM-T4.3 | QM | US-QM-04 | 对接真实 Quota 状态数据（轮询/SSE） | frontend | QM-T3.3/4.1/4.2 | — |
| QM-T6.2 | QM | US-QM-02 | 对接真实概览 API + ModelUsageCard 展开 | frontend | QM-T3.1/6.1 | — |
| QM-T6.3 | QM | US-QM-03 | 额度设置表单（ModelUsageCard 内嵌） | frontend | QM-T3.2/6.2 | — |
| QM-T5.2 | QM | US-QM-05 | Workspace 自动 Handoff 状态展示 | frontend | QM-T5.1/HM | **依赖 QM-T5.1（自动 Handoff 后端）+ HM-T5.4（Handoff UI）** |

### 4.5 Model Router 真实数据对接

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| MR-T4.2 | MR | US-MR-02 | 对接真实路由 API + 卡片交互 | frontend | MR-T3.1/4.1 | — |
| MR-T4.3 | MR | US-MR-05 | 评分拆解矩阵 UI（6 维度展开区域） | frontend | MR-T3.2/4.2 | — |
| MR-T4.4 | MR | US-MR-03 | 手动覆盖模型 UI（备用模型选择 + 确认） | frontend | MR-T3.3/4.2 | — |

### 4.6 前端组件测试（与开发并行）

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| AW-T7.2 | AW | US-AW-01~04 | 前端组件测试 | test | AW-T3/4/5.x | — |
| AG-T6.2 | AR | US-AR-01~05 | 前端组件测试 | test | AG-T4.x | — |
| LO-T8.3 | LO | US-LO-01~05/06 | 前端组件测试 | test | LO-T4/5/6/7.x | — |
| HM-T7.3 | HM | US-HM-01~06 | 前端组件测试 | test | HM-T5.x/4.2 | — |
| MR-T6.3 | MR | US-MR-02/03/05 | 前端组件测试 | test | MR-T4.x | — |
| QM-T8.3 | QM | US-QM-02/04 | 前端组件测试 | test | QM-T4/6.x | — |

---

## 5. Sprint 3 — 自动 Handoff、E2E 与打磨

**周期**：第 7-8 周

**目标**：实现额度 LIMITED 时系统自动拦截并触发 Handoff 的完整闭环；完成 Workspace 和 Handoff 的端到端自动化测试；修复集成中发现的问题。

**交付物清单**：
1. 自动 Handoff 演示：设置低额度 → 触发模型调用 → 额度达到 LIMITED → API 被拦截 → 自动触发 Handoff → Workspace 显示切换提示 → Task 由备用模型继续执行
2. Workspace E2E 测试通过：完整 happy path + Handoff 场景 + 错误场景
3. Handoff E2E 测试通过：完整手动 Handoff 流程 + 防重复 + Summary 失败兜底
4. 全模块 API 集成测试回归通过

---

### 5.1 端到端测试与闭环验证

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| AW-T7.3 | AW | US-AW-01~06 | Workspace 端到端工作流测试 | test | 全部 Feature（最后执行） | **跨模块：验证 Goal→Task→Log→Handoff 完整链路** |
| HM-T7.4 | HM | US-HM-01~07 | Handoff 端到端工作流测试 | test | 全部 Feature（最后执行） | **跨模块：验证 Handoff 全状态流转 + 日志事件链** |

### 5.2 回归与打磨（预留 Buffer）

| 任务 ID | 模块 | Story ID | 任务名称 | 类型 | 依赖任务 | 跨模块依赖 |
|---------|------|----------|---------|------|----------|-----------|
| REG-T1 | ALL | ALL | Sprint 2 集成问题修复与性能优化 | bugfix | Sprint 2 全部 | — |
| REG-T2 | ALL | ALL | 全模块 API 集成测试回归 | test | 全部 API | — |
| REG-T3 | ALL | ALL | Workspace 性能优化（轮询频率、重渲染控制） | optimize | AW-T5.2 | — |

---

## 6. 已排除的 P1 / 后期任务（不在 MVP Backlog 中）

以下任务明确标记为 P1 或属于后期功能，已排除以保证 MVP 聚焦：

| 任务 ID | 模块 | Story ID | 任务名称 | 排除原因 |
|---------|------|----------|---------|---------|
| QM-T1.3 | QM | US-QM-06 | 创建 QuotaStatusHistory 表 | P1 |
| QM-T7.1 | QM | US-QM-06 | GET /quota/models/:modelId/history API | P1 |
| QM-T7.2 | QM | US-QM-06 | QuotaStatusHistory 时间线组件 | P1 |
| LO-T7.1 | LO | US-LO-06 | GET /logs/aggregate 聚合统计 API | P1 |
| LO-T7.2 | LO | US-LO-06 | TokenUsageSummary 组件 | P1 |
| HM-T6.1 | HM | US-HM-10 | GET /handoffs 列表 API | P1 |
| HM-T6.2 | HM | US-HM-10 | Handoff 列表页 | P1 |
| AG-T5.1 | AR | US-AR-06 | GET /agents/:id/stats API | P1 |
| AG-T5.2 | AR | US-AR-06 | AgentStatsPanel 组件 | P1 |
| MR-T5.1 | MR | US-MR-06 | GET /router/rules API | P1 |
| MR-T5.2 | MR | US-MR-06 | RouterRulesPage 前端 | P1 |
| AW-T6.3 | AW | US-AW-07 | RiskBadge 集成（Quota 模块组件） | P1（AW 侧） |
| AW-T6.4 | AW | US-AW-08 | RoutingResultCard 集成（Router 模块组件） | P1（AW 侧） |

---

## 7. 关键跨模块依赖时序

为确保闭环演示，以下跨模块对接点必须按顺序完成：

```
Week 1-2 (Sprint 0)
  ├─ LO-T1.2 日志写入服务就绪
  │     → 阻塞 HM-T4.1 / QM-T5.1 的事件写入
  ├─ AG-T1.2 Agent 枚举就绪
  │     → 阻塞 AW-T1.4 状态枚举对齐
  ├─ MR-T3.1 简单路由 API 就绪
  │     → 阻塞 QM-T5.1 自动 Handoff 选备用模型
  └─ HM-T2.1 Handoff 触发 API 就绪
        → 阻塞 QM-T5.1 自动 Handoff 创建交接

Week 3-4 (Sprint 1)
  ├─ LO-T4.1 ExecutionLogPanel 组件就绪
  │     → 阻塞 AW-T6.1 集成
  ├─ HM-T5.1 HandoffStatusIndicator 组件就绪
  │     → 阻塞 AW-T6.2 集成
  ├─ QM-T5.1 LIMITED 拦截 + 自动 Handoff 就绪
  │     → 阻塞 QM-T5.2 前端展示
  └─ HM-T2.3 Accept API 就绪
        → 阻塞 HM-T5.4 接受交接 UI

Week 5-6 (Sprint 2)
  ├─ AW-T5.2 真实数据轮询就绪
  │     → 所有 Workspace 状态组件开始显示真实数据
  ├─ QM-T4.3 RiskBadge 真实数据就绪
  │     → 预警条与 Workspace 状态同步
  └─ MR-T4.2 真实路由卡片就绪
        → 模型选择可视化闭环

Week 7-8 (Sprint 3)
  └─ E2E 验收：AW-T7.3 + HM-T7.4
        → 验证 Goal→Task→Log→Handoff→Task 完整链路
```

---

## 8. 风险与应对（MVP 级别）

| 风险 | 影响 Sprint | 应对 |
|------|------------|------|
| Usage / 日志高频写入导致数据库压力 | 0-1 | 使用内存队列 + 批量写入（每 100 条或 1-5 秒 flush），MVP 不引入 Kafka/ELK |
| 自动 Handoff 依赖 Model Router + Handoff Manager 同时就绪 | 1 | QM-T5.1 先实现 LIMITED 拦截和事件触发，Handoff 创建用最小 stub；等 HM-T2.1 就绪后替换 |
| 前端轮询对服务端造成压力 | 2 | 2 秒轮询间隔；API 响应目标 < 100ms；后续可改为 SSE |
| LLM Summary 生成超时/失败 | 1-2 | HM-T1.3 兜底摘要机制保证 UI 永远有内容；HM-T3.1 先用 mock 生成器 |
| 6 维度评分算法过于复杂 | 1 | MR-T2.2 先提供简单评分让 API 跑通；MR-T2.3 完整算法延后到 Sprint 1 |
| 多个模块同时开发导致接口不兼容 | 0-2 | Sprint 0 优先完成数据表 Schema 和 TypeScript 接口定义，各模块签章锁定 |

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
>
> 相关文档：
> - `docs/tasks/agent-registry-tasks.md`
> - `docs/tasks/model-router-tasks.md`
> - `docs/tasks/quota-manager-tasks.md`
> - `docs/tasks/handoff-manager-tasks.md`
> - `docs/tasks/logs-observability-tasks.md`
> - `docs/tasks/agent-workspace-tasks.md`
