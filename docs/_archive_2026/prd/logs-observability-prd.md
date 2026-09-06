# Logs / Observability 技术型 PRD

> 所属产品：ModelGate Agent Studio
>
> 所属阶段：MVP-A / MVP-B 核心基础设施
>
> 文档定位：Logs / Observability 模块的产品与技术需求说明，作为任务可观测性、错误排查、过程复盘和知识沉淀的实现依据。

---

## 1. 功能背景

ModelGate Agent Studio 是多模型 Agent 协作平台。一个 Goal 从输入到完成，可能经过以下完整链路：

```text
用户输入 Goal
  ↓
Planner 拆解 Task
  ↓
Model Router 选择模型
  ↓
Runtime 调用模型 API（Coder / Reviewer / Researcher）
  ↓
Agent 执行 Step（推理、工具调用、代码生成）
  ↓
Tool 执行（文件读写、代码执行、搜索）
  ↓
Reviewer / Supervisor 审核输出
  ↓
Handoff Manager 触发交接（额度不足 / 质量不足 / 角色切换）
  ↓
Summarizer 压缩上下文
  ↓
Runtime 完成 Task
  ↓
Workspace 展示结果
```

这个链路中，用户需要回答以下问题：

- "我的任务现在执行到哪一步了？"
- "为什么这个 Task 失败了？"
- "Coder 用了哪个模型？生成代码花了多少 token？"
- "Handoff 前后，上下文丢失了多少？"
- "Reviewer 为什么拒绝了 Coder 的输出？"
- "哪个 Agent 最费 token？哪个模型表现最好？"

如果没有结构化的可观测性，这些问题只能靠猜测。Logs / Observability 模块的目标是把黑盒执行过程变成白盒：

> **每一次模型调用、每一次 Agent 执行、每一次工具调用、每一次状态变化、每一次 Handoff，都被结构化记录，可被查询、筛选、复盘和分析。**

这不是普通的 console.log，而是面向 Agent 协作场景的执行档案系统。

---

## 2. 用户问题

### 2.1 主要用户

- 多模型重度使用的开发者
- 需要长时间推进复杂任务的独立开发者 / AI 产品经理 / 研究者
- 需要排查任务失败原因的技术用户

### 2.2 用户痛点

#### 痛点一：任务执行是黑盒，看不到过程

用户输入 Goal 后，系统开始自动执行。但用户只能看到最终结果，不知道中间发生了什么：

- 哪些 Agent 参与了执行？
- 每个 Agent 执行了哪些 Step？
- 模型调用成功了吗？返回了什么？
- 为什么执行了 10 分钟还没完成？

#### 痛点二：任务失败时无法定位原因

当 Task 失败时，用户想知道：

- 是模型返回了错误？
- 是工具执行失败了？
- 是 Handoff 过程中上下文丢失了？
- 是 Supervisor 审核不通过？
- 是额度不足导致的中断？

没有日志，用户只能重新执行一遍，或者手动检查每个环节。

#### 痛点三：Handoff 前后变化不可追溯

Handoff 是 ModelGate 的核心能力，但用户关心：

- 为什么触发了 Handoff？（额度不足？质量不足？角色切换？）
- Handoff 前，原 Agent 的输出是什么？
- Handoff 后，新 Agent 接收到了什么上下文？
- Handoff 过程中有没有信息丢失？

#### 痛点四：Token 和成本不可见

用户想优化成本，但不知道：

- 哪个 Agent 消耗了最多 token？
- 哪个模型性价比最高？
- 一次 Goal 执行总共花了多少 token？
- 哪些 Step 是浪费的（比如重复调用、无效输出）？

#### 痛点五：经验无法沉淀

每次任务执行都是一次学习机会。但当前执行完成后，所有的决策、错误、成功经验都随着会话结束而消失：

- 为什么这次 Coder 表现好？
- 为什么上次 Reviewer 漏掉了 bug？
- 某个 Task 类型应该用哪个模型？
- 哪些工具组合最有效？

### 2.3 核心问题

Logs / Observability 要回答的问题是：

> 如何结构化记录 Agent 协作全链路的执行过程，让用户能够复盘任务、定位错误、对比 Handoff 前后变化、统计 token 消耗，并为后续的 Memory 和 Skill 沉淀提供数据基础？

---

## 3. 产品目标

### 3.1 核心目标

1. **全链路记录**：记录每次模型调用、Agent 执行、工具调用、状态变化、Handoff、额度变化。
2. **可查询筛选**：支持按 Goal、Task、Agent、Model、Event Type、Status、时间范围筛选。
3. **可复盘分析**：支持查看单个 Task 的完整执行链路，理解执行过程。
4. **Handoff 对比**：支持 Handoff 前后上下文对比，评估信息传递质量。
5. **错误定位**：支持快速定位任务失败的根因。
6. **知识沉淀**：日志结构支持后续 Knowledge Evolution Agent 提取经验。

### 3.2 体验目标

- 用户能在 Workspace 的 Logs Panel 中实时看到任务执行过程。
- 用户能点击任意日志查看详情，包括输入输出摘要、token 消耗、状态变化。
- 用户能筛选特定类型的日志（只看错误、只看 Handoff、只看模型调用）。
- 用户能查看某个 Task 的时间线，理解执行的先后顺序和依赖关系。
- 用户能对比 Handoff 前后的上下文，判断交接是否完整。

### 3.3 技术目标

- 日志采集为异步操作，不阻塞 Runtime 主流程。
- 日志存储支持本地文件 / SQLite（MVP），为后续迁移到结构化存储预留接口。
- 日志格式统一为结构化 JSON，支持程序解析。
- 日志量控制：自动清理超过保留期的日志，防止磁盘膨胀。

---

## 4. 日志类型设计

### 4.1 日志类型总览

| 类型 | 说明 | 产生时机 |
|------|------|----------|
| `model_call` | 模型 API 调用 | Runtime 发起模型调用前后 |
| `agent_step` | Agent 执行一个 Step | Agent 开始执行和完成执行时 |
| `tool_call` | 工具调用 | Tool 被调用和返回结果时 |
| `task_status_change` | Task 状态变化 | Task 状态发生流转时 |
| `quota_status_change` | 额度状态变化 | Quota Manager 判定状态变化时 |
| `handoff_created` | Handoff 被创建 | Handoff Manager 创建 HandoffRecord 时 |
| `handoff_completed` | Handoff 完成 | 接手 Agent 接受 Handoff 并继续执行时 |
| `error` | 错误事件 | 任何模块抛出错误时 |
| `supervisor_review` | Supervisor 审核 | Supervisor 审核 Agent 输出时 |
| `memory_write_candidate` | 记忆写入候选 | 系统识别出可沉淀为经验的事件时 |

