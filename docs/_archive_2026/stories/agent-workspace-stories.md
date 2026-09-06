# Agent Workspace 用户故事

> 所属产品：ModelGate Agent Studio
>
> 来源文档：`docs/prd/agent-workspace-prd.md`
>
> 文档定位：将 Workspace PRD 转化为可开发、可测试的用户故事与验收标准。

---

## 故事清单

| 编号 | 优先级 | 故事摘要 | 涉及页面 | 涉及接口 | 数据对象 |
|------|--------|----------|----------|----------|----------|
| US-AW-01 | P0 | 输入 Goal 并启动任务 | Workspace, GoalInputPanel | `POST /goals`, `POST /goals/:id/start` | Goal, Task |
| US-AW-02 | P0 | 实时观察 Task 状态变化 | Workspace, AgentStationBoard | `GET /workspace/:goalId/state` | Task, AgentStation |
| US-AW-03 | P0 | 查看 Task 详情和输出 | Workspace, TaskDetailPanel | `GET /tasks/:taskId` | Task, WorkerSession |
| US-AW-04 | P0 | 查看 Agent Station 和 Worker 状态 | Workspace, AgentStationCard | `GET /agents`, `GET /workspace/:goalId/state` | AgentStation, WorkerSession, Model |
| US-AW-05 | P0 | 查看执行日志 | Workspace, ExecutionLogPanel | `GET /logs` | ExecutionLog |
| US-AW-06 | P0 | Handoff 状态可视化 | Workspace, TaskCard | `GET /handoffs`, `GET /workspace/:goalId/state` | HandoffRecord, Task |
| US-AW-07 | P1 | 额度风险徽章展示 | Workspace, WorkerBadge | `GET /quota/models/:modelId/status` | QuotaRecord, WorkerSession |
| US-AW-08 | P1 | 模型路由决策展示 | Workspace, RoutingResultCard | `POST /router/select-model` | RoutingResult, Task |

---

## P0 用户故事

### US-AW-01：输入 Goal 并启动任务

- **Summary:** 用户在 Workspace 左侧输入 Goal，点击开始后系统创建 Goal 并进入 planning 状态。

#### Use Case:
- **As a** 多模型协作平台用户
- **I want to** 在 Workspace 左侧输入一个 Goal 并点击开始
- **so that** 系统能自动拆解任务并启动多 Agent 协作流程

#### Acceptance Criteria:

- **Scenario:** 用户输入 Goal 并启动
- **Given:** 我正在 Workspace 页面
- **and Given:** Goal 输入框为空或已填写内容
- **When:** 我输入 Goal 描述并点击 [开始] 按钮
- **Then:** 系统创建 Goal，返回 `goal_id`，Top Status Bar 显示 Goal 状态为 `planning`
- **and Then:** Planner Agent Station Card 边框变蓝，WorkerBadge 显示 ▶ running
- **and Then:** 如果 Goal 描述为空，前端禁用 [开始] 按钮并提示

**涉及页面：** Workspace / GoalInputPanel / TopStatusBar / AgentStationBoard
**涉及接口：** `POST /goals`, `POST /goals/:goalId/start`
**数据对象：** Goal, Task

**可转测试的验收点：**
1. 前端：空 Goal 时 [开始] 按钮禁用
2. 前端：点击开始后输入区收起，显示 "Planning..."
3. 前端：Top Status Bar 状态标签变为紫色 `planning`
4. 后端：`POST /goals` 返回 `{ goal_id, status: "idle" }`
5. 后端：`POST /goals/:goalId/start` 返回 `{ goal_id, status: "planning" }`
6. 后端：Goal 状态从 `idle` 流转为 `planning`

---

### US-AW-02：实时观察 Task 状态变化

- **Summary:** 用户在 Workspace 中间区域看到 TaskCard 随状态变化实时更新颜色、图标和动画。

#### Use Case:
- **As a** 需要跟踪任务进度的开发者
- **I want to** 在 Workspace 中实时看到每个 Task 的状态变化
- **so that** 我一眼就能知道哪些 Task 在等待、执行中、已完成或失败

#### Acceptance Criteria:

- **Scenario:** Task 状态变化在 Workspace 中可视化
- **Given:** Goal 已进入 `running` 状态，有多个 Task 被创建
- **When:** 任一 Task 的状态从 `pending` → `assigned` → `running` → `completed`/`failed` 变化时
- **Then:** 对应 TaskCard 的边框颜色、背景色、状态图标同步更新
- **and Then：** `running` 状态显示蓝色呼吸动画，`handoff` 状态显示紫色旋转动画，`failed` 状态显示红色抖动动画
- **and Then：** Task Tree 左侧的状态图标同步变化

