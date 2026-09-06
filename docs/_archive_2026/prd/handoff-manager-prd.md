# Handoff Manager 技术型 PRD

> 所属产品：ModelGate Agent Studio
>
> 所属阶段：MVP-A / MVP-B 核心能力
>
> 文档定位：Handoff Manager 的产品与技术需求说明，作为前端、后端、数据结构和验收实现依据。

---

## 1. 功能背景

ModelGate Agent Studio 是一个多模型 Agent 协作平台。用户输入一个 Goal 后，系统会拆解 Task，并将任务分配给不同 Agent Station，由不同模型驱动的 Worker 执行。

在长任务、多模型、多 Agent 协作过程中，任务经常会遇到以下中断点：

1. 当前模型额度不足。
2. 当前模型请求失败或进入冷却。
3. 当前 Agent 不适合继续处理当前任务。
4. 当前输出质量不足，需要交给 Reviewer、Summarizer 或更强模型继续。
5. 用户主动决定切换 Agent 或模型。
6. 任务执行到阶段性节点，需要压缩上下文并交给后续 Agent。

如果没有结构化交接，接手 Agent 只能重新理解 Goal、Task、历史输出、约束和已做决策，导致上下文丢失、重复工作、任务质量下降。

Handoff Manager 的目标是把“任务中断”转化为“可恢复交接”：

```text
当前 Agent / Worker
↓
触发 Handoff
↓
生成结构化 Handoff Summary
↓
保存 HandoffRecord
↓
选择接手 Agent / Model
↓
接手 Worker 加载摘要继续执行
```

Handoff 是 ModelGate 区别于普通聊天工具和简单 API 聚合器的核心差异化能力之一。

---

## 2. 用户问题

### 2.1 主要用户

- 多模型重度使用的开发者
- 使用多个 AI Coding Plan 或 API 的开发者
- 需要长时间推进复杂任务的独立开发者 / AI 产品经理 / 研究者

### 2.2 用户痛点

#### 问题一：模型额度不足会中断任务

用户使用 Claude、OpenAI、DeepSeek 等模型执行长任务时，可能因为 token、请求数、窗口期或服务错误导致任务中断。

痛点：

- 当前任务做到哪里不清楚。
- 已完成内容无法结构化传递。
- 接手模型需要重新理解上下文。
- 用户需要手动复制粘贴大量内容。

#### 问题二：多 Agent 协作缺少交接边界

Planner、Coder、Reviewer、Summarizer、Supervisor 各自负责不同工作，但它们之间需要传递目标、任务、输出、约束和风险。

痛点：

- Agent 之间的交接不可见。
- 任务流转只停留在 UI 动画，没有真实上下文传递。
- 用户无法判断接手 Agent 是否理解前序工作。

#### 问题三：质量不足时无法安全切换执行者

当某个模型输出质量不够、角色不匹配或执行失败时，用户需要把任务转给更适合的 Agent 或模型。

痛点：

- 不知道应该交给谁。
- 不知道需要携带哪些上下文。
- 接手后容易重复犯同样错误。

### 2.3 要解决的核心问题

Handoff Manager 要解决的是：

> 当任务不能由当前 Agent / Worker 继续完成时，系统如何生成足够清晰、完整、可追溯的交接摘要，让接手 Agent 不重新询问用户也能继续工作。

---

## 3. 产品目标

### 3.1 核心目标

1. 支持用户手动触发 Task Handoff。
2. 支持系统在额度不足、模型错误、质量不足时提示 Handoff。
3. 生成结构化 Handoff Summary。
4. 保存完整 HandoffRecord。
5. 让接手 Agent / Worker 可以加载交接摘要继续执行。
6. 在 Workspace 中清晰展示交接过程。
7. 在 Logs 和 Handoff 页面中保留可追溯记录。

### 3.2 非目标

当前阶段不追求：

- 完全自动判断所有交接时机。
- 完全自动修复失败任务。
- 自动读取所有 Coding Plan 的真实额度。
- 跨项目长期 Handoff Memory。
- 自动把交接经验沉淀为 Skill。
- 多人协作下的交接审批流。

### 3.3 成功判断

Handoff Manager 成功的标志：

> 接手 Agent 读取 Handoff Summary 后，可以理解原始目标、当前任务、已完成内容、未完成内容、关键约束、已做决策、风险和下一步建议，并继续执行任务。

