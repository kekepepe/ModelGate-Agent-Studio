# 数据结构与数据库 Schema 文档

> 🚧 **开发前必读**：本文档定义所有核心数据对象的字段和状态枚举。
>
> 代码中的数据结构必须与本文档严格一致。

---

## 一、状态枚举总览

**所有状态枚举必须定义在代码的常量文件中，不可用硬编码字符串。**

```typescript
// Goal 状态
type GoalStatus = 'created' | 'planning' | 'in_progress' | 'reviewing' | 'completed' | 'failed';

// Task 状态
type TaskStatus = 'pending' | 'assigned' | 'running' | 'waiting' | 'handoff' | 'completed' | 'failed';

// Agent Station 状态
type AgentStatus = 'idle' | 'busy' | 'handoff';

// Worker Session 状态
type WorkerStatus = 'idle' | 'running' | 'handoff_required' | 'completed' | 'failed';

// Handoff 状态
type HandoffStatus = 'requested' | 'generating_summary' | 'ready' | 'accepted' | 'completed' | 'failed';

// Provider 类型
type ProviderType = 'openai' | 'anthropic' | 'deepseek' | 'kimi' | 'mock';

// Log 级别
type LogLevel = 'info' | 'exec' | 'done' | 'handoff' | 'warn' | 'error';
```

---

## 二、核心表结构

### 2.1 Goal 表

用户输入的目标，是所有任务的根节点。

```typescript
interface Goal {
  // 主键
  id: string;                    // UUID

  // 基本信息
  title: string;                 // 目标标题（自动生成的简短标题）
  description: string;           // 用户输入的完整描述
  user_constraints?: string;     // 用户附加的约束条件

  // 状态
  status: GoalStatus;
  progress: number;              // 0-100，整体进度

  // 配置
  priority: 'low' | 'medium' | 'high';
  allowed_agents: string[];      // 允许的 Agent 类型列表
  allowed_models: string[];      // 允许的模型 ID 列表
  allow_handoff: boolean;        // 是否允许自动交接

  // 统计
  total_tasks: number;
  completed_tasks: number;
  handoff_count: number;
  total_tokens_used: number;
  total_duration_ms: number;

  // 结果
  final_summary?: string;        // Supervisor 生成的最终汇总
  output_format?: 'markdown' | 'json';

  // 时间戳
  created_at: Date;
  started_at?: Date;
  completed_at?: Date;
  updated_at: Date;
}
```

**索引建议**：
- `status` - 查询进行中的 Goal
- `created_at` - 按时间排序
- `id` - 主键

---

### 2.2 Task 表

从 Goal 拆解出来的具体任务。

```typescript
interface Task {
  // 主键
  id: string;                    // UUID

  // 关联
  goal_id: string;               // 所属 Goal ID
  parent_task_id?: string;       // 父任务 ID（如果有）

  // 基本信息
  title: string;                 // 任务标题
  description: string;           // 任务描述
  completion_criteria?: string;  // 任务完成标准

  // 状态
  status: TaskStatus;
  priority: 'low' | 'medium' | 'high';

  // 分配
  assigned_agent_id?: string;    // 分配的 Agent Station ID
  assigned_worker_id?: string;   // 当前执行的 Worker Session ID

  // 依赖
  dependencies: string[];        // 前置依赖 Task ID 列表

  // 输出
  output?: string;               // Agent 输出内容
  output_format?: 'markdown' | 'json' | 'code';

  // 统计
  tokens_used: number;
  duration_ms: number;
  retry_count: number;

  // Handoff 信息
  handoff_count: number;
  last_handoff_id?: string;      // 最近一次交接记录 ID

  // 时间戳
  created_at: Date;
  assigned_at?: Date;
  started_at?: Date;
  completed_at?: Date;
  updated_at: Date;
}
```

**索引建议**：
- `goal_id` - 查询某个 Goal 的所有 Task
- `status` - 查询特定状态的 Task
- `assigned_agent_id` - 查询某 Agent 分配的 Task
- `parent_task_id` - 查询子任务

---

### 2.3 Agent Station 表

Agent 工位定义，代表一个固定职责的角色。

