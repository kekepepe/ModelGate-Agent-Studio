# 数据结构与数据库 Schema

> **本文档是所有 PRD 数据对象的唯一权威聚合。**
>
> 所有状态枚举、接口定义、字段类型以 `docs/prd/` 目录下的 6 份 PRD 为准。本文档是 PRD 数据对象的统一速查表。
>
> 最后对齐：2026-06-25（agent-workspace-prd v2.0、handoff-manager-prd v1.0、model-router-prd v1.0、quota-manager-prd v1.0、agent-registry-prd v1.0、logs-observability-prd v1.0）

---

## 一、状态枚举

**所有状态枚举必须定义在代码常量文件中，禁止硬编码字符串。**

### 1.1 GoalStatus

```typescript
type GoalStatus =
  | 'idle'        // 刚创建，未启动
  | 'planning'    // Planner 正在拆解 Task
  | 'running'     // Task 正在执行
  | 'waiting'     // 等待用户输入或外部条件
  | 'handoff'     // 存在进行中的 Handoff
  | 'reviewing'   // Supervisor 正在审核
  | 'completed'   // 所有 Task 完成，Supervisor 已汇总
  | 'failed';     // 任务失败，无法继续
```

### 1.2 TaskStatus

```typescript
type TaskStatus =
  | 'pending'      // 等待分配
  | 'assigned'     // 已分配给 Agent，未开始
  | 'running'      // 正在执行
  | 'waiting'      // 等待依赖完成
  | 'handoff'      // 正在交接
  | 'completed'    // 完成
  | 'failed';      // 失败
```

### 1.3 AgentStatus

```typescript
type AgentStatus =
  | 'idle'         // 空闲，无当前任务
  | 'queued'       // 有任务排队
  | 'running'      // 正在执行任务
  | 'waiting'      // 等待依赖或输入
  | 'reviewing'    // 审查中（Reviewer / Supervisor）
  | 'handoff'      // 正在交接
  | 'blocked'      // 被阻塞
  | 'error'        // 出错
  | 'done';        // 当前任务完成
```

### 1.4 WorkerStatus

```typescript
type WorkerStatus =
  | 'idle'              // 未绑定任务
  | 'running'           // 正在执行
  | 'handoff_required'  // 需要交接
  | 'completed'         // 完成
  | 'failed';           // 失败
```

### 1.5 HandoffStatus

```typescript
type HandoffStatus =
  | 'requested'           // 交接请求已创建
  | 'generating_summary'  // 正在生成交接摘要
  | 'ready'               // 摘要已生成，等待接受
  | 'accepted'            // 接手 Agent 已接受
  | 'completed'           // 交接完成，新 Worker 开始执行
  | 'failed';             // 交接失败
```

### 1.6 HandoffReason

```typescript
type HandoffReason =
  | 'quota_exceeded'  // 额度不足
  | 'error'           // 模型错误
  | 'quality_issue'   // 输出质量不足
  | 'role_mismatch'   // 角色不匹配
  | 'manual'          // 用户手动触发
  | 'context_limit'   // 上下文限制
  | 'other';          // 其他原因
```

### 1.7 HandoffResult

```typescript
type HandoffResult = 'success' | 'failed' | 'partial';
```

### 1.8 QuotaStatus

```typescript
type QuotaStatus =
  | 'normal'      // 正常
  | 'warning'     // 注意，接近阈值
  | 'near_limit'  // 接近限制，建议准备切换
  | 'limited'     // 已受限，当前不可用
  | 'cooldown'    // 冷却中（rate limit），暂不可用
  | 'unknown';    // 无数据，无法判断
```

### 1.9 QuotaMode

```typescript
type QuotaMode = 'known' | 'estimated' | 'unknown';
```

### 1.10 LogEventType

```typescript
type LogEventType =
  | 'model_call'              // 模型 API 调用
  | 'agent_step'              // Agent 执行 Step
  | 'tool_call'               // 工具调用
  | 'task_status_change'      // Task 状态变化
  | 'quota_status_change'     // 额度状态变化
  | 'handoff_created'         // Handoff 创建
  | 'handoff_completed'       // Handoff 完成
  | 'error'                   // 错误事件
  | 'supervisor_review'       // Supervisor 审核
  | 'memory_write_candidate'; // 记忆写入候选
```