---

## 4. 用户流程

### 4.1 手动 Handoff 流程

```text
1. 用户在 Workspace 中查看正在执行的 Task。
2. 用户点击 Agent Card、Task Detail 或 Station Popover 中的 Generate Handoff。
3. 系统打开 Handoff 操作确认区。
4. 用户选择接手 Agent，填写或选择交接原因。
5. 用户确认触发 Handoff。
6. Handoff Manager 创建 HandoffRecord，状态为 requested。
7. 系统收集 Goal、Task、Agent、Worker、Logs、当前输出和错误信息。
8. Summarizer 或 Handoff Manager 生成 Handoff Summary。
9. HandoffRecord 状态更新为 ready。
10. 接手 Agent 接受 Handoff，创建新的 WorkerSession。
11. 接手 Worker 加载 handoff_summary 和 task context。
12. Task 状态从 handoff 更新为 running。
13. 原 Worker 状态更新为 completed 或 handoff_required。
14. 接手 Worker 继续执行任务。
15. HandoffRecord 状态更新为 completed，并记录 result_after_handoff。
```

### 4.2 额度不足 Handoff 流程

```text
1. Agent Runtime 执行任务。
2. Quota Manager 检测到当前模型达到 warning 或 blocked 阈值。
3. Agent Card 显示 Quota Warning。
4. 系统暂停新任务分配给当前模型。
5. Workspace 展示建议：Generate Handoff / Continue Anyway。
6. 用户点击 Generate Handoff。
7. Handoff Manager 生成摘要并选择备用模型或接手 Agent。
8. 接手 Worker 加载摘要继续执行。
```

MVP 阶段只要求“额度不足时提示 Handoff”，不要求系统无确认自动交接。

### 4.3 模型错误 Handoff 流程

```text
1. 当前模型调用失败或连续重试失败。
2. Task 状态更新为 failed 或 blocked。
3. Bottom Console 展示错误信息。
4. Workspace 提供 Retry / Generate Handoff。
5. 用户选择 Generate Handoff。
6. Handoff Summary 包含错误原因、已尝试方案和下一步建议。
7. 接手 Agent 避免重复相同失败路径。
```

### 4.4 质量不足 Handoff 流程

```text
1. Reviewer 或 Supervisor 判断当前输出未达标。
2. 系统建议将任务交给更适合的 Agent 或更强模型。
3. Handoff Summary 中记录质量问题和修改建议。
4. 接手 Agent 基于审查意见继续执行。
```

MVP 阶段质量不足可以通过用户手动选择或 Reviewer 输出触发，不要求自动评分。

---

## 5. 前端页面设计

### 5.1 Workspace 中的 Handoff 表达

Handoff 必须优先在 Workspace 中可见。Workspace 是 Handoff 的主操作入口。

#### Card Flow View

当 Handoff 发生时：

1. 原 Agent Card 状态变为 `handoff`，边框变为紫色。
2. 原 Agent Card 显示 `Generating Handoff Summary`。
3. 原 Agent 和接手 Agent 之间出现紫色 handoff edge。
4. 中间出现 Handoff Summary Card。
5. 接手 Agent Card 显示 `Loading Context`。
6. Handoff 完成后，edge 变为 done，接手 Agent 进入 running。

Handoff Summary Card 显示字段：

- Handoff 原因
- From Agent / Model
- To Agent / Model
- 当前 Task
- Summary 状态
- 创建时间
- View Details 按钮

#### Pixel Office View

MVP 阶段只做轻量表达：

1. 原工位状态灯变紫色。
2. 显示 Handoff Folder。
3. 接手工位显示 `Loading Context`。
4. Handoff 完成后，接手工位进入 running。

不做完整角色行走、复杂办公室动画。

### 5.2 Agent Detail Modal

在 Agent Detail Modal 中增加 Handoff 操作入口。

建议放在：

- Overview Tab：显示当前是否可交接。
- Task Tab：显示当前任务和交接按钮。
- Context Tab：显示 Handoff Summary 或 inherited Handoff。
- History Tab：显示该 Agent 相关 Handoff 记录。

操作按钮：

- Generate Handoff
- View Handoff Summary
- Retry Task
- Continue Anyway

### 5.3 Handoff Detail Modal

点击 Handoff Summary Card 或 Handoff 列表项后打开详情。

内容结构：