```typescript
interface AgentStation {
  // 主键
  id: string;                    // UUID

  // 基本信息
  name: string;                  // e.g. "Planner Agent", "Coder Agent"
  role: string;                  // 'planner' | 'coder' | 'reviewer' | 'summarizer' | 'supervisor'
  description: string;           // 该 Agent 的职责说明

  // 状态
  status: AgentStatus;
  current_task_id?: string;      // 当前正在执行的 Task ID

  // 模型配置
  default_model_id: string;      // 默认使用的模型
  backup_model_ids: string[];    // 备用模型列表

  // 工具权限
  allowed_tools: string[];       // 允许使用的工具 ID 列表
  max_tool_calls_per_task: number;

  // Prompt 配置
  system_prompt: string;         // 该角色的系统提示词
  output_format_requirement?: string;  // 输出格式要求

  // 执行限制
  max_steps_per_task: number;    // 单任务最大执行步数
  allow_handoff: boolean;        // 是否允许交接
  handoff_threshold_tokens: number;  // 触发交接的 token 阈值

  // 统计
  total_tasks_completed: number;
  total_handoffs_initiated: number;
  average_tokens_per_task: number;

  // 时间戳
  created_at: Date;
  updated_at: Date;
}
```

**索引建议**：
- `role` - 按角色查询
- `status` - 查询空闲 Agent
- `default_model_id` - 查询使用某模型的 Agent

---

### 2.4 Model 表

模型定义，包括 Provider 和具体模型名称。

```typescript
interface Model {
  // 主键
  id: string;                    // UUID

  // Provider 信息
  provider: ProviderType;
  provider_name: string;         // 显示名，如 "OpenAI", "Anthropic"

  // 模型信息
  model_name: string;            // API 调用时的模型名，如 "gpt-4", "claude-3-opus"
  display_name: string;          // 显示名，如 "GPT-4", "Claude 3 Opus"

  // 能力标签
  capability_tags: string[];     // e.g. ['code', 'planning', 'long-context', 'vision']
  max_context_tokens: number;    // 最大上下文长度
  supports_vision: boolean;
  supports_code_interpreter: boolean;
  supports_function_calling: boolean;

  // 成本信息（用于路由决策）
  cost_level: number;            // 1-5，成本等级，越低越便宜
  speed_level: number;           // 1-5，速度等级，越低越快

  // 额度配置
  quota_daily_limit?: number;     // 每日额度上限（请求次数）
  quota_daily_used: number;
  quota_token_daily_limit?: number;  // 每日 token 上限
  quota_token_daily_used: number;

  // API 配置
  api_key?: string;               // 加密存储
  base_url?: string;              // 自定义 API 端点
  custom_headers?: Record<string, string>;

  // 状态
  is_enabled: boolean;
  is_default: boolean;

  // 统计
  total_calls: number;
  total_tokens_used: number;
  total_handoffs_triggered: number;

  // 时间戳
  created_at: Date;
  updated_at: Date;
  last_used_at?: Date;
}
```

**索引建议**：
- `provider` - 按 Provider 查询
- `is_enabled` - 查询可用模型
- `capability_tags` - 按能力搜索

---

### 2.5 Worker Session 表

Agent 执行一个 Task 的具体会话实例。

```typescript
interface WorkerSession {
  // 主键
  id: string;                    // UUID

  // 关联
  agent_id: string;              // 所属 Agent Station ID
  model_id: string;              // 使用的模型 ID
  goal_id: string;               // 所属 Goal ID
  task_id: string;               // 正在执行的 Task ID

  // 承接 Handoff 的情况
  inherited_from_handoff_id?: string;  // 如果是交接来的，来源 Handoff 记录 ID

  // 状态
  status: WorkerStatus;

  // 上下文
  current_context?: string;       // 当前累积的上下文
  system_prompt_used: string;     // 实际使用的 System Prompt
  retrieved_memories?: string[];  // 检索到的 Memory ID 列表（v0.2+）

  // 执行记录
  step_count: number;              // 已执行步数
  tool_calls_made: number;
  errors_encountered: number;

  // Token 统计
  input_tokens_used: number;
  output_tokens_used: number;
  total_tokens_used: number;

  // 结果
  final_output?: string;
  error_message?: string;

  // 时间戳
  started_at: Date;
  last_step_at?: Date;
  completed_at?: Date;
}
```