**涉及页面：** Workspace / AgentStationBoard / TaskCard / GoalInputPanel(TaskTree)
**涉及接口：** `GET /workspace/:goalId/state`（轮询）
**数据对象：** Task, AgentStation

**可转测试的验收点：**
1. 前端：`pending` = 灰色虚线边框 + ⏸ 图标
2. 前端：`running` = 蓝色实线边框 + ▶ 图标 + 呼吸动画
3. 前端：`completed` = 绿色实线边框 + ✓ 图标
4. 前端：`failed` = 红色实线边框 + ✗ 图标 + 抖动动画
5. 前端：状态变化时有 300ms CSS 过渡动画
6. 后端：`GET /workspace/:goalId/state` 返回包含所有 Task 最新状态的聚合数据

---

### US-AW-03：查看 Task 详情和输出

- **Summary:** 用户点击 TaskCard 后，右侧 TaskDetailPanel 展示任务描述、完成标准、当前输出、分配 Agent 和 Token 消耗。

#### Use Case:
- **As a** 需要检查 Agent 输出质量的开发者
- **I want to** 点击任意 TaskCard 查看该任务的完整详情
- **so that** 我可以检查 Agent 的输出内容、执行进度和 Token 消耗

#### Acceptance Criteria:

- **Scenario:** 查看 Task 详情
- **Given:** Workspace 中有至少一个 TaskCard
- **When:** 我点击该 TaskCard
- **Then:** 右侧 TaskDetailPanel 展开，显示 Overview / Task / Context / Logs 等 Tab
- **and Then：** Overview Tab 显示：任务状态、优先级、分配 Agent、Worker 模型、Token 消耗、耗时
- **and Then：** Task Tab 显示：任务描述、完成标准、当前输出内容（支持复制）

**涉及页面：** Workspace / TaskCard / TaskDetailPanel
**涉及接口：** `GET /tasks/:taskId`
**数据对象：** Task, WorkerSession, Model

**可转测试的验收点：**
1. 前端：点击 TaskCard 后 TaskDetailPanel 从右侧滑出（300ms 动画）
2. 前端：TaskDetailPanel 默认显示 Overview Tab
3. 前端：输出内容区域支持复制和展开/折叠
4. 后端：`GET /tasks/:taskId` 返回完整 Task 对象，包含 `output`、`tokens_used`、`duration_ms`
5. 后端：返回的 `assigned_agent_id` 和 `assigned_worker_id` 可关联到 Agent 和 Worker

---

### US-AW-04：查看 Agent Station 和 Worker 状态

- **Summary:** 用户在 AgentStationBoard 中看到每个 Agent Station 的当前状态、绑定的 Worker 模型和状态灯。

#### Use Case:
- **As a** 多模型重度使用的开发者
- **I want to** 看到每个 Agent Station 当前由哪个模型驱动、处于什么状态
- **so that** 我可以确认系统是否按预期分配了正确的模型到正确的角色

#### Acceptance Criteria:

- **Scenario：** 查看 Agent Station 和 Worker 状态
- **Given：** Workspace 中有多个 Agent Station Card
- **When：** 页面加载或状态更新时
- **Then：** 每个 Agent Station Card 显示：Agent 名称、角色、当前 WorkerBadge（模型名 + 状态灯）
- **and Then：** WorkerBadge 状态灯颜色：idle=灰色、running=蓝色（呼吸）、handoff_required=紫色、completed=绿色、failed=红色（闪烁）
- **and Then：** Agent Station Card 边框颜色随 `AgentStatus` 变化（同 TaskCard 状态色）

**涉及页面：** Workspace / AgentStationBoard / AgentStationCard / WorkerBadge
**涉及接口：** `GET /workspace/:goalId/state`
**数据对象：** AgentStation, WorkerSession, Model

**可转测试的验收点：**
1. 前端：每个 Agent Station Card 包含 WorkerBadge 区域
2. 前端：WorkerBadge 显示模型名称和状态灯（彩色圆点）
3. 前端：`running` 状态灯有呼吸动画（CSS `animation: breathe 2s infinite`）
4. 前端：Handoff 后 WorkerBadge 模型名称平滑过渡到新模型（300ms）
5. 后端：`GET /workspace/:goalId/state` 返回 `agents[]` 和 `workers[]`，`worker.agent_id` 可关联到 Agent
6. 后端：Worker 的 `model_id` 对应 Model 表中的有效记录

