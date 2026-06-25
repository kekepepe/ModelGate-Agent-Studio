# Logs / Observability 用户故事

> 所属产品：ModelGate Agent Studio
>
> 来源文档：`docs/prd/logs-observability-prd.md`
>
> 文档定位：将 Logs / Observability PRD 转化为可开发、可测试的用户故事与验收标准。

---

## 故事清单

| 编号 | 优先级 | 故事摘要 | 涉及页面 | 涉及接口 | 数据对象 |
|------|--------|----------|----------|----------|----------|
| US-LO-01 | P0 | 查看实时执行日志 | Workspace, ExecutionLogPanel | `GET /logs` | ExecutionLog |
| US-LO-02 | P0 | 筛选特定类型日志 | ExecutionLogPanel | `GET /logs` | ExecutionLog |
| US-LO-03 | P0 | 查看单条日志详情 | ExecutionLogPanel | `GET /logs/:logId` | ExecutionLog |
| US-LO-04 | P0 | 查看 Task 完整执行时间线 | LogsPage | `GET /logs/task/:taskId/timeline` | ExecutionLog, Task |
| US-LO-05 | P0 | 查看错误日志定位失败原因 | ExecutionLogPanel, ErrorPanel | `GET /logs` | ExecutionLog |
| US-LO-06 | P1 | 查看 Token 使用统计 | LogsPage | `GET /logs/aggregate` | ExecutionLog |
| US-LO-07 | P1 | 查看 Handoff 前后对比 | HandoffDetailModal | `GET /logs/handoff/:handoffId/compare` | ExecutionLog, HandoffRecord |

---

## P0 用户故事

### US-LO-01：查看实时执行日志

- **Summary:** 用户在 Workspace 底部的 ExecutionLogPanel 中实时看到模型调用、Agent 执行、工具调用等日志事件滚动更新。

#### Use Case:
- **As a** 需要跟踪任务执行过程的开发者
- **I want to** 在 Workspace 中实时看到所有执行日志
- **so that** 我可以了解任务执行到了哪一步，每个 Agent 做了什么

#### Acceptance Criteria:

- **Scenario:** 实时查看执行日志
- **Given:** Goal 正在执行中，系统正在产生各类事件
- **When:** 新的 ExecutionLog 被写入
- **Then:** ExecutionLogPanel 实时追加新日志（延迟 < 2 秒）
- **and Then:** 每条日志显示：时间、事件类型图标、状态、Agent、Model、摘要
- **and Then:** 日志按时间倒序排列，最新日志在顶部
- **and Then:** 面板收起时只显示摘要条："运行中 · 12 次模型调用 · 5 个 Task · 1 次 Handoff"

**涉及页面：** Workspace / ExecutionLogPanel / BottomConsole
**涉及接口：** `GET /logs`（轮询或 SSE）
**数据对象：** ExecutionLog

**可转测试的验收点：**
1. 前端：新日志追加时高亮显示 2 秒后恢复正常
2. 前端：`model_call` 类型显示 🧠 图标，`agent_step` 显示 🤖 图标，`tool_call` 显示 🔧 图标
3. 前端：`failed` 状态日志行背景为红色
4. 前端：收起状态下摘要条数字正确反映当前统计
5. 后端：`GET /logs?goal_id=xxx` 返回按 `created_at` 倒序排列的日志列表
6. 后端：每条日志包含 `event_type`、`event_status`、`agent_id`、`model_id`、`created_at`

---

### US-LO-02：筛选特定类型日志

- **Summary:** 用户在 ExecutionLogPanel 中按事件类型（模型调用、Handoff、错误等）或状态筛选日志。

#### Use Case:
- **As a** 排查特定问题的开发者
- **I want to** 只看某一种类型的日志（比如只看错误或只看 Handoff）
- **so that** 我可以快速定位感兴趣的事件，不被大量日志淹没

#### Acceptance Criteria:

- **Scenario:** 筛选日志
- **Given:** ExecutionLogPanel 中有多种类型的日志
- **When:** 我点击快速筛选按钮（如 [仅错误] [仅模型调用] [仅 Handoff]）
- **Then:** 日志列表只显示匹配类型的记录
- **and Then:** 我可以通过搜索框输入关键词搜索 input_summary / output_summary / error_message
- **and Then:** 筛选条件可以组合：类型 + 时间范围 + 关键词