### 4.2 各类型日志的详细定义

#### 4.2.1 model_call

记录每次模型 API 调用的完整信息：

```typescript
interface ModelCallLog {
  event_type: 'model_call';
  event_status: 'started' | 'completed' | 'failed';
  model_id: string;
  model_name: string;
  agent_id: string;
  task_id: string;
  goal_id: string;
  input_summary: string;        // 输入摘要（前 500 字符）
  output_summary: string;       // 输出摘要（前 500 字符）
  token_usage: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
  latency_ms: number;           // 调用延迟
  error_code?: string;          // 错误码（如有）
  error_message?: string;       // 错误信息（如有）
  routing_info?: {              // 路由信息
    routing_reason: string;
    confidence: number;
    risk_flags: string[];
  };
}
```

#### 4.2.2 agent_step

记录 Agent 执行一个 Step 的过程：

```typescript
interface AgentStepLog {
  event_type: 'agent_step';
  event_status: 'started' | 'completed' | 'failed' | 'skipped';
  agent_id: string;
  agent_role: string;           // planner, coder, reviewer, etc.
  task_id: string;
  goal_id: string;
  step_number: number;          // 当前是第几步
  step_name: string;            // 步骤名称
  input_summary: string;        // Step 输入摘要
  output_summary: string;       // Step 输出摘要
  token_usage: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
  duration_ms: number;          // Step 执行时长
  tool_calls?: string[];        // 本 Step 调用的工具列表
  reasoning?: string;           // Agent 的推理过程摘要（如有）
}
```

#### 4.2.3 tool_call

记录工具调用的执行过程：

```typescript
interface ToolCallLog {
  event_type: 'tool_call';
  event_status: 'started' | 'completed' | 'failed';
  tool_name: string;            // 工具名称
  tool_type: string;            // file_read, file_write, code_execute, search, etc.
  agent_id: string;
  task_id: string;
  goal_id: string;
  input_summary: string;        // 工具输入参数摘要
  output_summary: string;       // 工具返回结果摘要
  duration_ms: number;          // 工具执行时长
  error_message?: string;       // 错误信息
}
```

#### 4.2.4 task_status_change

记录 Task 状态流转：

```typescript
interface TaskStatusChangeLog {
  event_type: 'task_status_change';
  event_status: 'transition';
  task_id: string;
  goal_id: string;
  from_status: string;          // pending, running, completed, failed, etc.
  to_status: string;
  reason?: string;              // 状态变化原因
  triggered_by: 'system' | 'user' | 'agent' | 'handoff';
}
```

#### 4.2.5 quota_status_change

记录额度状态变化（与 Quota Manager 联动）：

```typescript
interface QuotaStatusChangeLog {
  event_type: 'quota_status_change';
  event_status: 'transition';
  model_id: string;
  model_name: string;
  from_status: string;          // normal, warning, near_limit, limited, cooldown, unknown
  to_status: string;
  usage_percent: number;
  total_tokens: number;
  limit_error_count: number;
  reason: string;
  triggered_by: 'system' | 'user' | 'handoff' | 'router';
}
```

#### 4.2.6 handoff_created

记录 Handoff 创建事件：

```typescript
interface HandoffCreatedLog {
  event_type: 'handoff_created';
  event_status: 'created';
  handoff_id: string;
  task_id: string;
  goal_id: string;
  from_agent_id: string;
  from_model_id: string;
  to_agent_id: string;
  to_model_id: string;
  handoff_reason: string;       // quota_exceeded, quality_insufficient, role_mismatch, manual
  trigger_type: 'auto' | 'manual';
  summary_length: number;       // HandoffSummary 的字符数
  context_tokens: number;       // 传递的上下文 token 数
}
```

#### 4.2.7 handoff_completed

记录 Handoff 完成事件：

```typescript
interface HandoffCompletedLog {
  event_type: 'handoff_completed';
  event_status: 'accepted' | 'rejected' | 'timeout';
  handoff_id: string;
  task_id: string;
  goal_id: string;
  from_agent_id: string;
  to_agent_id: string;
  acceptance_time_ms: number;   // 从创建到接受的时间
  context_loss_estimate?: number; // 估算的上下文损失比例
}
```

#### 4.2.8 error

记录错误事件：

```typescript
interface ErrorLog {
  event_type: 'error';
  event_status: 'error';
  error_type: string;           // api_error, tool_error, timeout, validation, etc.
  error_code?: string;          // 错误码
  error_message: string;        // 错误信息
  stack_trace?: string;         // 堆栈跟踪（开发模式）
  agent_id?: string;
  task_id?: string;
  goal_id?: string;
  model_id?: string;
  recoverable: boolean;         // 是否可恢复
  recovery_action?: string;     // 系统采取的恢复动作
}
```

#### 4.2.9 supervisor_review

记录 Supervisor 审核事件：

```typescript
interface SupervisorReviewLog {
  event_type: 'supervisor_review';
  event_status: 'approved' | 'rejected' | 'needs_revision';
  supervisor_agent_id: string;
  reviewed_agent_id: string;
  task_id: string;
  goal_id: string;
  review_criteria: string[];    // 审核维度
  issues_found?: string[];      // 发现的问题
  suggestions?: string[];       // 改进建议
  output_summary: string;       // 被审核的输出摘要
}
```

#### 4.2.10 memory_write_candidate

记录可沉淀为经验的事件：

```typescript
interface MemoryWriteCandidateLog {
  event_type: 'memory_write_candidate';
  event_status: 'detected';
  candidate_type: string;       // pattern, lesson, preference, tool_combo
  source_event_ids: string[];   // 来源日志 ID 列表
  task_id: string;
  goal_id: string;
  description: string;          // 候选经验描述
  confidence: number;           // 置信度
  suggested_tags: string[];     // 建议标签
}
```

---

## 5. 日志采集时机

### 5.1 采集原则