---

### US-AW-05：查看执行日志

- **Summary:** 用户在底部 ExecutionLogPanel 中实时看到模型调用、Agent 执行、工具调用、状态变化等日志事件。

#### Use Case:
- **As a** 需要排查任务执行过程的开发者
- **I want to** 在 Workspace 底部看到实时的执行日志
- **so that** 我可以追踪每个模型调用、每次状态变化和每个错误的发生时机

#### Acceptance Criteria:

- **Scenario：** 实时查看执行日志
- **Given：** Goal 正在执行中
- **When：** 系统产生新的 ExecutionLog（model_call / agent_step / task_status_change / error 等）
- **Then：** ExecutionLogPanel 实时追加新日志行（延迟 < 2 秒）
- **and Then：** 每条日志显示：时间、图标（✓/✗/🔄/⚡）、事件类型、Agent、Model、摘要
- **and Then：** 错误日志自动高亮为红色，ExecutionLogPanel 自动展开
- **and Then：** 点击日志中的 Task ID 或 Agent ID 可高亮对应 TaskCard 或 Agent Station

**涉及页面：** Workspace / ExecutionLogPanel / BottomConsole
**涉及接口：** `GET /logs`（轮询或 SSE）
**数据对象：** ExecutionLog

**可转测试的验收点：**
1. 前端：新日志追加时高亮 2 秒后恢复正常
2. 前端：`error` 类型日志行背景为红色
3. 前端：`handoff_created` 类型日志显示紫色 🔄 图标
4. 前端：错误发生时 BottomConsole 自动从收起状态展开
5. 后端：`GET /logs?goal_id=xxx` 返回按时间倒序的日志列表
6. 后端：每条日志包含 `event_type`、`event_status`、`agent_id`、`model_id`、`created_at`

---

### US-AW-06：Handoff 状态可视化

- **Summary:** Handoff 发生时，Workspace 中 TaskCard 显示 HandoffStatusIndicator，展示从 requested → generating_summary → ready → accepted → completed 的完整状态流转。

#### Use Case:
- **As a** 需要跟踪任务交接进度的开发者
- **I want to** 在 Workspace 中实时看到 Handoff 的当前状态和进度
- **so that** 我知道交接进行到哪一步，上下文摘要是否已生成，接手 Agent 是否已加载

#### Acceptance Criteria:

- **Scenario：** Handoff 状态可视化
- **Given：** 一个 Task 触发了 Handoff
- **When：** Handoff 状态从 `requested` 逐步变化到 `completed`
- **Then：** TaskCard 上显示 HandoffStatusIndicator，状态标签、图标和颜色同步更新
- **and Then：** `requested`=黄色 🔄、`generating_summary`=紫色 ✍（脉冲）、`ready`=紫色 📋、`accepted`=蓝色 ▶、`completed`=绿色 ✓
- **and Then：** HandoffStatusIndicator 显示进度条：`[✓ requested] → [✍ generating_summary] → [○ ready] → [○ accepted] → [○ completed]`
- **and Then：** Handoff 完成后 Indicator 变为完成标记，3 秒后消失

**涉及页面：** Workspace / TaskCard / HandoffStatusIndicator / AgentStationBoard
**涉及接口：** `GET /handoffs/:handoffId`, `GET /workspace/:goalId/state`
**数据对象：** HandoffRecord, Task

**可转测试的验收点：**
1. 前端：Handoff 触发后 TaskCard 边框变紫色（`handoff` 状态）
2. 前端：HandoffStatusIndicator 在 TaskCard 底部可见
3. 前端：状态变化时图标和颜色平滑过渡（300ms）
4. 前端：`generating_summary` 状态的 ✍ 图标有脉冲动画
5. 后端：`GET /handoffs/:handoffId` 返回 `status`、`from_agent_id`、`to_agent_id`、`handoff_reason`
6. 后端：Handoff 状态变化触发 `handoff_status_updated` 事件（SSE/轮询可感知）

---

## P1 用户故事

### US-AW-07：额度风险徽章展示

- **Summary:** WorkerBadge 上显示 RiskBadge，实时反映当前模型的额度状态（normal / warning / near_limit / limited / cooldown / unknown）。