### 1.11 LogEventStatus

```typescript
type LogEventStatus =
  | 'started'           // 开始
  | 'completed'         // 完成
  | 'failed'            // 失败
  | 'skipped'           // 跳过
  | 'transition'        // 状态流转
  | 'created'           // 已创建
  | 'accepted'          // 已接受
  | 'rejected'          // 已拒绝
  | 'timeout'           // 超时
  | 'approved'          // 审核通过
  | 'needs_revision'    // 需要修改
  | 'detected'          // 已检测到
  | 'error';            // 错误
```

---

## 二、核心数据对象

### 2.1 Goal

用户输入的目标，是所有任务的根节点。

```typescript
interface Goal {
  id: string;                          // UUID
  title: string;                       // 目标标题
  description: string;                 // 目标描述
  status: GoalStatus;                  // 状态
  progress: number;                    // 进度（0-1）
  priority: 'low' | 'medium' | 'high'; // 优先级
  total_tasks: number;                 // 总 Task 数
  completed_tasks: number;             // 已完成 Task 数
  handoff_count: number;               // 累计 Handoff 次数
  total_tokens_used: number;           // 累计 token 消耗
  final_summary?: string;              // 最终汇总（完成后）
  created_at: string;                  // ISO 8601
  started_at?: string;                 // ISO 8601
  completed_at?: string;               // ISO 8601
}
```

### 2.2 Task

Goal 拆解后的子任务。

```typescript
interface Task {
  id: string;                          // UUID
  goal_id: string;                     // 所属 Goal
  parent_task_id?: string;             // 父 Task（子任务）
  title: string;                       // 任务标题
  description: string;                 // 任务描述
  status: TaskStatus;                  // 状态
  priority: 'low' | 'medium' | 'high'; // 优先级
  assigned_agent_id?: string;          // 分配的 Agent
  assigned_worker_id?: string;         // 绑定的 Worker
  dependencies: string[];              // 依赖的 Task ID 列表
  output?: string;                     // 输出内容
  completion_criteria?: string;        // 完成标准
  tokens_used: number;                 // 已用 token
  duration_ms: number;                 // 执行时长
  handoff_count: number;               // 累计 Handoff 次数
  step_number?: number;                // 当前 Step 序号
  total_steps?: number;                // 总 Step 数
  created_at: string;                  // ISO 8601
  started_at?: string;                 // ISO 8601
  completed_at?: string;               // ISO 8601
}
```

### 2.3 AgentStation

Agent 工位，代表一个角色。

```typescript
interface AgentStation {
  id: string;                          // UUID
  name: string;                        // 显示名称
  role: 'planner' | 'coder' | 'reviewer' | 'research' | 'summarizer' | 'supervisor';
  description: string;                 // 职责描述
  status: AgentStatus;                 // 状态
  current_task_id?: string;            // 当前任务
  default_model_id: string;            // 默认模型
  backup_model_ids: string[];          // 备用模型列表
  system_prompt: string;               // 系统提示词
  max_steps_per_task: number;          // 每任务最大 Step 数
  max_tool_calls_per_task?: number;    // 每任务最大工具调用数（MVP-B）
  allow_handoff: boolean;              // 是否允许交接
  handoff_threshold_tokens?: number;   // 交接阈值 token 数
  allowed_tools?: string[];            // 允许的工具列表
  output_format?: string;              // 输出格式要求
  total_tasks_completed: number;       // 历史完成任务数
  total_tasks_failed: number;          // 历史失败任务数
}
```

### 2.4 WorkerSession

绑定到 Agent Station 的模型实例。

```typescript
interface WorkerSession {
  id: string;                          // UUID
  agent_id: string;                    // 所属 Agent
  model_id: string;                    // 使用的模型
  goal_id: string;                     // 所属 Goal
  task_id: string;                     // 当前任务
  inherited_from_handoff_id?: string;  // 继承自哪个 Handoff
  status: WorkerStatus;                // 状态
  current_context?: string;            // 当前上下文
  final_output?: string;               // 最终输出
  error_message?: string;              // 错误信息
  input_tokens_used: number;           // 输入 token
  output_tokens_used: number;          // 输出 token
  total_tokens_used: number;           // 总 token
  started_at: string;                  // ISO 8601
  completed_at?: string;               // ISO 8601
}
```