1. **异步采集**：日志写入不阻塞主流程，使用事件队列或后台任务。
2. **双写策略**：关键日志同时写入内存缓存（供前端实时展示）和持久化存储（供历史查询）。
3. **失败不重试**：日志写入失败不影响主流程，可丢失但需记录写入失败事件。
4. **批量写入**：非实时日志（如历史查询）支持批量写入，减少 I/O。

### 5.2 各模块采集时机

#### 5.2.1 Runtime 采集

| 时机 | 采集内容 | 日志类型 |
|------|----------|----------|
| 发起模型调用前 | model_id, agent_id, input_summary | model_call (started) |
| 收到模型响应后 | output_summary, token_usage, latency | model_call (completed/failed) |
| Agent 开始执行 Step | agent_id, step_name, input_summary | agent_step (started) |
| Agent 完成 Step | output_summary, token_usage, duration | agent_step (completed/failed) |
| 调用工具前 | tool_name, input_summary | tool_call (started) |
| 工具返回后 | output_summary, duration, error | tool_call (completed/failed) |
| 捕获错误时 | error_type, error_message, stack_trace | error |

#### 5.2.2 Task Service 采集

| 时机 | 采集内容 | 日志类型 |
|------|----------|----------|
| Task 状态变化 | from_status, to_status, reason | task_status_change |

#### 5.2.3 Handoff Manager 采集

| 时机 | 采集内容 | 日志类型 |
|------|----------|----------|
| 创建 HandoffRecord | handoff_id, from/to agent, reason | handoff_created |
| 接手 Agent 接受 Handoff | acceptance_time, context_loss | handoff_completed |

#### 5.2.4 Quota Manager 采集

| 时机 | 采集内容 | 日志类型 |
|------|----------|----------|
| 额度状态变化 | from_status, to_status, usage_percent | quota_status_change |

#### 5.2.5 Supervisor 采集

| 时机 | 采集内容 | 日志类型 |
|------|----------|----------|
| 审核 Agent 输出 | status, issues, suggestions | supervisor_review |

#### 5.2.6 Memory Service 采集（MVP-B）

| 时机 | 采集内容 | 日志类型 |
|------|----------|----------|
| 检测到可沉淀经验 | candidate_type, description, confidence | memory_write_candidate |

---

## 6. 日志字段设计

### 6.1 通用字段（所有日志类型共享）

```typescript
interface LogBase {
  // 标识
  log_id: string;               // UUID，唯一标识

  // 关联对象
  goal_id?: string;             // 所属 Goal
  task_id?: string;             // 所属 Task
  agent_id?: string;            // 所属 Agent
  worker_id?: string;           // 所属 Worker（模型实例）
  model_id?: string;            // 使用的模型

  // 事件信息
  event_type: LogEventType;     // 日志类型
  event_status: LogEventStatus; // 事件状态
  created_at: string;           // ISO 8601，事件发生时间

  // 内容摘要
  input_summary?: string;       // 输入摘要（前 500 字符）
  output_summary?: string;      // 输出摘要（前 500 字符）

  // Token 消耗
  token_usage?: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };

  // 额度状态（如有）
  quota_status?: string;        // 事件发生时的额度状态

  // Handoff 状态（如有）
  handoff_status?: string;      // 事件发生时的 Handoff 状态

  // 工具信息（如是工具调用）
  tool_name?: string;           // 工具名称

  // 错误信息（如是错误）
  error_message?: string;       // 错误信息

  // 扩展元数据
  metadata?: Record<string, any>; // 各类型特定的额外字段
}
```

### 6.2 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| log_id | 是 | UUID，全局唯一 |
| event_type | 是 | 日志类型，枚举值 |
| event_status | 是 | 事件状态，枚举值 |
| created_at | 是 | 事件发生时间 |
| goal_id | 否 | 允许独立事件（如系统级错误）不关联 Goal |
| task_id | 否 | 同上 |
| agent_id | 否 | 系统级事件可能无 Agent |
| model_id | 否 | 非模型调用事件可能无模型 |
| input_summary | 否 | 有输入的事件必填，限制 500 字符 |
| output_summary | 否 | 有输出的事件必填，限制 500 字符 |
| token_usage | 否 | 模型调用和 Agent Step 必填 |
| quota_status | 否 | 涉及额度的事件填写 |
| handoff_status | 否 | 涉及 Handoff 的事件填写 |
| tool_name | 否 | tool_call 必填 |
| error_message | 否 | error 类型必填 |
| metadata | 否 | 各类型特有字段，JSON 格式 |

### 6.3 摘要生成规则