**索引建议**：
- `task_id` - 查询 Task 的所有 Worker
- `agent_id` - 查询 Agent 的历史
- `status` - 查询活跃的 Worker

---

### 2.6 Handoff Record 表

任务交接记录，是产品核心差异化的数据基础。

```typescript
interface HandoffRecord {
  // 主键
  id: string;                    // UUID

  // 关联
  goal_id: string;
  task_id: string;

  // 交接双方
  from_agent_id: string;         // 交出的 Agent
  from_model_id: string;          // 交出的模型
  to_agent_id: string;           // 接手的 Agent
  to_model_id: string;            // 接手的模型

  // 交接原因
  reason: 'quota_exceeded' | 'error' | 'role_mismatch' | 'manual' | 'other';
  reason_description?: string;

  // 交接摘要（核心）
  handoff_summary: {
    original_goal: string;
    current_task: string;
    completed_work: string[];
    unfinished_work: string[];
    important_constraints: string[];
    key_decisions: string[];
    errors_and_risks: string[];
    next_suggested_steps: string[];
    context_needed: string[];
  };

  // 交接结果
  status: HandoffStatus;
  result_after_handoff?: 'success' | 'failed' | 'partial';
  time_saved_estimate_ms?: number;  // 估计因为交接节省的时间

  // 交接前后对比
  tokens_before_handoff: number;
  tokens_after_handoff: number;

  // 时间戳
  created_at: Date;
  summary_generated_at?: Date;
  accepted_at?: Date;
  completed_at?: Date;
}
```

**索引建议**：
- `goal_id` - 查询 Goal 的交接历史
- `task_id` - 查询 Task 的交接历史
- `from_agent_id` / `to_agent_id` - 查询 Agent 的交接记录
- `reason` - 按原因统计

---

### 2.7 Execution Log 表

执行日志，详细记录每一步操作。

```typescript
interface ExecutionLog {
  // 主键
  id: string;                    // UUID

  // 关联（都可以为空，表示全局日志）
  goal_id?: string;
  task_id?: string;
  agent_id?: string;
  worker_id?: string;
  model_id?: string;
  handoff_id?: string;

  // 日志内容
  level: LogLevel;
  action: string;                 // 简短动作描述，如 "开始执行", "调用模型", "生成输出"
  message: string;                // 详细内容

  // 模型调用详情（如果是模型调用）
  model_call_details?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    latency_ms: number;
    error?: string;
  };

  // 工具调用详情（如果是工具调用，v0.2+）
  tool_call_details?: {
    tool_name: string;
    parameters: Record<string, any>;
    result?: string;
    error?: string;
    latency_ms: number;
  };

  // 时间戳
  created_at: Date;
}
```

**索引建议**：
- `goal_id` - 查询 Goal 的所有日志
- `task_id` - 查询 Task 的所有日志
- `level` - 按级别筛选
- `created_at` - 按时间排序

---

### 2.8 Quota Usage 表

额度使用记录（比 Model 表更细粒度的统计）。

```typescript
interface QuotaUsage {
  id: string;
  model_id: string;

  // 时间维度
  date: string;                   // YYYY-MM-DD
  hour?: number;                  // 0-23，小时级统计（可选）

  // 使用统计
  request_count: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;

  // 限制
  daily_request_limit?: number;
  daily_token_limit?: number;

  // 计算字段
  request_usage_percent: number;  // 0-100
  token_usage_percent: number;    // 0-100

  created_at: Date;
  updated_at: Date;
}
```

**索引建议**：
- `model_id + date` - 唯一索引，查询某模型某天的用量
- `date` - 按日期统计

---

## 三、v0.2+ 预留表结构（暂不实现）

### Memory Item 表（v0.2+）

```typescript
// 本地知识库中的记忆条目
interface MemoryItem {
  id: string;
  type: 'project_memory' | 'user_preference' | 'agent_experience' | 'general_knowledge';
  title: string;
  content: string;
  tags: string[];
  source_task_id?: string;
  confidence: number;  // 0-100
  human_approved: boolean;
  usage_count: number;
  embedding?: number[];  // 向量，用于 RAG
  expires_at?: Date;
  created_at: Date;
  updated_at: Date;
  last_used_at?: Date;
}
```