### 2.5 Model

底层模型能力定义。

```typescript
interface Model {
  id: string;                          // UUID
  provider: string;                    // 平台：openai, anthropic, deepseek, kimi...
  model_name: string;                  // 模型 ID：gpt-4o, claude-3-5-sonnet...
  display_name: string;                // 显示名称
  capability_tags: string[];           // 能力标签
  max_context_tokens: number;          // 最大上下文长度
  cost_level: number;                  // 成本等级（1-5）
  speed_level: number;                 // 速度等级（1-5）
  is_enabled: boolean;                 // 是否启用
}
```

---

## 三、Handoff 相关

### 3.1 HandoffRecord

```typescript
interface HandoffRecord {
  id: string;                          // UUID
  goal_id: string;                     // 所属 Goal
  task_id: string;                     // 所属 Task

  from_agent_id: string;               // 原 Agent
  from_model_id: string;               // 原模型
  from_worker_id?: string;             // 原 Worker

  to_agent_id: string;                 // 接手 Agent
  to_model_id: string;                 // 接手模型
  to_worker_id?: string;               // 接手 Worker

  reason: HandoffReason;               // 交接原因
  reason_description?: string;         // 原因描述

  handoff_summary: HandoffSummary;     // 交接摘要

  status: HandoffStatus;               // 交接状态
  result_after_handoff?: HandoffResult; // 交接结果
  result_note?: string;                // 结果备注

  tokens_before_handoff: number;       // 交接前 token 数
  tokens_after_handoff: number;        // 交接后 token 数
  time_saved_estimate_ms?: number;     // 估算节省时间

  created_at: string;                  // ISO 8601
  summary_generated_at?: string;       // ISO 8601
  accepted_at?: string;                // ISO 8601
  completed_at?: string;               // ISO 8601
  updated_at: string;                  // ISO 8601
}
```

### 3.2 HandoffSummary

```typescript
interface HandoffSummary {
  original_goal: string;               // 原始目标
  current_task: string;                // 当前任务
  completed_work: string[];            // 已完成工作
  unfinished_work: string[];           // 未完成工作
  important_constraints: string[];     // 重要约束
  key_decisions: string[];             // 关键决策
  errors_and_risks: string[];          // 错误和风险
  next_suggested_steps: string[];      // 下一步建议
  context_needed: string[];            // 需要的上下文
}
```

---

## 四、Quota 相关

### 4.1 QuotaRecord

```typescript
interface QuotaRecord {
  quota_record_id: string;             // UUID
  provider: string;                    // 平台
  model_id: string;                    // 模型 ID
  model_name: string;                  // 显示名称

  request_count: number;               // API 调用总次数
  input_tokens: number;                // 输入 token 总量
  output_tokens: number;               // 输出 token 总量
  total_tokens: number;                // 总 token 量

  last_used_at: string;                // ISO 8601，最近一次调用
  updated_at: string;                  // ISO 8601
  created_at: string;                  // ISO 8601

  estimated_remaining: number;         // 估算剩余额度
  quota_mode: QuotaMode;               // 额度模式

  token_limit?: number;                // token 上限
  request_limit?: number;              // 请求数上限
  cost_limit?: number;                 // 费用上限（USD）
  reset_period?: 'daily' | 'weekly' | 'monthly' | 'never';
  reset_date?: number;                 // 每月几号重置

  quota_status: QuotaStatus;           // 额度状态

  limit_error_count: number;           // 额度/限制相关错误次数
  cooldown_until?: string;             // ISO 8601，冷却结束时间

  handoff_triggered_count: number;     // 因额度触发的 Handoff 次数

  estimation_confidence?: number;      // 估算置信度（0-1）
  estimation_method?: 'usage_trend' | 'error_frequency' | 'default_assumption';
}
```

### 4.2 QuotaStatusHistory

```typescript
interface QuotaStatusHistory {
  history_id: string;                  // UUID
  quota_record_id: string;             // 关联 QuotaRecord
  from_status: QuotaStatus;            // 原状态
  to_status: QuotaStatus;              // 新状态
  reason: string;                      // 变化原因
  triggered_by: 'system' | 'user' | 'handoff' | 'router';
  usage_percent_at_change: number;     // 变化时使用率
  total_tokens_at_change: number;      // 变化时总 token
  request_count_at_change: number;     // 变化时请求数
  limit_error_count_at_change: number; // 变化时错误数
  created_at: string;                  // ISO 8601
}
```