**涉及页面：** Workspace / ExecutionLogPanel
**涉及接口：** `GET /logs`
**数据对象：** ExecutionLog

**可转测试的验收点：**
1. 前端：快速筛选按钮点击后立即过滤列表
2. 前端：[仅错误] 按钮只显示 `event_status = failed/error` 的日志
3. 前端：搜索框输入 "429" 后只显示包含 "429" 的日志
4. 后端：`GET /logs?event_type=model_call,error` 支持多类型筛选
5. 后端：`GET /logs?search=429` 在 `input_summary`、`output_summary`、`error_message` 中模糊匹配
6. 后端：组合筛选使用 AND 逻辑

---

### US-LO-03：查看单条日志详情

- **Summary:** 用户点击日志列表中的某一行，右侧弹出 Log Detail Drawer，展示完整的输入输出、token 消耗、元数据。

#### Use Case:
- **As a** 需要深入检查某次模型调用或 Agent 执行的开发者
- **I want to** 点击某条日志查看其完整详情
- **so that** 我可以检查具体的输入输出内容、token 消耗、错误详情

#### Acceptance Criteria:

- **Scenario:** 查看日志详情
- **Given:** ExecutionLogPanel 中有多条日志
- **When:** 我点击某条日志行
- **Then:** 右侧弹出 Log Detail Drawer，展示：事件类型、状态、关联 Goal/Task/Agent/Model、输入摘要、输出摘要、token_usage、metadata
- **and Then:** 如果是 `model_call` 日志，显示 latency_ms、routing_info
- **and Then:** 如果是 `error` 日志，显示 error_type、error_code、error_message

**涉及页面：** Workspace / ExecutionLogPanel / LogDetailDrawer
**涉及接口：** `GET /logs/:logId`
**数据对象：** ExecutionLog

**可转测试的验收点：**
1. 前端：点击日志行后 Drawer 从右侧滑出（300ms 动画）
2. 前端：Drawer 中关联实体（Goal/Task/Agent）可点击跳转
3. 前端：代码块输出保留语法高亮和复制按钮
4. 后端：`GET /logs/:logId` 返回完整 ExecutionLog 对象，包含 `metadata`
5. 后端：`model_call` 类型的 `metadata` 包含 `latency_ms`、`routing_reason`、`confidence`

---

### US-LO-04：查看 Task 完整执行时间线

- **Summary:** 用户在 Logs 页面查看某个 Task 的完整执行时间线，按时间顺序展示所有相关事件（模型调用、工具调用、状态变化、Handoff）。

#### Use Case:
- **As a** 需要复盘单个任务执行过程的开发者
- **I want to** 查看某个 Task 从头到尾的完整执行时间线
- **so that** 我可以理解该 Task 经历了哪些步骤、何时失败、何时交接、总共耗时多少

#### Acceptance Criteria:

- **Scenario:** 查看 Task 时间线
- **Given:** 某个 Task 已完成或失败，产生了多条日志
- **When:** 我在 Logs 页面点击该 Task 的 [查看时间线] 按钮
- **Then:** 页面展示垂直时间线，每个节点为一个事件，按时间顺序排列
- **and Then:** 时间线节点显示：时间、事件图标、类型、状态、Agent、Model、摘要
- **and Then:** Handoff 事件节点可点击展开，查看前后对比
- **and Then:** 底部显示统计：总耗时、总 token、模型调用次数、Handoff 次数、错误次数

**涉及页面：** LogsPage / TaskTimeline
**涉及接口：** `GET /logs/task/:taskId/timeline`
**数据对象：** ExecutionLog, Task

**可转测试的验收点：**
1. 前端：时间线采用垂直布局，事件节点用连线串联
2. 前端：不同事件类型用不同颜色节点（model_call=蓝、tool_call=青、handoff=紫、error=红）
3. 前端：底部统计栏数字正确
4. 后端：`GET /logs/task/:taskId/timeline` 返回 `{ events: [...], summary: { total_duration_ms, total_tokens, model_call_count, handoff_count, error_count } }`
5. 后端：`events[]` 按 `created_at` 升序排列
6. 后端：只返回 `task_id` 匹配的日志

---

### US-LO-05：查看错误日志定位失败原因