- **input_summary**：取输入的前 500 字符，超过部分用 "..." 截断。
- **output_summary**：取输出的前 500 字符，代码块保留前 10 行，超过部分用 "..." 截断。
- **代码特殊处理**：如果是代码生成，output_summary 保留代码块标记（```language）和前 5 行代码。

---

## 7. 日志查询与筛选

### 7.1 查询接口

```
GET /logs
```

**查询参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| goal_id | string | 按 Goal 筛选 |
| task_id | string | 按 Task 筛选 |
| agent_id | string | 按 Agent 筛选 |
| model_id | string | 按 Model 筛选 |
| event_type | string[] | 按事件类型筛选（可多选） |
| event_status | string[] | 按事件状态筛选（可多选） |
| start_time | string | 开始时间（ISO 8601） |
| end_time | string | 结束时间（ISO 8601） |
| has_error | boolean | 是否只显示含错误的事件 |
| search | string | 关键词搜索（input_summary / output_summary / error_message） |
| sort_by | string | 排序字段：created_at, token_usage.total_tokens, duration_ms |
| order | string | asc / desc |
| limit | number | 每页数量，默认 50，最大 200 |
| offset | number | 分页偏移 |

**响应**：

```json
{
  "logs": [
    {
      "log_id": "log-001",
      "event_type": "model_call",
      "event_status": "completed",
      "agent_id": "agent-coder-1",
      "model_id": "gpt-4o",
      "task_id": "task-123",
      "goal_id": "goal-456",
      "input_summary": "生成用户登录功能的 React 组件...",
      "output_summary": "```tsx\nimport React...",
      "token_usage": { "input_tokens": 1500, "output_tokens": 800, "total_tokens": 2300 },
      "created_at": "2026-06-25T10:00:00Z",
      "metadata": { "latency_ms": 2500 }
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### 7.2 聚合查询接口

```
GET /logs/aggregate
```

**查询参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| goal_id | string | 按 Goal 聚合 |
| task_id | string | 按 Task 聚合 |
| group_by | string | 聚合维度：agent, model, event_type, date |
| metric | string | 聚合指标：count, total_tokens, avg_latency, error_rate |
| period | string | 时间范围：24h, 7d, 30d |

**响应示例**（按 Agent 聚合 token 消耗）：

```json
{
  "group_by": "agent",
  "metric": "total_tokens",
  "data": [
    { "agent_id": "agent-coder-1", "agent_role": "coder", "total_tokens": 45000, "request_count": 20 },
    { "agent_id": "agent-reviewer-1", "agent_role": "reviewer", "total_tokens": 12000, "request_count": 8 }
  ]
}
```

### 7.3 快速筛选预设

前端提供以下快速筛选按钮：

| 预设 | 筛选条件 |
|------|----------|
| 全部 | 无筛选 |
| 仅错误 | event_status = failed/error |
| 仅模型调用 | event_type = model_call |
| 仅 Handoff | event_type = handoff_created/handoff_completed |
| 仅工具调用 | event_type = tool_call |
| 仅审核 | event_type = supervisor_review |
| 最近 1 小时 | start_time = now - 1h |
| 当前 Goal | goal_id = 当前激活的 Goal |
| 当前 Task | task_id = 当前选中的 Task |

---

## 8. 日志详情展示

### 8.1 详情抽屉（Log Detail Drawer）

点击日志列表中的任意行，右侧弹出详情抽屉：

```
┌──────────────────────────────────────────────────────────────┐
│ 日志详情                                        [×]          │
├──────────────────────────────────────────────────────────────┤
│ 类型：model_call              状态：✓ completed             │
│ 时间：2026-06-25 10:00:00                                    │
├──────────────────────────────────────────────────────────────┤
│ 关联信息                                                     │
│ Goal：实现用户认证系统          [查看]                       │
│ Task：生成登录组件              [查看]                       │
│ Agent：Coder #1                 [查看]                       │
│ Model：gpt-4o                   [查看]                       │
│ Worker：worker-abc123                                        │
├──────────────────────────────────────────────────────────────┤
│ Token 消耗                                                   │
│ Input：  1,500 tokens                                        │
│ Output：   800 tokens                                        │
│ Total：  2,300 tokens                                        │
│ 延迟：   2,500 ms                                            │
├──────────────────────────────────────────────────────────────┤
│ 输入（完整）                                                 │
│ ┌────────────────────────────────────────────────────────┐   │
│ │ 请生成一个 React 登录组件，包含...                       │   │
│ └────────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│ 输出（完整）                                                 │
│ ┌────────────────────────────────────────────────────────┐   │
│ │ ```tsx                                                 │   │
│ │ import React, { useState } from 'react';               │   │
│ │ ...                                                    │   │
│ └────────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│ 元数据                                                       │
│ routing_reason: "代码生成任务，GPT-4o 能力匹配度最高"        │
│ confidence: 0.95                                             │
│ risk_flags: []                                               │
└──────────────────────────────────────────────────────────────┘
```

**交互**：

- 点击 [查看] 跳转对应 Goal/Task/Agent 详情。
- 输入/输出区域支持复制、展开/折叠。
- 如果是错误日志，显示错误详情和堆栈（开发模式）。
- 如果是 Handoff 日志，显示 Handoff 前后对比按钮。

### 8.2 Handoff 前后对比视图

在 Handoff 相关日志中，提供对比视图：

```
┌──────────────────────────────────────────────────────────────┐
│ Handoff 前后对比                              [×]          │
├──────────────────────────────────────────────────────────────┤
│ 从：Coder #1 (claude-3-5) → 到：Coder #2 (gpt-4o)          │
│ 原因：额度耗尽                                               │
│ 时间：2026-06-25 10:05:00                                    │
├──────────────────────────┬───────────────────────────────────┤
│ Handoff 前上下文         │ Handoff 后上下文                  │
├──────────────────────────┼───────────────────────────────────┤
│ 已完成任务：              │ 接收到的任务：                    │
│ - 生成登录组件骨架        │ - 继续完善登录组件                │
│ - 实现表单验证逻辑        │ - 添加密码强度检查                │
│                          │                                   │
│ 待办：                   │ 已知约束：                        │
│ - 添加密码强度检查        │ - 使用 React Hook Form            │
│ - 样式美化               │ - 支持邮箱验证                    │
│                          │                                   │
│ Token 数：2,500          │ Token 数：1,800                   │
│ [上下文完整度：95%]       │ [上下文完整度：85%]               │
├──────────────────────────┴───────────────────────────────────┤
│ ⚠️ 上下文损失：400 tokens（表单验证细节部分丢失）            │
└──────────────────────────────────────────────────────────────┘
```

---

## 9. 与 Agent Runtime 的关系

### 9.1 Runtime 作为核心日志生产者

Agent Runtime 是日志的最大生产者：

```text
Runtime 执行流程：
  1. 加载 Task 和 Agent
     ↓ 日志：agent_step (started)
  2. 调用 Model Router 选择模型
     ↓ 日志：model_call (started) + routing_info
  3. 调用模型 API
     ↓ 日志：model_call (completed/failed) + token_usage + latency
  4. 解析模型输出，决定下一步
     ↓ 日志：agent_step (completed) + reasoning
  5. 如需调用工具
     ↓ 日志：tool_call (started)
     ↓ 工具执行
     ↓ 日志：tool_call (completed/failed) + duration
  6. 循环直到 Task 完成
     ↓ 日志：task_status_change
```

### 9.2 Runtime 日志采集方式

Runtime 通过 Hook 机制采集日志：

```typescript
interface RuntimeLogHooks {
  onAgentStepStart: (step: AgentStep) => void;
  onAgentStepEnd: (step: AgentStep, result: StepResult) => void;
  onModelCallStart: (call: ModelCall) => void;
  onModelCallEnd: (call: ModelCall, response: ModelResponse) => void;
  onToolCallStart: (call: ToolCall) => void;
  onToolCallEnd: (call: ToolCall, result: ToolResult) => void;
  onError: (error: ExecutionError) => void;
}
```

Runtime 在执行关键节点调用对应 Hook，Logs Service 异步写入日志。

### 9.3 性能保证

- Hook 调用为同步触发，但日志写入为异步。
- Hook 执行时间必须 < 10ms，不影响 Runtime 主流程。
- 如果日志服务不可用，Runtime 继续执行，日志可丢弃。

---

## 10. 与 Handoff Manager 的关系

### 10.1 Handoff 日志链路

Handoff 是用户最关心的链路之一，需要完整记录：

```text
Handoff 触发
  ↓ 日志：handoff_created
  ├─ from_agent_id
  ├─ from_model_id
  ├─ to_agent_id
  ├─ to_model_id
  ├─ handoff_reason
  ├─ trigger_type (auto/manual)
  ├─ summary_length
  └─ context_tokens

生成 HandoffSummary
  ↓ 日志：agent_step (HandoffSummary 生成)

接手 Agent 加载上下文
  ↓ 日志：agent_step (started) + handoff_context_loaded

接手 Agent 接受 Handoff
  ↓ 日志：handoff_completed
  ├─ event_status: accepted/rejected/timeout
  ├─ acceptance_time_ms
  └─ context_loss_estimate
```

### 10.2 Handoff 对比支持

Logs Service 提供 Handoff 对比查询接口：

```
GET /logs/handoff/:handoff_id/compare
```

**响应**：

```json
{
  "handoff_id": "handoff-001",
  "from_context": {
    "agent_id": "agent-coder-1",
    "model_id": "claude-3-5",
    "completed_steps": ["生成骨架", "表单验证"],
    "pending_steps": ["密码强度", "样式美化"],
    "context_tokens": 2500,
    "output_summary": "已完成登录组件骨架和表单验证..."
  },
  "to_context": {
    "agent_id": "agent-coder-2",
    "model_id": "gpt-4o",
    "received_task": "继续完善登录组件",
    "known_constraints": ["使用 React Hook Form", "支持邮箱验证"],
    "context_tokens": 1800,
    "input_summary": "接手任务：继续完善登录组件，已知..."
  },
  "context_loss": {
    "lost_tokens": 400,
    "loss_percent": 0.16,
    "lost_details": ["表单验证的具体规则细节"]
  }
}
```

---

## 11. 与 Quota Manager 的关系

### 11.1 Quota 日志联动

Quota Manager 状态变化时，自动写入 quota_status_change 日志：

```text
Quota Manager 判定状态变化
  ↓
写入 QuotaStatusHistory（Quota Manager 内部）
  ↓
触发事件：quota.status_changed
  ↓
Logs Service 写入 quota_status_change 日志
  ↓
Workspace Logs Panel 实时展示状态变化
```

### 11.2 Token 消耗关联

每次 model_call 日志的 token_usage 与 QuotaRecord 的统计数据对齐：

- model_call 的 input_tokens + output_tokens = QuotaRecord 的累加值。
- 不一致时，以 model_call 日志为准，触发 QuotaRecord 修正。

---

## 12. 与 Memory / Skill Evolution 的关系

### 12.1 日志作为 Memory 的数据源

Logs 不仅是给用户看的，更是给系统自己学习用的。Knowledge Evolution Agent 会从日志中提取：

| 提取目标 | 来源日志类型 | 提取规则 |
|----------|-------------|----------|
| 模型表现模式 | model_call | 同一 Task 类型下，哪个模型 latency 低、token 少、成功率高 |
| Agent 协作模式 | agent_step, handoff_created | 哪些 Agent 组合执行效率高 |
| 工具使用模式 | tool_call | 哪些工具组合在特定任务中最有效 |
| 错误模式 | error | 哪些错误在特定场景下反复出现 |
| 用户偏好 | memory_write_candidate | 用户对输出格式、风格的偏好 |
| Handoff 效率 | handoff_completed | 哪些 Handoff 场景上下文损失最小 |

### 12.2 memory_write_candidate 日志

当系统检测到可沉淀为经验的事件时，写入 memory_write_candidate 日志：

**触发条件**：

1. 同一 Task 类型连续 3 次成功，且使用相同模型 + Agent 组合。
2. 某 Agent 的 Step 连续被 Supervisor 审核通过，无 revision。
3. 某工具组合在特定 Task 类型下显著减少 token 消耗。
4. Handoff 后接手 Agent 一次性完成任务，无二次 Handoff。

**示例**：

```json
{
  "event_type": "memory_write_candidate",
  "event_status": "detected",
  "candidate_type": "model_preference",
  "source_event_ids": ["log-001", "log-002", "log-003"],
  "task_id": "task-123",
  "goal_id": "goal-456",
  "description": "代码生成任务中，gpt-4o 在 React 组件生成上表现优于 claude-3-5，平均 token 消耗少 15%，latency 低 20%",
  "confidence": 0.85,
  "suggested_tags": ["code_generation", "react", "gpt-4o", "model_preference"]
}
```

### 12.3 日志保留策略

| 日志类型 | 保留期 | 说明 |
|----------|--------|------|
| error | 90 天 | 错误日志长期保留，用于问题排查 |
| handoff_created / handoff_completed | 90 天 | Handoff 日志用于复盘 |
| memory_write_candidate | 永久 | 经验沉淀日志永久保留 |
| 其他 | 30 天 | 普通日志保留 30 天 |

---

## 13. 前端页面设计

### 13.1 Logs List（日志列表）

**布局**：

```
┌─────────────────────────────────────────────────────────────────────┐
│ Logs / Observability                                    [设置]      │
├─────────────────────────────────────────────────────────────────────┤
│ 筛选栏                                                               │
│ [Goal: 全部 ▼] [Task: 全部 ▼] [Agent: 全部 ▼] [Model: 全部 ▼]      │
│ [类型: 全部 ▼] [状态: 全部 ▼] [时间: 全部 ▼] [搜索...]             │
├─────────────────────────────────────────────────────────────────────┤
│ 快速筛选                                                            │
│ [全部] [仅错误] [仅模型调用] [仅Handoff] [仅工具] [仅审核] [最近1h] │
├─────────────────────────────────────────────────────────────────────┤
│ 日志列表                                                             │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 时间    类型         状态   Agent    Model   Task    摘要      │ │
│ ├─────────────────────────────────────────────────────────────────┤ │
│ │ 10:05   handoff     ✓      Coder→   claude→ gpt-4o  额度耗尽   │ │
│ │ 10:04   model_call  ✓      Coder    gpt-4o  登录组件 生成骨架  │ │
│ │ 10:03   tool_call   ✓      Coder    -       登录组件 写入文件  │ │
│ │ 10:02   model_call  ✗      Coder    claude  登录组件 429错误   │ │
│ │ 10:01   agent_step  ✓      Planner  -       -       拆解任务  │ │
│ │ 10:00   task_status ✓      -        -       登录组件 运行中   │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                    │
│ 分页：[1] [2] [3] ... [10]  共 150 条                              │
└─────────────────────────────────────────────────────────────────────┘
```

**交互**：

- 点击任意行 → 打开右侧 Log Detail Drawer。
- 点击快速筛选按钮 → 立即应用对应筛选条件。
- 搜索框支持关键词搜索 input_summary / output_summary / error_message。
- 列表每行显示：时间、类型图标、状态图标、Agent、Model、Task、摘要。

### 13.2 Log Detail Drawer（日志详情抽屉）

见 8.1 节。

### 13.3 Task Timeline（任务时间线）

**布局**：

```
┌─────────────────────────────────────────────────────────────────────┐
│ Task Timeline：生成登录组件                             [返回列表] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ 10:00 ──●── task_status_change: pending → running                │
│         │                                                           │
│ 10:01 ──●── agent_step: Planner 拆解任务                          │
│         │   └─ 输出：3 个子任务                                    │
│         │                                                           │
│ 10:02 ──●── model_call: Coder 调用 claude-3-5                     │
│         │   └─ 429 rate limit ⚠️                                   │
│         │                                                           │
│ 10:03 ──●── handoff_created: Coder #1 → Coder #2                  │
│         │   └─ 原因：额度耗尽                                      │
│         │                                                           │
│ 10:04 ──●── model_call: Coder 调用 gpt-4o ✓                       │
│         │   └─ 生成骨架代码                                        │
│         │                                                           │
│ 10:05 ──●── tool_call: 写入文件 ✓                                 │
│         │                                                           │
│ 10:06 ──●── supervisor_review: Reviewer 审核通过 ✓               │
│         │                                                           │
│ 10:07 ──●── task_status_change: running → completed              │
│                                                                     │
│ 总耗时：7 分钟  总 token：3,500  模型调用：2 次  Handoff：1 次     │
└─────────────────────────────────────────────────────────────────────┘
```

**交互**：

- 点击时间线上的任意节点 → 打开对应日志详情。
- Handoff 节点支持点击展开对比视图。
- 底部统计栏展示 Task 执行摘要。
- 支持缩放时间轴（查看全部 / 只看最近 1 小时）。

### 13.4 Agent Execution Trace（Agent 执行追踪）

针对单个 Agent 的执行过程，展示其所有 Step：

```
┌─────────────────────────────────────────────────────────────────────┐
│ Agent Execution Trace：Coder #1                       [返回列表] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Step 1: 理解任务                                                     │
│ ├── model_call (claude-3-5) ✓                                       │
│ │   └── token: 800  latency: 1.2s                                   │
│ └── 输出：理解完成                                                   │
│                                                                     │
│ Step 2: 生成代码骨架                                                 │
│ ├── model_call (claude-3-5) ✗                                       │
│ │   └── error: 429 rate limit                                       │
│ └── 触发 Handoff                                                     │
│                                                                     │
│ Step 3: [Handoff 后由 Coder #2 继续]                                 │
│                                                                     │
│ 统计：2 次 model_call，1 次成功，1 次失败，总 token 800            │
└─────────────────────────────────────────────────────────────────────┘
```

### 13.5 Token Usage Summary（Token 使用汇总）

**布局**：

```
┌─────────────────────────────────────────────────────────────────────┐
│ Token Usage Summary                                                 │
├─────────────────────────────────────────────────────────────────────┤
│ 按 Agent 汇总                                                        │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Planner    ████████░░░░░░░░░░  2,000 tokens  (20%)             │ │
│ │ Coder      ██████████████████  8,000 tokens  (60%)             │ │
│ │ Reviewer   ███░░░░░░░░░░░░░░░  1,500 tokens  (15%)             │ │
│ │ Summarizer █░░░░░░░░░░░░░░░░░    500 tokens   (5%)             │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ 按 Model 汇总                                                        │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ gpt-4o       ████████████████  6,000 tokens  (50%)             │ │
│ │ claude-3-5   ██████████░░░░░░  4,000 tokens  (35%)             │ │
│ │ deepseek     ██░░░░░░░░░░░░░░  1,500 tokens  (12%)             │ │
│ │ kimi         ░░░░░░░░░░░░░░░░      0 tokens   (0%)             │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ 总计：11,500 tokens  模型调用：12 次  平均延迟：2.1s              │
└─────────────────────────────────────────────────────────────────────┘
```

### 13.6 Error Panel（错误面板）

**布局**：

```
┌─────────────────────────────────────────────────────────────────────┐
│ Error Panel                                           [导出错误]   │
├─────────────────────────────────────────────────────────────────────┤
│ 今日错误统计                                                         │
│ 总计：5 次  API错误：2  工具错误：2  超时：1                        │
├─────────────────────────────────────────────────────────────────────┤
│ 错误列表                                                             │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ ⚠️ 10:02  Coder  429 rate limit (claude-3-5)  [查看] [修复]   │ │
│ │ ✗  09:45  Coder  文件写入失败 (权限不足)        [查看] [修复]   │ │
│ │ ✗  09:30  Planner 模型返回格式错误              [查看] [修复]   │ │
│ │ ⏱  09:15  Reviewer 超时 (10s)                  [查看] [修复]   │ │
│ │ ⚠️ 09:00  Coder  429 rate limit (gpt-4o)       [查看] [修复]   │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ 点击 [修复] 可尝试自动重试或切换到备用模型                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 14. 后端接口设计

### 14.1 日志查询接口

#### 14.1.1 查询日志列表

```
GET /logs
```

见 7.1 节。

#### 14.1.2 查询单条日志详情

```
GET /logs/:log_id
```

**响应**：

```json
{
  "log_id": "log-001",
  "event_type": "model_call",
  "event_status": "completed",
  "goal_id": "goal-456",
  "task_id": "task-123",
  "agent_id": "agent-coder-1",
  "worker_id": "worker-abc123",
  "model_id": "gpt-4o",
  "input_summary": "生成用户登录功能的 React 组件...",
  "output_summary": "```tsx\nimport React...",
  "token_usage": { "input_tokens": 1500, "output_tokens": 800, "total_tokens": 2300 },
  "quota_status": "normal",
  "created_at": "2026-06-25T10:00:00Z",
  "metadata": {
    "latency_ms": 2500,
    "routing_reason": "代码生成任务，GPT-4o 能力匹配度最高",
    "confidence": 0.95,
    "risk_flags": []
  }
}
```

#### 14.1.3 聚合查询

```
GET /logs/aggregate
```

见 7.2 节。

### 14.2 Task 链路接口

#### 14.2.1 获取 Task 完整执行链路

```
GET /logs/task/:task_id/timeline
```

**响应**：

```json
{
  "task_id": "task-123",
  "task_name": "生成登录组件",
  "goal_id": "goal-456",
  "events": [
    {
      "log_id": "log-001",
      "event_type": "task_status_change",
      "event_status": "transition",
      "from_status": "pending",
      "to_status": "running",
      "created_at": "2026-06-25T10:00:00Z"
    },
    {
      "log_id": "log-002",
      "event_type": "agent_step",
      "event_status": "completed",
      "agent_id": "agent-planner-1",
      "step_name": "拆解任务",
      "created_at": "2026-06-25T10:01:00Z"
    },
    {
      "log_id": "log-003",
      "event_type": "model_call",
      "event_status": "failed",
      "agent_id": "agent-coder-1",
      "model_id": "claude-3-5",
      "error_message": "429 rate limit exceeded",
      "created_at": "2026-06-25T10:02:00Z"
    },
    {
      "log_id": "log-004",
      "event_type": "handoff_created",
      "event_status": "created",
      "from_agent_id": "agent-coder-1",
      "to_agent_id": "agent-coder-2",
      "handoff_reason": "quota_exceeded",
      "created_at": "2026-06-25T10:03:00Z"
    },
    {
      "log_id": "log-005",
      "event_type": "model_call",
      "event_status": "completed",
      "agent_id": "agent-coder-2",
      "model_id": "gpt-4o",
      "created_at": "2026-06-25T10:04:00Z"
    },
    {
      "log_id": "log-006",
      "event_type": "task_status_change",
      "event_status": "transition",
      "from_status": "running",
      "to_status": "completed",
      "created_at": "2026-06-25T10:07:00Z"
    }
  ],
  "summary": {
    "total_duration_ms": 420000,
    "total_tokens": 3500,
    "model_call_count": 2,
    "handoff_count": 1,
    "error_count": 1
  }
}
```

### 14.3 Handoff 对比接口

```
GET /logs/handoff/:handoff_id/compare
```

见 10.2 节。

### 14.4 日志管理接口

#### 14.4.1 清理日志

```
POST /logs/cleanup
```

**请求体**：

```json
{
  "retention_days": 30,
  "event_types": ["model_call", "agent_step", "tool_call"],
  "dry_run": false
}
```

#### 14.4.2 导出日志

```
GET /logs/export
```

**查询参数**：

- `goal_id`：导出特定 Goal 的日志
- `task_id`：导出特定 Task 的日志
- `format`：json / csv
- `start_time`, `end_time`：时间范围

---

## 15. 数据对象设计

### 15.1 ExecutionLog（执行日志）

```typescript
interface ExecutionLog {
  // 主键
  log_id: string;               // UUID

  // 关联对象
  goal_id?: string;
  task_id?: string;
  agent_id?: string;
  worker_id?: string;
  model_id?: string;

  // 事件信息
  event_type: LogEventType;
  event_status: LogEventStatus;
  created_at: string;           // ISO 8601

  // 内容
  input_summary?: string;       // 前 500 字符
  output_summary?: string;      // 前 500 字符

  // Token
  token_usage?: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };

  // 额度
  quota_status?: string;

  // Handoff
  handoff_status?: string;
  handoff_id?: string;

  // 工具
  tool_name?: string;
  tool_type?: string;

  // 错误
  error_type?: string;
  error_code?: string;
  error_message?: string;
  stack_trace?: string;

  // 性能
  latency_ms?: number;
  duration_ms?: number;

  // 元数据
  metadata?: Record<string, any>;

  // 上下文引用（MVP-B）
  context_snapshot_id?: string; // 关联的上下文快照 ID
}

type LogEventType =
  | 'model_call'
  | 'agent_step'
  | 'tool_call'
  | 'task_status_change'
  | 'quota_status_change'
  | 'handoff_created'
  | 'handoff_completed'
  | 'error'
  | 'supervisor_review'
  | 'memory_write_candidate';

type LogEventStatus =
  | 'started'
  | 'completed'
  | 'failed'
  | 'skipped'
  | 'transition'
  | 'created'
  | 'accepted'
  | 'rejected'
  | 'timeout'
  | 'approved'
  | 'needs_revision'
  | 'detected'
  | 'error';
```

### 15.2 LogIndex（日志索引，MVP-B）

为加速查询，建立复合索引：

```typescript
interface LogIndex {
  // 按 Goal + Time 索引
  goal_id: string;
  created_at: string;
  log_id: string;

  // 按 Task + Time 索引
  task_id: string;
  created_at: string;
  log_id: string;

  // 按 Agent + Time 索引
  agent_id: string;
  created_at: string;
  log_id: string;

  // 按 Event Type + Time 索引
  event_type: string;
  created_at: string;
  log_id: string;
}
```

### 15.3 ContextSnapshot（上下文快照，MVP-B）

用于 Handoff 对比和复盘：

```typescript
interface ContextSnapshot {
  snapshot_id: string;
  log_id: string;               // 关联的日志
  agent_id: string;
  task_id: string;
  goal_id: string;

  // 完整上下文（存储为 JSON 或文件引用）
  context_data: {
    messages: Message[];        // 完整对话历史
    files: string[];            // 相关文件列表
    memory_items: string[];     // 已加载的记忆
    tool_results: ToolResult[]; // 工具执行结果
  };

  context_tokens: number;       // 上下文 token 数
  created_at: string;
}
```

---

## 16. 异常状态

### 16.1 日志写入失败

**场景**：日志服务不可用，或磁盘空间不足。

**处理策略**：

1. 日志写入失败不影响主流程。
2. 内存中保留最近 100 条日志缓存。
3. 写入失败时，在控制台输出降级日志："[Logs] Failed to write log: {reason}"。
4. 服务恢复后，尝试批量写入缓存中的日志。
5. 如果缓存溢出，丢弃最早的日志（FIFO）。

### 16.2 日志量过大

**场景**：长时间运行大量 Task，日志量激增。

**处理策略**：

1. 自动清理：超过保留期的日志自动删除。
2. 归档：MVP-B 支持将旧日志归档到压缩文件。
3. 采样：调试模式下可开启采样（只记录 10% 的 model_call）。
4. 限制：单个 Goal 的日志上限为 10,000 条，超过后提示用户清理。

### 16.3 敏感信息泄露

**场景**：模型输入或输出中包含 API Key、密码等敏感信息。

**处理策略**：

1. 日志写入前，扫描 input_summary / output_summary。
2. 匹配敏感模式（如 `sk-...`, `Bearer ...`, `password:`），自动脱敏为 `***`。
3. 用户可在设置中配置自定义脱敏规则。
4. 完整的原始输入/输出不存入日志，只存摘要。

### 16.4 时间错乱

**场景**：系统时间被修改，导致日志时间戳混乱。

**处理策略**：

1. 使用单调时钟（monotonic clock）记录相对时间。
2. 时间戳使用 UTC，不受本地时区影响。
3. 检测到时间倒流时，标记该日志为 "time_anomaly"。

---

## 17. MVP 范围

### MVP-A（核心闭环）

1. **记录模型调用日志**：
   - model_call (started/completed/failed)。
   - 包含 model_id、agent_id、token_usage、latency。

2. **记录 Agent 执行日志**：
   - agent_step (started/completed/failed)。
   - 包含 agent_role、step_name、duration。

3. **记录 Task 状态变化**：
   - task_status_change (transition)。
   - 包含 from_status、to_status、reason。

4. **记录 Handoff 事件**：
   - handoff_created、handoff_completed。
   - 包含 from/to agent、handoff_reason。

5. **记录错误信息**：
   - error。
   - 包含 error_type、error_message、recoverable。

6. **Logs 列表和详情抽屉**：
   - Logs List 页面，支持基础筛选（Goal、Task、Agent、Model、类型、状态）。
   - Log Detail Drawer，展示完整字段。

7. **按 Goal/Task/Agent/Model/状态筛选**：
   - 基础筛选栏 + 快速筛选按钮。

### MVP-B（增强体验）

1. **tool_call 日志**：完整记录工具调用过程。
2. **quota_status_change 日志**：与 Quota Manager 联动。
3. **supervisor_review 日志**：记录审核过程。
4. **Task Timeline 页面**：可视化时间线。
5. **Token Usage Summary**：统计图表。
6. **Error Panel**：错误集中展示和快速修复。
7. **Handoff 对比视图**：前后上下文对比。
8. **日志导出**：JSON/CSV 格式。

---

## 18. 暂缓范围

1. **不做复杂链路追踪系统**：
   - 理由：MVP 不需要分布式追踪级别的链路分析。
   - 替代：Task Timeline 展示线性时间线即可。

2. **不做企业级监控告警**：
   - 理由：告警体系属于平台化能力，MVP 阶段不需要。
   - 替代：Error Panel 集中展示错误。

3. **不做完整成本分析平台**：
   - 理由：成本分析需要接入真实计费数据，MVP 阶段使用 token 估算。
   - 替代：Token Usage Summary 展示基础统计。

4. **不做自动性能优化**：
   - 理由：自动优化需要大量数据和模型学习，属于 V1+。
   - 替代：memory_write_candidate 日志记录优化建议。

5. **不做高级日志可视化图谱**：
   - 理由：图谱可视化（如节点关系图）复杂度高，MVP 阶段不需要。
   - 替代：Task Timeline 线性展示。

---

## 19. 验收标准

### 19.1 功能验收

- [ ] 每次模型调用后，系统写入 model_call 日志，包含 model_id、agent_id、token_usage。
- [ ] 每次 Agent Step 完成后，系统写入 agent_step 日志，包含 step_name、duration。
- [ ] 每次 Task 状态变化时，系统写入 task_status_change 日志，包含 from_status、to_status。
- [ ] 每次 Handoff 创建和完成时，系统写入 handoff_created / handoff_completed 日志。
- [ ] 每次错误发生时，系统写入 error 日志，包含 error_type、error_message。
- [ ] Logs List 页面正确展示所有日志，支持分页。
- [ ] 筛选栏支持按 Goal、Task、Agent、Model、Event Type、Status 筛选。
- [ ] 快速筛选按钮（仅错误、仅模型调用、仅 Handoff 等）工作正常。
- [ ] 点击日志行打开 Log Detail Drawer，展示完整字段。
- [ ] Task Timeline 页面正确展示 Task 的执行时间线。
- [ ] Token Usage Summary 正确统计各 Agent 和 Model 的 token 消耗。
- [ ] Error Panel 集中展示所有错误，支持 [查看] 和 [修复]。

### 19.2 体验验收

- [ ] 用户能在任务执行过程中实时看到 Logs 更新（延迟 < 2 秒）。
- [ ] 用户能在 3 秒内通过筛选找到特定类型的日志。
- [ ] 用户能通过 Task Timeline 理解任务的完整执行过程。
- [ ] 用户能通过 Handoff 对比视图评估上下文传递质量。
- [ ] 用户能通过 Token Usage Summary 识别 token 消耗最高的 Agent/Model。

### 19.3 性能验收

- [ ] 日志写入为异步操作，不阻塞 Runtime 主流程（Hook 延迟 < 10ms）。
- [ ] Logs List 页面加载时间 < 1 秒（1000 条日志以内）。
- [ ] 筛选查询响应时间 < 500ms。
- [ ] Task Timeline 渲染时间 < 500ms（50 个事件以内）。

### 19.4 安全验收

- [ ] 日志中不包含 API Key、密码等敏感信息（已脱敏）。
- [ ] 用户可配置自定义脱敏规则。
- [ ] 日志数据仅存储在本地，不上传云端。
- [ ] 日志保留策略正确执行，超期日志自动清理。

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
>
> 相关文档：
> - `docs/prd/agent-workspace-prd.md` — Logs Panel 在 Workspace 中的展示
> - `docs/prd/handoff-manager-prd.md` — Handoff 日志和对比视图
> - `docs/prd/quota-manager-prd.md` — Quota 状态变化日志
> - `docs/prd/model-router-prd.md` — RoutingInfo 在日志中的记录
> - `docs/prd/agent-registry-prd.md` — Agent 执行日志中的 agent_role