```text
Header
- Handoff ID
- Status
- Reason
- Created At

Participants
- From Agent
- From Model
- To Agent
- To Model

Summary
- Original Goal
- Current Task
- Completed Work
- Unfinished Work
- Important Constraints
- Key Decisions
- Errors and Risks
- Next Suggested Steps
- Context Needed

Result
- Result After Handoff
- Tokens Before / After
- Completed At
```

### 5.4 Handoff 页面

MVP-B 阶段提供独立 Handoff 页面。

列表字段：

- Handoff ID
- Goal
- Task
- From Agent
- To Agent
- Reason
- Status
- Result
- Created At

筛选条件：

- goal_id
- task_id
- reason
- status
- from_agent_id
- to_agent_id

### 5.5 Bottom Console 日志表达

Bottom Console 必须显示 Handoff 事件：

- Handoff requested
- Generating summary
- Handoff summary ready
- Handoff accepted
- Handoff completed
- Handoff failed

出错时自动展开 Error Logs。

---

## 6. 后端接口设计

接口遵循现有 API 约定：

```text
Base URL: /api/v1
Response: { success: boolean, data?: object, error?: object }
```

### 6.1 手动触发 Task Handoff

```http
POST /tasks/:taskId/handoff
```

请求体：

```json
{
  "to_agent_id": "agent-uuid",
  "to_model_id": "model-uuid-optional",
  "reason": "manual",
  "reason_description": "用户手动选择交接给 Reviewer",
  "include_recent_logs": true,
  "include_current_output": true
}
```

响应：

```json
{
  "success": true,
  "data": {
    "handoff_id": "handoff-uuid",
    "task_id": "task-uuid",
    "status": "generating_summary",
    "message": "正在生成交接摘要"
  }
}
```

### 6.2 获取 Handoff 列表

```http
GET /handoffs?goal_id=xxx&task_id=xxx&status=ready&reason=manual&page=1&page_size=20
```

响应：

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "handoff-uuid",
        "goal_id": "goal-uuid",
        "task_id": "task-uuid",
        "from_agent_name": "Coder Agent",
        "from_model_name": "Claude",
        "to_agent_name": "Reviewer Agent",
        "to_model_name": "GPT",
        "reason": "manual",
        "status": "completed",
        "result_after_handoff": "success",
        "created_at": "2026-06-24T12:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

### 6.3 获取 Handoff 详情

```http
GET /handoffs/:handoffId
```

响应：

```json
{
  "success": true,
  "data": {
    "id": "handoff-uuid",
    "goal_id": "goal-uuid",
    "task_id": "task-uuid",
    "from_agent_id": "agent-1",
    "from_model_id": "model-1",
    "to_agent_id": "agent-2",
    "to_model_id": "model-2",
    "reason": "quota_exceeded",
    "reason_description": "Claude token 用量达到 90%",
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
    "tokens_before_handoff": 12000,
    "tokens_after_handoff": 3000,
    "created_at": "2026-06-24T12:00:00Z",
    "summary_generated_at": "2026-06-24T12:00:10Z",
    "accepted_at": "2026-06-24T12:00:15Z",
    "completed_at": "2026-06-24T12:03:00Z"
  }
}
```

### 6.4 接受 Handoff

```http
POST /handoffs/:handoffId/accept
```

请求体：

```json
{
  "agent_id": "agent-uuid",
  "model_id": "model-uuid-optional",
  "auto_continue": true
}
```

响应：

```json
{
  "success": true,
  "data": {
    "handoff_id": "handoff-uuid",
    "worker_id": "worker-uuid",
    "task_id": "task-uuid",
    "status": "accepted"
  }
}
```

### 6.5 标记 Handoff 结果

```http
PATCH /handoffs/:handoffId/result
```

请求体：

```json
{
  "result_after_handoff": "success",
  "status": "completed",
  "result_note": "接手 Agent 已完成任务"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "handoff_id": "handoff-uuid",
    "status": "completed",
    "result_after_handoff": "success"
  }
}
```

### 6.6 重新生成 Handoff Summary

```http
POST /handoffs/:handoffId/regenerate-summary
```

请求体：

```json
{
  "reason": "summary_incomplete",
  "additional_context": "请补充错误原因和下一步建议"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "handoff_id": "handoff-uuid",
    "status": "generating_summary"
  }
}
```

MVP-A 可以暂不实现该接口，MVP-B 再补齐。

