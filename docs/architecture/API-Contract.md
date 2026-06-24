# API Contract 文档

> 🚧 **前后端开发前必读**：本文档定义所有接口的请求响应格式。
>
> 前后端必须严格遵循此文档开发。

---

## 通用约定

### Base URL

```
http://localhost:8000/api/v1
```

### 请求头

所有 API 请求都需要：

```http
Content-Type: application/json
```

### 响应格式

**成功响应：**

```json
{
  "success": true,
  "data": {},
  "message": "操作成功"
}
```

**失败响应：**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {}
  }
}
```

### 分页参数

```
GET /api/v1/xxx?page=1&page_size=20
```

分页响应：

```json
{
  "success": true,
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

### 错误码

| HTTP 状态码 | 错误码 | 说明 |
|------------|--------|------|
| 400 | BAD_REQUEST | 请求参数错误 |
| 404 | NOT_FOUND | 资源不存在 |
| 409 | CONFLICT | 资源冲突 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

---

## 一、Goal 相关接口

### 1.1 创建 Goal

```
POST /goals
```

**请求体：**

```json
{
  "title": "简短标题",
  "description": "详细的目标描述...",
  "user_constraints": "可选的约束条件",
  "priority": "medium",
  "allowed_agents": ["planner", "coder", "reviewer"],
  "allowed_models": ["model-uuid-1", "model-uuid-2"],
  "allow_handoff": true
}
```

**响应：201 Created**

```json
{
  "success": true,
  "data": {
    "id": "goal-uuid",
    "title": "简短标题",
    "description": "详细的目标描述...",
    "status": "created",
    "progress": 0,
    "priority": "medium",
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

---

### 1.2 获取 Goal 列表

```
GET /goals?page=1&page_size=20&status=in_progress
```

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| page | number | 页码，默认 1 |
| page_size | number | 每页数量，默认 20 |
| status | string | 可选，按状态筛选 |

**响应：200 OK**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "goal-uuid",
        "title": "标题",
        "status": "in_progress",
        "progress": 65,
        "total_tasks": 5,
        "completed_tasks": 3,
        "created_at": "2024-01-01T12:00:00Z"
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 1.3 获取单个 Goal 详情

```
GET /goals/:goalId
```

**响应：200 OK**

```json
{
  "success": true,
  "data": {
    "id": "goal-uuid",
    "title": "标题",
    "description": "详细描述...",
    "status": "in_progress",
    "progress": 65,
    "priority": "medium",
    "total_tasks": 5,
    "completed_tasks": 3,
    "handoff_count": 1,
    "total_tokens_used": 12500,
    "total_duration_ms": 120000,
    "final_summary": null,
    "created_at": "2024-01-01T12:00:00Z",
    "started_at": "2024-01-01T12:01:00Z",
    "tasks": [
      {
        "id": "task-uuid",
        "title": "任务标题",
        "status": "completed",
        "assigned_agent_id": "agent-uuid"
      }
    ]
  }
}
```

---

### 1.4 启动 Goal（开始拆解并执行）

```
POST /goals/:goalId/start
```

**请求体：**

```json
{
  "auto_plan": true,
  "auto_execute": true
}
```

**响应：200 OK**

```json
{
  "success": true,
  "data": {
    "goal_id": "goal-uuid",
    "status": "planning",
    "message": "Planner Agent 正在拆解任务"
  }
}
```

---

### 1.5 暂停 Goal

```
POST /goals/:goalId/pause
```

**响应：200 OK**

```json
{
  "success": true,
  "data": {
    "goal_id": "goal-uuid",
    "status": "paused"
  }
}
```

---

### 1.6 继续 Goal

```
POST /goals/:goalId/resume
```

**响应：200 OK**

```json
{
  "success": true,
  "data": {
    "goal_id": "goal-uuid",
    "status": "in_progress"
  }
}
```

---

## 二、Task 相关接口

### 2.1 获取 Goal 下的 Task 列表

```
GET /goals/:goalId/tasks
```

**响应：200 OK**

```json
{
  "success": true,
  "data": [
    {
      "id": "task-uuid",
      "goal_id": "goal-uuid",
      "title": "任务标题",
      "description": "任务描述",
      "status": "running",
      "priority": "high",
      "assigned_agent_id": "agent-uuid",
      "assigned_agent_name": "Coder Agent",
      "assigned_model_name": "DeepSeek Coder",
      "dependencies": ["parent-task-uuid"],
      "output": "输出内容...",
      "tokens_used": 2500,
      "duration_ms": 45000,
      "handoff_count": 0,
      "created_at": "2024-01-01T12:00:00Z",
      "started_at": "2024-01-01T12:05:00Z"
    }
  ]
}
```

---

### 2.2 获取单个 Task 详情

```
GET /tasks/:taskId
```

**响应：200 OK**

```json
{
  "success": true,
  "data": {
    "id": "task-uuid",
    "goal_id": "goal-uuid",
    "title": "任务标题",
    "description": "详细描述...",
    "completion_criteria": "完成标准...",
    "status": "running",
    "assigned_agent_id": "agent-uuid",
    "assigned_worker_id": "worker-uuid",
    "output": "完整输出内容...",
    "handoff_history": [
      {
        "handoff_id": "handoff-uuid",
        "from_agent": "Old Agent",
        "to_agent": "New Agent",
        "reason": "quota_exceeded",
        "created_at": "2024-01-01T12:10:00Z"
      }
    ]
  }
}
```

---

### 2.3 手动运行 Task

```
POST /tasks/:taskId/run
```

**请求体（可选）：**

```json
{
  "model_id": "specific-model-uuid",
  "force_rerun": false
}
```

**响应：200 OK**

```json
{
  "success": true,
  "data": {
    "task_id": "task-uuid",
    "status": "running",
    "worker_id": "new-worker-uuid"
  }
}
```

---

### 2.4 手动触发 Task 的 Handoff

```
POST /tasks/:taskId/handoff
```

**请求体：**

```json
{
  "to_agent_id": "target-agent-uuid",
  "reason": "manual",
  "reason_description": "用户手动选择交接"
}
```

**响应：200 OK**

```json
{
  "success": true,
  "data": {
    "handoff_id": "handoff-uuid",
    "status": "generating_summary",
    "message": "正在生成交接摘要..."
  }
}
```

---

## 三、Agent 相关接口

### 3.1 获取 Agent 列表

```
GET /agents
```

**响应：200 OK**

```json
{
  "success": true,
  "data": [
    {
      "id": "agent-uuid",
      "name": "Planner Agent",
      "role": "planner",
      "description": "负责拆解目标为可执行任务",
      "status": "idle",
      "default_model_name": "Claude 3 Opus",
      "total_tasks_completed": 156
    }
  ]
}
```

---

### 3.2 获取单个 Agent 详情

```
GET /agents/:agentId
```

**响应：200 OK**

```json
{
  "success": true,
  "data": {
    "id": "agent-uuid",
    "name": "Planner Agent",
    "role": "planner",
    "description": "...",
    "status": "idle",
    "current_task_id": null,
    "default_model_id": "model-uuid",
    "backup_model_ids": ["backup-model-uuid"],
    "system_prompt": "完整的系统提示词...",
    "allowed_tools": [],
    "allow_handoff": true
  }
}
```

---

### 3.3 创建 Agent

```
POST /agents
```

**请求体：**

```json
{
  "name": "自定义 Agent",
  "role": "custom",
  "description": "描述",
  "default_model_id": "model-uuid",
  "system_prompt": "系统提示词...",
  "allow_handoff": true
}
```

**响应：201 Created**

---

### 3.4 更新 Agent

```
PATCH /agents/:agentId
```

**请求体（只传要更新的字段）：**

```json
{
  "name": "新名称",
  "default_model_id": "new-model-uuid"
}
```

**响应：200 OK**

---

## 四、Model 相关接口

### 4.1 获取模型列表

```
GET /models
```

**响应：200 OK**

```json
{
  "success": true,
  "data": [
    {
      "id": "model-uuid",
      "provider": "anthropic",
      "provider_name": "Anthropic",
      "model_name": "claude-3-opus-20240229",
      "display_name": "Claude 3 Opus",
      "capability_tags": ["code", "planning", "long-context"],
      "max_context_tokens": 200000,
      "cost_level": 5,
      "speed_level": 3,
      "is_enabled": true,
      "is_default": true,
      "quota_token_daily_used": 45000,
      "quota_token_daily_limit": 100000,
      "last_used_at": "2024-01-01T12:30:00Z"
    }
  ]
}
```

---

### 4.2 创建/配置模型

```
POST /models
```

**请求体：**

```json
{
  "provider": "openai",
  "model_name": "gpt-4-turbo-preview",
  "display_name": "GPT-4 Turbo",
  "api_key": "sk-xxx",
  "base_url": "https://api.openai.com/v1",
  "capability_tags": ["code", "planning"],
  "max_context_tokens": 128000,
  "cost_level": 4,
  "speed_level": 3,
  "quota_token_daily_limit": 50000
}
```

**响应：201 Created**

---

### 4.3 测试模型连接

```
POST /models/:modelId/test
```

**响应：200 OK**

```json
{
  "success": true,
  "data": {
    "connected": true,
    "latency_ms": 456,
    "message": "连接成功"
  }
}
```

---

## 五、Handoff 相关接口

### 5.1 获取 Handoff 列表

```
GET /handoffs?goal_id=xxx&task_id=xxx
```

**响应：200 OK**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "handoff-uuid",
        "goal_id": "goal-uuid",
        "task_id": "task-uuid",
        "from_agent_name": "Old Coder Agent",
        "from_model_name": "Claude",
        "to_agent_name": "New Coder Agent",
        "to_model_name": "DeepSeek",
        "reason": "quota_exceeded",
        "status": "completed",
        "result_after_handoff": "success",
        "created_at": "2024-01-01T12:10:00Z"
      }
    ],
    "total": 10
  }
}
```

---

### 5.2 获取 Handoff 详情（含完整摘要）

```
GET /handoffs/:handoffId
```

**响应：200 OK**

```json
{
  "success": true,
  "data": {
    "id": "handoff-uuid",
    "goal_id": "goal-uuid",
    "task_id": "task-uuid",
    "from_agent_id": "old-agent-uuid",
    "from_model_id": "old-model-uuid",
    "to_agent_id": "new-agent-uuid",
    "to_model_id": "new-model-uuid",
    "reason": "quota_exceeded",
    "reason_description": "Claude 当日 token 用量已达 80%",
    "handoff_summary": {
      "original_goal": "...",
      "current_task": "...",
      "completed_work": ["..."],
      "unfinished_work": ["..."],
      "important_constraints": ["..."],
      "key_decisions": ["..."],
      "errors_and_risks": ["..."],
      "next_suggested_steps": ["..."],
      "context_needed": ["..."]
    },
    "status": "completed",
    "result_after_handoff": "success",
    "created_at": "2024-01-01T12:10:00Z",
    "completed_at": "2024-01-01T12:11:00Z"
  }
}
```

---

## 六、Logs 相关接口

### 6.1 获取执行日志

```
GET /logs?goal_id=xxx&task_id=xxx&level=error&page=1&page_size=50
```

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| goal_id | string | 可选，按 Goal 筛选 |
| task_id | string | 可选，按 Task 筛选 |
| agent_id | string | 可选，按 Agent 筛选 |
| level | string | 可选，按级别筛选 |
| page | number | 页码 |
| page_size | number | 每页数量 |

**响应：200 OK**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "log-uuid",
        "goal_id": "goal-uuid",
        "task_id": "task-uuid",
        "agent_id": "agent-uuid",
        "level": "exec",
        "action": "调用模型",
        "message": "调用 Claude 3 Opus 执行任务",
        "model_call_details": {
          "prompt_tokens": 1500,
          "completion_tokens": 800,
          "total_tokens": 2300,
          "latency_ms": 3200
        },
        "created_at": "2024-01-01T12:10:00Z"
      }
    ],
    "total": 156
  }
}
```

---

## 七、Quota 相关接口

### 7.1 获取额度概览

```
GET /quota/overview
```

**响应：200 OK**

```json
{
  "success": true,
  "data": {
    "models": [
      {
        "model_id": "model-uuid",
        "display_name": "Claude 3 Opus",
        "today_tokens_used": 45000,
        "today_token_limit": 100000,
        "token_usage_percent": 45,
        "today_requests_used": 23,
        "today_request_limit": 100,
        "request_usage_percent": 23,
        "status": "normal"
      },
      {
        "model_id": "model-uuid-2",
        "display_name": "GPT-4 Turbo",
        "token_usage_percent": 88,
        "status": "warning"
      }
    ],
    "warnings": [
      "GPT-4 Turbo 今日 token 用量已达 88%"
    ]
  }
}
```

---

### 7.2 获取某模型的额度历史

```
GET /quota/models/:modelId/history?days=7
```

**响应：200 OK**

```json
{
  "success": true,
  "data": [
    {
      "date": "2024-01-01",
      "request_count": 45,
      "total_tokens": 67800
    }
  ]
}
```

---

## 八、Dashboard 相关接口

### 8.1 获取 Dashboard 统计数据

```
GET /dashboard/stats
```

**响应：200 OK**

```json
{
  "success": true,
  "data": {
    "active_goals_count": 3,
    "completed_goals_today": 2,
    "total_tokens_today": 125600,
    "handoffs_today": 1,
    "agents_status": [
      {
        "agent_id": "uuid",
        "name": "Planner Agent",
        "status": "idle"
      }
    ],
    "recent_goals": [
      {
        "id": "goal-uuid",
        "title": "最近的目标",
        "status": "in_progress",
        "progress": 65,
        "created_at": "2024-01-01T12:00:00Z"
      }
    ]
  }
}
```

---

## 九、WebSocket 接口（实时更新）

### 连接地址

```
ws://localhost:8000/ws/workspace
```

### 订阅消息

连接后，前端可以发送订阅消息：

```json
{
  "action": "subscribe",
  "goal_id": "goal-uuid"
}
```

### 服务端推送的消息类型

#### 1. Task 状态更新

```json
{
  "type": "task_status_updated",
  "task_id": "task-uuid",
  "old_status": "pending",
  "new_status": "running",
  "assigned_agent_id": "agent-uuid"
}
```

#### 2. 新的执行日志

```json
{
  "type": "new_log",
  "log": {
    "id": "log-uuid",
    "level": "exec",
    "message": "Agent 开始执行任务",
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

#### 3. Handoff 事件

```json
{
  "type": "handoff_started",
  "handoff_id": "handoff-uuid",
  "task_id": "task-uuid",
  "from_agent_id": "old-agent-uuid",
  "to_agent_id": "new-agent-uuid"
}
```

#### 4. Goal 进度更新

```json
{
  "type": "goal_progress_updated",
  "goal_id": "goal-uuid",
  "progress": 75,
  "completed_tasks": 4,
  "total_tasks": 5
}
```

---

## 十、接口开发顺序建议

按优先级开发：

```
P0 - 第一天就要用的：
1. GET/POST /goals - 创建和查询 Goal
2. POST /goals/:id/start - 启动 Goal
3. GET /goals/:id/tasks - 获取 Task 列表
4. GET /tasks/:id - 获取 Task 详情
5. POST /tasks/:id/run - 运行 Task
6. GET /logs - 获取日志

P1 - 核心功能：
7. POST /tasks/:id/handoff - 触发交接
8. GET /agents - Agent 列表
9. GET /models - 模型列表
10. GET /handoffs - 交接历史

P2 - 周边功能：
11. PATCH /agents - 更新 Agent
12. POST/PATCH /models - 配置模型
13. GET /dashboard/stats - Dashboard 数据
14. GET /quota/overview - 额度概览

P3 - 实时性：
15. WebSocket - 实时更新
```

---

## 十一、前端 Mock 数据建议

在后端开发完成前，前端可以用 Mock 数据开发页面。建议 Mock：

1. Goal 列表：3-5 个，状态分布合理
2. Task 列表：每个 Goal 下 3-5 个 Task
3. Agent 列表：5 个标准 Agent
4. Model 列表：3-4 个常用模型
5. Logs：10-20 条不同级别的日志
6. Handoff：1-2 条完整的交接记录

Mock 数据的字段名和结构必须和本文档一致，这样后端开发完成后前端只需改 API 地址即可。

---

## 十、Workspace State 数据结构（前端渲染专用）

### 10.1 Workspace State（双视图共享底层状态）

这是前端 Store 中的核心状态结构，两个 Renderer 都基于此数据渲染。

```typescript
type WorkspaceView = 'card-flow' | 'pixel-office';

type AgentStatus =
  | 'idle'
  | 'queued'
  | 'running'
  | 'waiting'
  | 'reviewing'
  | 'handoff'
  | 'blocked'
  | 'error'
  | 'done';

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

### 10.2 Card Flow View 渲染数据

```typescript
type CardFlowNode = {
  id: string;
  agentId: string;
  title: string;
  modelName: string;
  status: AgentStatus;
  taskTitle: string;
  progress: number;
  tokensUsed: number;
  collapsed: boolean;
  position: { x: number; y: number };
};

type CardFlowEdge = {
  id: string;
  from: string;
  to: string;
  status: 'planned' | 'active' | 'done' | 'handoff' | 'error';
  handoffId?: string;
};

type CardFlowData = {
  nodes: CardFlowNode[];
  edges: CardFlowEdge[];
  completedAgents: CardFlowNode[];
};
```

### 10.3 Pixel Office View 渲染数据

```typescript
type PixelStation = {
  id: string;
  agentId: string;
  stationName: string;
  position: { x: number; y: number };
  status: AgentStatus;
  currentWorkerId?: string;
  currentTaskId?: string;
  currentTaskTitle?: string;
};

type PixelWorkerAnimation =
  | 'idle'
  | 'entering'
  | 'walking'
  | 'working'
  | 'handoff_give'
  | 'handoff_receive'
  | 'leaving';

type PixelWorker = {
  id: string;
  modelName: string;
  agentId: string;
  position: { x: number; y: number };
  targetStationId: string;
  animationState: PixelWorkerAnimation;
};

type HandoffFolder = {
  id: string;
  handoffId: string;
  fromStationId: string;
  toStationId: string;
  position: { x: number; y: number };
  animationState: 'appearing' | 'flying' | 'landing';
};

type PixelOfficeData = {
  stations: PixelStation[];
  workers: PixelWorker[];
  handoffFolders: HandoffFolder[];
  cameraPosition: { x: number; y: number };
  zoom: number;
};
```
