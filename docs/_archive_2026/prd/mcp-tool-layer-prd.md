# MCP Tool Layer MVP 技术型 PRD

> 所属产品：ModelGate Agent Studio
>
> 所属阶段：P2 核心能力
>
> 文档定位：MCP Tool Layer 的产品与技术需求说明，作为前端、后端、数据结构和验收实现依据。

---

## 1. 功能背景

ModelGate Agent Studio 是一个多模型 Agent 协作平台。当前 Runtime 引擎已能驱动 Agent 调用模型执行任务，但模型输出仅限于文本。Agent 无法：

1. 读取项目中的文件
2. 搜索代码库
3. 运行测试并获取结果
4. 查看 git diff 分析变更

在真实开发场景中，Agent 需要工具来感知和操作项目环境。MCP Tool Layer 提供一套最小可用的工具执行框架，让 Agent 在 Runtime 中真正能调用工具完成任务。

```text
当前: Model call → 文本输出 → 写入 task.output
目标: Model call → 可能返回 tool_calls → 执行工具 → 工具结果回传 → Model 继续 → 最终输出
```

---

## 2. 核心目标

- 提供 Tool Registry：后端统一管理工具定义（名称、参数 schema、风险级别、分类）
- 提供 Tool Executor：运行时执行工具调用（file_read, file_search, git_diff, test_runner）
- 集成 Runtime 工具调用循环：model → tool_calls → execute → tool_result → model → final_output
- Agent 工具权限在 Runtime 中生效：`allowed_tools` 控制 Agent 可调用哪些工具
- 工具调用全过程可观测：写入 execution_logs（event_type="tool_call"）
- 前端 Tool Manager 页面：查看、注册工具定义

### P0 scope（本轮）

- Tool Registry CRUD API
- 4 个内置工具：file_read, file_search, git_diff, test_runner
- Runtime 工具调用循环
- Agent 工具权限校验
- tool_call 日志记录
- 前端 Tool Manager 页面
- 前端 Workspace 展示工具调用记录

### P1 scope（延后）

- MCP 协议集成（外部 MCP Server 连接）
- 更多内置工具（file_write, terminal_execute, web_search, diff_view）
- 工具调用超时与重试
- 工具权限细粒度策略（per-task 限制）

---

## 3. 工具定义

### 3.1 ToolDefinition 数据对象

```text
id: UUID
name: string (唯一标识，如 "file_read")
display_name: string (展示名，如 "文件读取")
description: string (功能描述)
category: string (文件操作 / 终端 / 网络 / 代码 / 测试)
risk_level: "low" | "medium" | "high"
parameters: JSON (JSON Schema 格式参数定义)
is_enabled: boolean
created_at: datetime
updated_at: datetime
```

### 3.2 内置工具（MVP）

| name | display_name | category | risk_level | parameters |
|---|---|---|---|---|
| file_read | 文件读取 | 文件操作 | low | `{"path": {"type": "string", "description": "文件路径"}}` |
| file_search | 文件搜索 | 文件操作 | low | `{"pattern": {"type": "string"}, "dir": {"type": "string", "default": "."}}` |
| git_diff | Git 差异 | 代码 | low | `{"ref": {"type": "string", "default": "HEAD"}, "file": {"type": "string"}}` |
| test_runner | 测试运行 | 测试 | medium | `{"command": {"type": "string"}, "cwd": {"type": "string", "default": "."}}` |

### 3.3 ToolCallRecord 数据对象

```text
id: UUID
goal_id: UUID (FK → goals)
task_id: UUID (FK → tasks)
agent_id: UUID (FK → agent_stations)
worker_id: UUID (FK → worker_sessions)
tool_name: string
tool_input: JSON
tool_output: text
status: "started" | "completed" | "failed"
latency_ms: int
error_message: string?
created_at: datetime
```

---

## 4. 工具调用循环设计

```
_execute_single_task():
  1. 选择模型（现有逻辑）
  2. 构建 messages（包含 agent.system_prompt + task.description）
  3. 将 agent.allowed_tools 转为 OpenAI tools 格式传入 ModelRequest.tools
  4. Model call（Provider.generate）
  5. 检查 response.finish_reason:
     a. "stop" → 写入 output，任务完成
     b. "tool_calls" → 进入工具调用循环:
        - 解析 response.tool_calls[]
        - 对每个 tool_call:
          * 校验 tool_name 在 Agent.allowed_tools 中 → 否则跳过/报错
          * 校验 tool_name 在 ToolRegistry 中且 is_enabled → 否则跳过
          * 调用 ToolExecutor.execute(tool_name, arguments)
          * 创建 tool_call 日志
          * 将 tool_result 追加到 messages
        - 回到步骤 4（循环，最多 max_tool_calls_per_task 次）
        - 达到上限 → 写最后一次输出
  6. 写入 task.output → 记录 quota → 完成任务
```

---

## 5. API 设计

### 5.1 Tool Registry CRUD

```
GET    /api/v1/tools?category=&risk_level=&is_enabled=&page=1&page_size=20
GET    /api/v1/tools/{tool_id}
POST   /api/v1/tools
PUT    /api/v1/tools/{tool_id}
DELETE /api/v1/tools/{tool_id}
PATCH  /api/v1/tools/{tool_id}/toggle
```

### 5.2 Tool Call 查询

```
GET    /api/v1/tools/calls?goal_id=&task_id=&agent_id=&tool_name=&page=1&page_size=20
GET    /api/v1/tools/calls/{call_id}
```

### 5.3 响应格式

沿用现有统一格式 `{ success: boolean, data?: object, error?: { code, message } }`。

---

## 6. 现有依赖

| 依赖项 | 状态 | 说明 |
|--------|------|------|
| Runtime Engine | 已完成 | `runtime_service.py` 的 `_execute_single_task` |
| ModelProvider 接口 | 已完成 | `providers/base.py` 的 `ModelRequest/ModelResponse` |
| Agent Station | 已完成 | `allowed_tools`、`max_tool_calls_per_task` 字段 |
| Execution Logs | 已完成 | `tool_call` 事件类型、`tool_name` 字段 |
| Workspace | 已完成 | Task 详情面板展示 |

---

## 7. 不与以下模块耦合

- Supervisor Review（工具调用不影响审核逻辑）
- Memory/Skill Evolution（工具调用日志作为记忆素材，但不由本模块触发）
- Handoff Manager（工具调用中不触发 handoff）
- Quota Manager（工具调用不消耗 quota，仅 model call 消耗）

---

## 8. 验收标准

1. `GET /tools` 返回内置工具列表
2. `POST /tools` 可注册新工具定义
3. Runtime 执行时，若 Mock Provider 模拟返回 tool_calls，实际调用对应工具
4. 工具调用受 `Agent.allowed_tools` 权限控制
5. 每次工具调用产生 `tool_call` 类型日志
6. 前端 `/tools` 页面可查看工具列表
7. Workspace Task 详情面板展示工具调用记录
8. 所有现有 330 测试保持通过
9. 新增后端测试覆盖工具 CRUD + 执行引擎
10. 新增前端测试覆盖 ToolManagerPage