- **Summary:** 当任务失败时，ExecutionLogPanel 自动展开并切换到 Error Logs，集中展示所有错误事件，帮助用户快速定位失败原因。

#### Use Case:
- **As a** 需要排查任务失败原因的开发者
- **I want to** 在任务失败时快速看到所有错误日志
- **so that** 我可以定位失败根因，决定是重试还是 Handoff

#### Acceptance Criteria:

- **Scenario:** 错误发生后自动展示错误日志
- **Given:** 某个 Task 执行过程中发生了错误（如 429 rate limit、500 server error）
- **When:** 错误事件被写入 ExecutionLog
- **Then:** ExecutionLogPanel 自动从收起状态展开
- **and Then:** 自动切换到 Error Logs Tab
- **and Then:** 错误日志行显示红色背景，包含 error_type、error_code、error_message、关联 Agent/Model
- **and Then：** 每条错误日志提供 [查看详情] 和 [快速修复] 按钮

**涉及页面：** Workspace / ExecutionLogPanel / ErrorPanel
**涉及接口：** `GET /logs?event_status=error,failed`
**数据对象：** ExecutionLog

**可转测试的验收点：**
1. 前端：error 日志写入后，ExecutionLogPanel 在 1 秒内自动展开
2. 前端：Error Logs Tab 自动激活
3. 前端：错误日志行背景为红色，error_message 完整显示
4. 前端：点击 [快速修复] 弹出操作建议（如 Retry / Handoff）
5. 后端：`GET /logs?event_status=error,failed` 只返回错误和失败状态日志
6. 后端：错误日志的 `error_type` 枚举值：`api_error`、`tool_error`、`timeout`、`validation`

---

## P1 用户故事

### US-LO-06：查看 Token 使用统计

- **Summary:** 用户在 Logs 页面查看各 Agent 和各 Model 的 token 消耗统计，识别 token 消耗最高的环节。

#### Use Case:
- **As a** 需要优化成本的开发者
- **I want to** 查看每个 Agent 和每个 Model 的 token 消耗统计
- **so that** 我可以识别哪些 Agent 最费 token，哪些模型性价比最高

#### Acceptance Criteria:

- **Scenario:** 查看 token 统计
- **Given:** 系统中已有多条 model_call 和 agent_step 日志
- **When:** 我进入 Logs 页面的 Token Summary Tab
- **Then：** 展示两个统计图表：按 Agent 聚合的 token 消耗柱状图、按 Model 聚合的 token 消耗柱状图
- **and Then：** 显示总 token、总模型调用次数、平均延迟

**涉及页面：** LogsPage / TokenUsageSummary
**涉及接口：** `GET /logs/aggregate`
**数据对象：** ExecutionLog

**可转测试的验收点：**
1. 前端：柱状图正确展示各 Agent/Model 的 token 占比
2. 后端：`GET /logs/aggregate?group_by=agent&metric=total_tokens` 返回各 Agent 的 token 总和
3. 后端：`GET /logs/aggregate?group_by=model&metric=total_tokens` 返回各 Model 的 token 总和

---

### US-LO-07：查看 Handoff 前后对比

- **Summary:** 用户在 Handoff 相关日志中查看交接前后的上下文对比，评估信息传递完整度。

#### Use Case:
- **As a** 关注任务连续性的开发者
- **I want to** 对比 Handoff 前后 Agent 接收到的上下文
- **so that** 我可以评估交接是否丢失了关键信息

#### Acceptance Criteria:

- **Scenario:** 查看 Handoff 对比
- **Given：** Logs 中存在 `handoff_created` 和 `handoff_completed` 日志
- **When：** 我点击 Handoff 日志的 [查看对比] 按钮
- **Then：** 展示左右对比视图：Handoff 前上下文 vs Handoff 后上下文
- **and Then：** 显示 token 损失数量：`tokens_before_handoff - tokens_after_handoff`

**涉及页面：** LogsPage / HandoffDetailModal
**涉及接口：** `GET /logs/handoff/:handoffId/compare`
**数据对象：** ExecutionLog, HandoffRecord

**可转测试的验收点：**
1. 前端：对比视图采用左右分栏
2. 后端：`GET /logs/handoff/:handoffId/compare` 返回 `{ from_context, to_context, context_loss }`

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