---

## 7. 数据对象设计

### 7.1 HandoffRecord

```typescript
type HandoffStatus =
  | 'requested'
  | 'generating_summary'
  | 'ready'
  | 'accepted'
  | 'completed'
  | 'failed';

type HandoffReason =
  | 'quota_exceeded'
  | 'error'
  | 'quality_issue'
  | 'role_mismatch'
  | 'manual'
  | 'context_limit'
  | 'other';

type HandoffResult = 'success' | 'failed' | 'partial';

interface HandoffRecord {
  id: string;
  goal_id: string;
  task_id: string;

  from_agent_id: string;
  from_model_id: string;
  from_worker_id?: string;

  to_agent_id: string;
  to_model_id: string;
  to_worker_id?: string;

  reason: HandoffReason;
  reason_description?: string;

  handoff_summary: HandoffSummary;

  status: HandoffStatus;
  result_after_handoff?: HandoffResult;
  result_note?: string;

  tokens_before_handoff: number;
  tokens_after_handoff: number;
  time_saved_estimate_ms?: number;

  created_at: Date;
  summary_generated_at?: Date;
  accepted_at?: Date;
  completed_at?: Date;
  updated_at: Date;
}
```

### 7.2 HandoffSummary

```typescript
interface HandoffSummary {
  original_goal: string;
  current_task: string;
  completed_work: string[];
  unfinished_work: string[];
  important_constraints: string[];
  key_decisions: string[];
  errors_and_risks: string[];
  next_suggested_steps: string[];
  context_needed: string[];
}
```

### 7.3 与其他对象的关系

```text
Goal 1 ── N Task
Task 1 ── N HandoffRecord
AgentStation 1 ── N HandoffRecord as from_agent
AgentStation 1 ── N HandoffRecord as to_agent
Model 1 ── N HandoffRecord as from_model
Model 1 ── N HandoffRecord as to_model
WorkerSession 1 ── N HandoffRecord as from_worker
WorkerSession 1 ── 1 HandoffRecord as inherited source
```

### 7.4 WorkerSession 扩展字段

```typescript
interface WorkerSession {
  id: string;
  agent_id: string;
  model_id: string;
  goal_id: string;
  task_id: string;
  inherited_from_handoff_id?: string;
  status: WorkerStatus;
  current_context?: string;
  final_output?: string;
  error_message?: string;
}
```

### 7.5 ExecutionLog 关联字段

ExecutionLog 需要支持 `handoff_id`，用于追踪交接全过程。

```typescript
interface ExecutionLog {
  id: string;
  goal_id?: string;
  task_id?: string;
  agent_id?: string;
  worker_id?: string;
  model_id?: string;
  handoff_id?: string;
  level: LogLevel;
  action: string;
  message: string;
  created_at: Date;
}
```

---

## 8. 状态流转

### 8.1 HandoffRecord 状态流转

```text
requested
↓
generating_summary
↓
ready
↓
accepted
↓
completed
```

失败路径：

```text
requested → failed
generating_summary → failed
ready → failed
accepted → failed
```

### 8.2 Task 状态流转

Handoff 相关 Task 状态：

```text
running
↓
handoff
↓
running
↓
completed
```

失败路径：

```text
running → failed → handoff → running
running → handoff → failed
```

### 8.3 WorkerSession 状态流转

原 Worker：

```text
running
↓
handoff_required
↓
completed
```

接手 Worker：

```text
idle
↓
running
↓
completed / failed
```

### 8.4 AgentStation 状态流转

```text
running
↓
handoff
↓
done / idle
```

接手 Agent：

```text
idle
↓
waiting / handoff
↓
running
```

### 8.5 前端渲染状态映射

| 后端状态 | Card Flow View | Pixel Office View |
|----------|----------------|-------------------|
| requested | 显示 pending handoff | 工位出现交接提示 |
| generating_summary | 紫色卡片 + Generating | 紫色状态灯 + Summary 生成中 |
| ready | Handoff Summary Card 可点击 | Handoff Folder ready |
| accepted | 接手 Agent Loading Context | 接手工位 Loading Context |
| completed | 紫色线变绿色线 | 接手工位 running/done |
| failed | 红色错误态 | 工位警告标识 |

---

## 9. 异常状态

### 9.1 接手 Agent 不存在或不可用

触发条件：