### 4.3 QuotaThresholds（配置）

```typescript
interface QuotaThresholds {
  warning_percent: number;             // 默认 0.70
  near_limit_percent: number;          // 默认 0.90
  cooldown_minutes: number;            // 默认 1
  max_errors_per_hour: number;         // 默认 3
  max_rate_limit_errors: number;       // 默认 2
  model_overrides?: Record<string, Partial<QuotaThresholds>>;
}
```

---

## 五、Logs 相关

### 5.1 ExecutionLog

```typescript
interface ExecutionLog {
  log_id: string;                      // UUID

  goal_id?: string;                    // 所属 Goal
  task_id?: string;                    // 所属 Task
  agent_id?: string;                   // 所属 Agent
  worker_id?: string;                  // 所属 Worker
  model_id?: string;                   // 使用的模型
  handoff_id?: string;                 // 关联 Handoff

  event_type: LogEventType;            // 事件类型
  event_status: LogEventStatus;        // 事件状态
  created_at: string;                  // ISO 8601

  input_summary?: string;              // 输入摘要（前 500 字符）
  output_summary?: string;             // 输出摘要（前 500 字符）

  token_usage?: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };

  quota_status?: string;               // 事件发生时的额度状态
  handoff_status?: string;             // 事件发生时的 Handoff 状态
  tool_name?: string;                  // 工具名称
  tool_type?: string;                  // 工具类型

  error_type?: string;                 // 错误类型
  error_code?: string;                 // 错误码
  error_message?: string;              // 错误信息
  stack_trace?: string;                // 堆栈跟踪

  latency_ms?: number;                 // 调用延迟
  duration_ms?: number;                // 执行时长

  metadata?: Record<string, any>;      // 扩展元数据
  context_snapshot_id?: string;        // 关联上下文快照（MVP-B）
}
```

---

## 六、Model Router 相关

### 6.1 RoutingRequest

```typescript
interface RoutingRequest {
  task_id: string;                     // 任务 ID
  task_type: string;                   // 任务类型
  task_complexity: 'low' | 'medium' | 'high';
  required_capabilities: string[];     // 所需能力标签
  budget_preference?: 'low' | 'medium' | 'high';
  speed_preference?: 'fast' | 'balanced' | 'quality';
  quota_status?: QuotaStatus;          // 当前额度状态
  context_length_estimate?: number;    // 预估上下文长度
}
```

### 6.2 RoutingResult

```typescript
interface RoutingResult {
  selected_model_id: string;           // 推荐模型 ID
  selected_model_name: string;         // 推荐模型名称
  backup_model_ids: string[];          // 备用模型列表
  routing_reason: string;              // 路由理由
  confidence: number;                  // 置信度（0-1）
  risk_flags: string[];                // 风险标记
  score_breakdown: {
    capability_match: number;          // 能力匹配（默认权重 0.25）
    role_match: number;                // 角色匹配（默认权重 0.20）
    context_fit: number;               // 上下文适配（默认权重 0.15）
    cost_fit: number;                  // 成本适配（默认权重 0.15）
    speed_fit: number;                 // 速度适配（默认权重 0.10）
    quota_health: number;              // 额度健康度（默认权重 0.10）
    historical_performance?: number;    // 历史表现（MVP-B，默认权重 0.05）
  };
}
```

---

## 七、Workspace 渲染相关

### 7.1 WorkspaceState

前端集中式状态管理的核心结构。

```typescript
interface WorkspaceState {
  goal: Goal | null;
  tasks: Task[];
  agents: AgentStation[];
  workers: WorkerSession[];
  models: Model[];
  handoffs: HandoffRecord[];
  quotaRecords: QuotaRecord[];
  routingResults: RoutingResult[];
  logs: ExecutionLog[];

  selectedEntity: {
    type: 'task' | 'agent' | 'handoff' | 'goal' | 'quota' | null;
    id: string | null;
  };

  isRunning: boolean;
  viewMode: 'card-flow' | 'pixel-office';
  error: string | null;

  quotaAlerts: QuotaAlert[];
  activeHandoffs: HandoffRecord[];
  latestRoutingResult: RoutingResult | null;
  latestError: ExecutionLog | null;
}

interface QuotaAlert {
  model_id: string;
  model_name: string;
  quota_status: QuotaStatus;
  usage_percent: number;
}
```