### Skill 表（v0.2+）

```typescript
// 可复用的任务执行模板
interface Skill {
  id: string;
  name: string;
  description: string;
  applicable_scenarios: string[];

  // 输入输出定义
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;

  // 步骤
  steps: {
    order: number;
    description: string;
    recommended_agent_role?: string;
    tool_required?: string;
  }[];

  // Prompt 模板
  prompt_template: string;

  // 统计
  usage_count: number;
  success_rate: number;
  average_duration_ms: number;

  version: string;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
}
```

---

## 四、数据库设计原则

### 4.1 选择数据库

**v0.1 建议用 SQLite**：
- 无需额外部署
- 本地开发方便
- 足够支撑 MVP 规模

**v0.2+ 可以迁移到 PostgreSQL**：
- 更好的 JSON 支持
- 更好的并发
- 向量扩展（pgvector）支持 RAG

### 4.2 ORM 建议

- TypeScript 项目推荐用 **Prisma**
- Python 项目推荐用 **SQLAlchemy**

### 4.3 数据迁移

- 所有 Schema 变更必须写迁移脚本
- 迁移脚本必须可以回滚
- 生产数据迁移前必须备份

---

## 五、验收标准

开发完成后必须能回答这些问题：

```
查询类：
1. 当前有哪些 Goal 正在进行中？
2. 某个 Goal 下有哪些 Task？各自的状态是什么？
3. 某个 Agent 历史上完成过多少 Task？
4. 某个模型今天用了多少 token？是否接近额度？
5. 某个 Task 发生过几次 Handoff？分别是什么原因？
6. 某个 Goal 的完整执行日志是什么？
```

```
写入类：
1. 可以创建 Goal 和 Task
2. 可以更新 Task 状态
3. 可以创建 Worker Session 并更新进度
4. 可以创建 Handoff Record 并生成摘要
5. 可以记录每一步的 Execution Log
6. 可以统计模型额度使用情况
```

---

## 五、前端渲染数据结构（Frontend Rendering Types）

> **注意**：以下类型仅用于前端渲染，不持久化到数据库。

### 5.1 Workspace State（Workspace 状态）

```typescript
type WorkspaceView = 'card-flow' | 'pixel-office';

type WorkspaceState = {
  goal: Goal;
  tasks: Task[];
  agents: Agent[];
  workers: WorkerSession[];
  edges: TaskEdge[];
  handoffs: HandoffRecord[];
  logs: ExecutionLog[];
  quota: QuotaStatus[];
  currentView: WorkspaceView;
  selectedEntityId?: string;
};
```

### 5.2 Card Flow View 渲染类型

```typescript
type CardFlowNode = {
  id: string;
  type: 'agent' | 'task' | 'handoff-summary' | 'completed';
  position: { x: number; y: number };
  status: AgentStatus;
  title: string;
  subtitle?: string;
  assignedAgent?: string;
  modelName?: string;
  tokenUsed?: number;
  handoffFrom?: string;
  isSelected: boolean;
  isHovered: boolean;
};

type CardFlowEdge = {
  id: string;
  source: string;
  target: string;
  type: 'planned' | 'active' | 'done' | 'handoff' | 'error' | 'waiting';
  animated?: boolean;
  label?: string;
};
```

### 5.3 Pixel Office View 渲染类型

```typescript
type PixelStation = {
  id: string;
  position: { x: number; y: number };
  agentType: string;
  status: AgentStatus;
  worker?: PixelWorker;
};

type PixelWorker = {
  id: string;
  modelName: string;
  status: AgentStatus;
  currentTaskId: string;
  animation: 'idle' | 'working' | 'handoff-give' | 'handoff-receive' | 'walking' | 'done';
  position: { x: number; y: number };
};

type HandoffFolder = {
  id: string;
  fromStation: string;
  toStation: string;
  position: { x: number; y: number };
  progress: number; // 0.0 ~ 1.0
  animationState: 'flying' | 'landing';
};
```