- `to_agent_id` 不存在。
- 接手 Agent 被禁用。
- 接手 Agent 当前 blocked。

处理：

- API 返回 400 或 409。
- HandoffRecord 不进入 accepted。
- Workspace 提示用户重新选择 Agent。

### 9.2 接手模型不可用

触发条件：

- `to_model_id` 不存在。
- 模型 disabled。
- 模型连接测试失败。
- 模型额度 blocked。

处理：

- Model Router 推荐备用模型。
- 如果没有可用模型，Handoff 状态更新为 failed。
- Log 记录 `handoff_target_model_unavailable`。

### 9.3 Handoff Summary 生成失败

触发条件：

- Summarizer 模型调用失败。
- Prompt 超出上下文。
- 上游数据缺失。

处理：

- 状态更新为 failed。
- 保留错误信息。
- Workspace 提供 Retry Generate Summary。
- MVP-A 可以使用模板兜底生成简版 Summary。

### 9.4 Summary 内容不完整

触发条件：

- completed_work 为空。
- unfinished_work 为空。
- next_suggested_steps 为空。
- original_goal 或 current_task 缺失。

处理：

- 标记 summary_quality 为 warning。
- 前端提示用户检查。
- MVP-B 支持 regenerate-summary。

### 9.5 接手后继续失败

触发条件：

- 新 Worker 执行失败。
- 接手模型输出为空。
- Task 再次进入 failed。

处理：

- HandoffRecord result_after_handoff = failed 或 partial。
- Task 进入 failed。
- Workspace 提供 Retry 或再次 Handoff。
- Log 记录失败链路。

### 9.6 重复触发 Handoff

触发条件：

- 同一 Task 已有 requested / generating_summary / ready / accepted 状态的 Handoff。

处理：

- API 返回 409。
- 前端提示已有进行中的 Handoff。
- 用户可以继续已有 Handoff 或取消后重新生成。

---

## 10. 日志记录

### 10.1 必须记录的日志事件

| action | level | 说明 |
|--------|-------|------|
| handoff_requested | handoff | 用户或系统触发 Handoff |
| handoff_summary_generating | handoff | 开始生成交接摘要 |
| handoff_summary_ready | handoff | 摘要生成完成 |
| handoff_summary_failed | error | 摘要生成失败 |
| handoff_accepted | handoff | 接手 Agent 接受交接 |
| handoff_worker_created | exec | 创建接手 WorkerSession |
| handoff_context_loaded | exec | 接手 Worker 加载交接上下文 |
| handoff_completed | done | 交接完成 |
| handoff_failed | error | 交接失败 |
| handoff_result_partial | warn | 接手后部分完成 |

### 10.2 日志字段要求

每条 Handoff 相关日志至少包含：

- goal_id
- task_id
- handoff_id
- agent_id
- worker_id
- model_id
- level
- action
- message
- created_at

模型调用相关日志还需要包含：

- prompt_tokens
- completion_tokens
- total_tokens
- latency_ms
- error

### 10.3 Bottom Console 展示

Bottom Console 中 Handoff 事件应以紫色或 handoff 标签显示。

示例：

```text
[Handoff] Coder Agent requested handoff because Claude quota warning.
[Handoff] Generating summary with Summarizer Agent.
[Handoff] Summary ready. Target: Reviewer Agent / GPT.
[Exec] New WorkerSession created from handoff.
[Done] Handoff completed successfully.
```

---

## 11. MVP 范围

### 11.1 MVP-A 必须实现

| 功能 | 说明 |
|------|------|
| 手动 Handoff | 从 Task / Agent Detail 触发交接 |
| Handoff Summary 生成 | 使用模板或模型生成结构化摘要 |
| HandoffRecord 保存 | 保存交接双方、原因、摘要、状态 |
| 接手 Worker 创建 | 接手 Agent 读取摘要继续执行 |
| Workspace 展示 | Card Flow View 显示 Handoff 状态和 Summary Card |
| Bottom Console 日志 | 展示关键交接事件 |
| Handoff Detail | 可以查看完整 Summary |
| 简单失败处理 | Summary 生成失败时有错误提示和日志 |

### 11.2 MVP-B 建议实现