#### Use Case:
- **As a** 拥有多个 AI Coding Plan 的开发者
- **I want to** 在 Workspace 中一眼看到每个 Worker 所用模型的额度状态
- **so that** 我可以提前知道哪些模型快用完了，避免任务突然中断

#### Acceptance Criteria:

- **Scenario：** 查看模型额度风险
- **Given：** Workspace 中有多个正在执行或空闲的 WorkerBadge
- **When：** 任一模型的 QuotaStatus 发生变化
- **Then：** 对应 WorkerBadge 上的 RiskBadge 同步更新颜色和图标
- **and Then：** normal=绿色✓、warning=黄色⚠、near_limit=橙色🔴、limited=红色✗、cooldown=蓝色⏱、unknown=灰色?
- **and Then：** 鼠标悬停 RiskBadge 显示 Tooltip：使用率、剩余额度、最近错误

**涉及页面：** Workspace / WorkerBadge / RiskBadge
**涉及接口：** `GET /quota/models/:modelId/status`
**数据对象：** QuotaRecord, WorkerSession

**可转测试的验收点：**
1. 前端：每个 WorkerBadge 右上角显示 RiskBadge（圆形或标签）
2. 前端：RiskBadge 颜色与 QuotaStatus 严格对应
3. 前端：鼠标悬停显示 Tooltip，包含 `usage_percent` 和 `estimated_remaining`
4. 后端：`GET /quota/models/:modelId/status` 返回 `quota_status`、`usage_percent`、`estimated_remaining`
5. 后端：Quota 状态变化触发事件，前端可实时更新

---

### US-AW-08：模型路由决策展示

- **Summary:** Model Router 做出路由决策时，Workspace 弹出 RoutingResultCard，展示推荐模型、置信度、评分拆解和风险标记。

#### Use Case:
- **As a** 需要理解系统为什么选某个模型的开发者
- **I want to** 看到 Model Router 的路由决策详情
- **so that** 我理解为什么选这个模型、它的优势和风险是什么，并可以手动覆盖

#### Acceptance Criteria:

- **Scenario：** 查看路由决策
- **Given：** 一个 Task 被分配给某个 Agent，Model Router 正在选择模型
- **When：** Model Router 返回 RoutingResult
- **Then：** Workspace 弹出 RoutingResultCard，显示推荐模型名、置信度条、评分拆解
- **and Then：** 评分拆解显示 6 个维度分数：capability_match、role_match、context_fit、cost_fit、speed_fit、quota_health
- **and Then：** 如果有 risk_flags（如 near_quota_limit），显示 RiskFlagBanner
- **and Then：** 提供 [接受] 和 [切换模型] 按钮

**涉及页面：** Workspace / RoutingResultCard / AgentStationBoard
**涉及接口：** `POST /router/select-model`
**数据对象：** RoutingResult, Model

**可转测试的验收点：**
1. 前端：RoutingResultCard 以浮层形式弹出，5 秒后自动收起（用户未操作时）
2. 前端：置信度条显示为百分比进度条（0-100%）
3. 前端：RiskFlagBanner 根据 `risk_flags` 数组显示对应警告
4. 前端：点击 [切换模型] 弹出备用模型选择列表
5. 后端：`POST /router/select-model` 返回 `RoutingResult` 完整对象
6. 后端：`confidence` 字段为 0-1 之间的浮点数

---

## 附录：数据对象速查

### Task

```typescript
interface Task {
  id: string;
  goal_id: string;
  title: string;
  description: string;
  status: TaskStatus;
  assigned_agent_id?: string;
  assigned_worker_id?: string;
  output?: string;
  tokens_used: number;
  duration_ms: number;
}
```

### AgentStation

```typescript
interface AgentStation {
  id: string;
  name: string;
  role: string;
  status: AgentStatus;
  current_task_id?: string;
  default_model_id: string;
}
```

### WorkerSession

```typescript
interface WorkerSession {
  id: string;
  agent_id: string;
  model_id: string;
  task_id: string;
  status: WorkerStatus;
  total_tokens_used: number;
}
```

### ExecutionLog

```typescript
interface ExecutionLog {
  log_id: string;
  event_type: string;
  event_status: string;
  agent_id?: string;
  model_id?: string;
  task_id?: string;
  created_at: string;
}
```

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
>
> 相关文档：> - `docs/prd/agent-workspace-prd.md` — 完整产品需求