---

## 八、对象关系图

```text
Goal 1
├── N Task
│   ├── 1 AgentStation（assigned）
│   ├── 0..1 WorkerSession（当前执行）
│   ├── 0..N HandoffRecord
│   └── 0..N ExecutionLog
│
└── 1..N AgentStation（参与协作）
    ├── 0..1 WorkerSession（当前 Worker）
    ├── 1 Model（default_model）
    └── 0..N Task（历史任务）

Model 1
├── 0..N QuotaRecord（按 provider + model_id）
├── 0..N WorkerSession
└── 0..N HandoffRecord（as from_model / to_model）

HandoffRecord 1
├── 1 Task
├── 1 Goal
├── 1 AgentStation（from_agent）
├── 1 AgentStation（to_agent）
├── 1 Model（from_model）
├── 1 Model（to_model）
├── 0..1 WorkerSession（from_worker）
├── 0..1 WorkerSession（to_worker）
└── 1 HandoffSummary

ExecutionLog N
├── 0..1 Goal
├── 0..1 Task
├── 0..1 AgentStation
├── 0..1 WorkerSession
├── 0..1 Model
└── 0..1 HandoffRecord
```

---

## 九、数据库表设计建议

### 9.1 表清单

| 表名 | 说明 | 核心索引 |
|------|------|----------|
| `goals` | Goal 表 | `id`, `status`, `created_at` |
| `tasks` | Task 表 | `id`, `goal_id`, `status`, `assigned_agent_id` |
| `agent_stations` | Agent Station 表 | `id`, `role`, `status` |
| `worker_sessions` | Worker Session 表 | `id`, `agent_id`, `task_id`, `status` |
| `models` | Model 表 | `id`, `provider`, `is_enabled` |
| `handoff_records` | Handoff 记录表 | `id`, `task_id`, `goal_id`, `status` |
| `quota_records` | 额度记录表 | `id`, `provider`, `model_id`, `quota_status` |
| `quota_status_history` | 额度状态历史表 | `id`, `quota_record_id`, `created_at` |
| `execution_logs` | 执行日志表 | `id`, `goal_id`, `task_id`, `event_type`, `created_at` |

### 9.2 JSON 字段使用建议

以下字段建议存储为 JSON / JSONB，以支持灵活扩展：

- `handoff_records.handoff_summary` — HandoffSummary 结构
- `handoff_records.score_breakdown` — RoutingResult 的 score_breakdown
- `execution_logs.metadata` — 各类型特定的扩展字段
- `execution_logs.token_usage` — Token 使用统计
- `quota_records.model_overrides` — 模型特定阈值覆盖

### 9.3 外键约束

| 子表 | 外键字段 | 父表 |
|------|----------|------|
| `tasks` | `goal_id` | `goals` |
| `tasks` | `assigned_agent_id` | `agent_stations` |
| `tasks` | `assigned_worker_id` | `worker_sessions` |
| `worker_sessions` | `agent_id` | `agent_stations` |
| `worker_sessions` | `model_id` | `models` |
| `worker_sessions` | `task_id` | `tasks` |
| `handoff_records` | `goal_id` | `goals` |
| `handoff_records` | `task_id` | `tasks` |
| `handoff_records` | `from_agent_id` | `agent_stations` |
| `handoff_records` | `to_agent_id` | `agent_stations` |
| `handoff_records` | `from_model_id` | `models` |
| `handoff_records` | `to_model_id` | `models` |
| `quota_records` | `model_id` | `models` |
| `execution_logs` | `goal_id` | `goals` |
| `execution_logs` | `task_id` | `tasks` |
| `execution_logs` | `agent_id` | `agent_stations` |
| `execution_logs` | `worker_id` | `worker_sessions` |
| `execution_logs` | `model_id` | `models` |
| `execution_logs` | `handoff_id` | `handoff_records` |

---

## 十、变更日志

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-06-25 | v2.0 | 按 6 份 PRD 重写：统一状态枚举、对齐所有数据对象字段、补充 WorkspaceState 和对象关系图 |
| 2026-06-24 | v1.0 | 初始版本（早期草稿，状态枚举与 PRD 冲突） |