| 功能 | 说明 |
|------|------|
| 额度 warning 触发建议 | Quota Manager 提示用户生成 Handoff |
| 模型错误后建议 Handoff | Task failed 时提供 Generate Handoff |
| Handoff 独立页面 | 列表、筛选、详情 |
| Regenerate Summary | 用户发现摘要不完整时重新生成 |
| Pixel Office 轻量表达 | 工位紫色状态和 Handoff Folder |
| Handoff 结果标记 | success / partial / failed |

---

## 12. 暂缓范围

当前阶段明确不做：

1. 完全自动 Handoff，无用户确认。
2. 自动读取所有 AI Coding Plan 真实额度。
3. 完整 Pixel Office 交接动画。
4. 多 Agent 并行交接。
5. 跨 Goal 或跨项目 Handoff。
6. 自动将 Handoff 经验沉淀为 Skill。
7. Handoff Memory 页面。
8. 团队协作下的交接审批。
9. 企业权限、审计和多租户隔离。
10. 自动执行本地文件修改或终端命令来完成交接后的任务。
11. 复杂质量评分模型。
12. Handoff Marketplace 或第三方交接模板生态。

这些能力进入 V1 或更后阶段再评估。

---

## 13. 验收标准

### 13.1 功能验收

1. 用户可以在 Workspace 中对正在执行或失败的 Task 触发 Handoff。
2. 用户可以选择接手 Agent，并填写交接原因。
3. 系统可以创建 HandoffRecord，状态从 requested 进入 generating_summary。
4. 系统可以生成结构化 Handoff Summary。
5. Handoff Summary 至少包含 original_goal、current_task、completed_work、unfinished_work、important_constraints、key_decisions、errors_and_risks、next_suggested_steps、context_needed。
6. HandoffRecord 状态可以从 generating_summary 进入 ready。
7. 接手 Agent 接受 Handoff 后，系统创建新的 WorkerSession。
8. 新 WorkerSession 的 inherited_from_handoff_id 指向原 HandoffRecord。
9. 接手 Worker 可以读取 Handoff Summary 并继续执行 Task。
10. Task 状态可以从 running 进入 handoff，再回到 running 或 completed。
11. Handoff 完成后 result_after_handoff 可以记录 success、partial 或 failed。

### 13.2 前端验收

1. Card Flow View 中原 Agent Card 在 Handoff 时显示紫色状态。
2. Card Flow View 中可以看到 Handoff Summary Card。
3. 点击 Handoff Summary Card 可以查看完整交接摘要。
4. Agent Detail Modal 中可以触发 Generate Handoff。
5. Bottom Console 可以看到 Handoff 全过程日志。
6. Handoff 失败时前端展示错误状态和错误原因。
7. Pixel Office View 至少能用紫色状态灯表达正在交接。

### 13.3 后端验收

1. `POST /tasks/:taskId/handoff` 可创建 Handoff。
2. `GET /handoffs` 可查询 Handoff 列表。
3. `GET /handoffs/:handoffId` 可查询完整 Handoff Summary。
4. `POST /handoffs/:handoffId/accept` 可创建接手 WorkerSession。
5. `PATCH /handoffs/:handoffId/result` 可记录接手结果。
6. Handoff 相关接口对不存在的 Task、Agent、Model 返回明确错误。
7. 同一 Task 不能同时存在多个进行中的 Handoff。
8. Handoff 过程必须写入 ExecutionLog。

### 13.4 数据验收

1. HandoffRecord 可以关联 Goal、Task、from_agent、to_agent、from_model、to_model。
2. HandoffSummary 使用结构化 JSON 保存。
3. ExecutionLog 可以通过 handoff_id 查询完整交接链路。
4. WorkerSession 可以通过 inherited_from_handoff_id 追溯来源。
5. HandoffRecord 的状态变化符合状态机定义。

### 13.5 Demo 验收

必须能稳定演示以下流程：

```text
1. 用户输入 Goal。
2. Planner 拆解 Task。
3. Coder Agent 开始执行 Task。
4. 用户手动触发 Handoff。
5. 系统生成 Handoff Summary。
6. Workspace 出现 Handoff Summary Card。
7. Reviewer 或 Summarizer Agent 接手任务。
8. 接手 Agent 读取 Summary 并继续执行。
9. Supervisor 生成 Final Summary。
10. Handoff 页面或详情中可以查看完整交接记录。
11. Logs 中可以看到完整 Handoff 事件链路。
```

如果上述流程可稳定跑通，Handoff Manager MVP 即视为完成。
