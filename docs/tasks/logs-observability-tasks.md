# Logs / Observability 开发任务拆解

> 基于 `docs/stories/logs-observability-stories.md` 的 5 条 P0 + 1 条 P1 用户故事拆解
>
> 拆分模式：Operations (Pattern 2 — CRUD) + Simple/Complex (Pattern 7)
> ——先建表 + 统一写入接口，再做查询 API，最后叠加前端面板和时间线。

---

## Epic: Logs / Observability

**目标：** 让开发者在 Workspace 和 Logs 页面中实时查看、筛选、追踪任务执行过程中的所有事件，快速定位错误。

**Epic 验收标准：**
1. Workspace 底部的 ExecutionLogPanel 实时滚动显示执行日志（延迟 < 2 秒）
2. 支持按事件类型、状态、关键词筛选日志
3. 点击单条日志可查看完整详情（输入输出、token、元数据）
4. Logs 页面可查看某个 Task 的完整执行时间线
5. 错误日志自动高亮为红色，自动展开面板
6. Token 使用统计可查看（P1）

---

## Feature 1: 日志数据模型与统一写入

> 对应 Story: US-LO-01 / US-LO-02 / US-LO-03 / US-LO-04 / US-LO-05 / US-LO-06
> 说明：所有 Story 共享 execution_logs 表和写入逻辑，合并为同一 Feature。

### Task 1.1: 创建 execution_logs 数据库表

| 属性 | 值 |
|------|-----|
| **task_id** | LO-T1.1 |
| **story_id** | US-LO-01 / US-LO-02 / US-LO-03 / US-LO-04 / US-LO-05 / US-LO-06 |
| **任务类型** | database |
| **文件** | `migrations/00x_create_execution_logs.sql` |
| **任务说明** | 创建 `execution_logs` 表，字段对齐 ExecutionLog 接口：log_id, event_type, event_status, agent_id, model_id, task_id, goal_id, handoff_id, input_summary, output_summary, error_message, error_type, error_code, token_usage (JSONB), latency_ms, metadata (JSONB), routing_info (JSONB), created_at。创建索引：idx_task_id、idx_goal_id、idx_agent_id、idx_model_id、idx_event_type、idx_event_status、idx_created_at、idx_handoff_id。 |
| **完成标准** | 1. 迁移脚本执行成功，表结构符合接口定义<br>2. 字段类型、NOT NULL 约束、默认值正确<br>3. 索引覆盖高频查询场景（按 task / goal / agent / model / event_type / status / created_at）<br>4. token_usage、metadata、routing_info 字段类型为 JSONB |
| **依赖任务** | 无 |
| **推荐顺序** | 1 |

---

### Task 1.2: 定义 LogEventType / LogEventStatus 枚举与日志写入服务

| 属性 | 值 |
|------|-----|
| **task_id** | LO-T1.2 |
| **story_id** | US-LO-01 / US-LO-02 / US-LO-03 / US-LO-04 / US-LO-05 / US-LO-06 |
| **任务类型** | backend |
| **文件** | `src/domain/log.ts`、`src/services/log/log-writer.ts` |
| **任务说明** | 1. 定义 `LogEventType` 枚举：model_call、agent_step、tool_call、task_status_change、quota_status_change、handoff_created、handoff_completed、error、supervisor_review、memory_write_candidate<br>2. 定义 `LogEventStatus` 枚举：success、failed、error、info、warning、pending、running、completed、cancelled、timeout、rate_limited、quota_exceeded、validation_error、unknown<br>3. 实现统一日志写入服务 `logWriter.write(logEntry)`：接收日志对象，校验 event_type 和 event_status 合法性，异步写入 execution_logs 表（setImmediate / 内存队列，不阻塞主流程）<br>4. 日志写入响应时间 < 50ms，后台批量 flush 到数据库（每 100 条或每 1 秒触发一次写入）<br>5. 提供便捷封装函数：`logModelCall()`、`logAgentStep()`、`logTaskStatusChange()`、`logError()`、`logHandoffEvent()` |
| **完成标准** | 1. 枚举值与 PRD / Schema 文档完全一致<br>2. 非法 event_type / event_status 写入时返回 400 或静默丢弃并告警<br>3. 写入服务响应时间 < 50ms（内存队列）<br>4. 批量写入逻辑可配置（batchSize / flushInterval）<br>5. 单元测试覆盖全部枚举值和写入逻辑 |
| **依赖任务** | LO-T1.1 |
| **推荐顺序** | 2 |

---

## Feature 2: 日志查询 API

> 对应 Story: US-LO-01 / US-LO-02 / US-LO-03 / US-LO-05
> 说明：列表查询和单条详情查询拆分为两个 Task，筛选能力合并到列表查询中。

### Task 2.1: GET /logs 列表 + 筛选 API

| 属性 | 值 |
|------|-----|
| **task_id** | LO-T2.1 |
| **story_id** | US-LO-01 / US-LO-02 / US-LO-05 |
| **任务类型** | backend |
| **文件** | `src/routes/logs.ts`、`src/services/log/log-query.service.ts` |
| **任务说明** | 1. 实现 `GET /logs` 接口，返回按 created_at 倒序排列的日志列表<br>2. 支持查询参数：<br>   - `goal_id`、`task_id`、`agent_id`、`model_id` — 精确匹配<br>   - `event_type` — 支持多值（逗号分隔），如 `event_type=model_call,error`<br>   - `event_status` — 支持多值，如 `event_status=error,failed`<br>   - `search` — 在 input_summary、output_summary、error_message 中模糊匹配<br>   - `start_time`、`end_time` — 时间范围筛选<br>   - `page`、`page_size` — 分页<br>3. 组合筛选使用 AND 逻辑<br>4. 返回结构：`{ items: [...], total, page, page_size }` |
| **完成标准** | 1. 无参数时返回全部日志，按 created_at 倒序<br>2. `?event_type=model_call,error` 只返回匹配类型的日志<br>3. `?search=429` 在 input_summary、output_summary、error_message 中模糊匹配<br>4. 时间范围筛选正确（start_time ≤ created_at ≤ end_time）<br>5. 分页返回 total、page、page_size<br>6. 集成测试覆盖全部筛选组合 |
| **依赖任务** | LO-T1.1 / LO-T1.2 |
| **推荐顺序** | 3 |

---

### Task 2.2: GET /logs/:logId 单条详情 API

| 属性 | 值 |
|------|-----|
| **task_id** | LO-T2.2 |
| **story_id** | US-LO-03 |
| **任务类型** | backend |
| **文件** | `src/routes/logs.ts` |
| **任务说明** | 1. 实现 `GET /logs/:logId` 接口<br>2. 返回完整 ExecutionLog 对象，包含全部字段：event_type、event_status、agent_id、model_id、task_id、goal_id、input_summary、output_summary、token_usage、latency_ms、routing_info、metadata、error_type、error_code、error_message、created_at<br>3. model_call 类型的 metadata 包含 latency_ms、routing_reason、confidence<br>4. error 类型的 metadata 包含 error_type、error_code、error_message<br>5. 关联的 Task、Agent、Goal 基本信息一并返回（减少前端多次请求） |
| **完成标准** | 1. 正常请求返回 200 + 完整 ExecutionLog JSON<br>2. logId 不存在返回 404<br>3. model_call 类型返回的 metadata 包含 latency_ms、routing_reason、confidence<br>4. error 类型返回的 error_type、error_code、error_message 完整<br>5. 关联实体（Task/Agent/Goal）信息正确填充<br>6. 集成测试覆盖 |
| **依赖任务** | LO-T1.1 / LO-T1.2 |
| **推荐顺序** | 4 |

---

## Feature 3: Task 时间线 API

> 对应 Story: US-LO-04

### Task 3.1: GET /logs/task/:taskId/timeline API

| 属性 | 值 |
|------|-----|
| **task_id** | LO-T3.1 |
| **story_id** | US-LO-04 |
| **任务类型** | backend |
| **文件** | `src/routes/logs.ts`、`src/services/log/timeline-builder.service.ts` |
| **任务说明** | 1. 实现 `GET /logs/task/:taskId/timeline` 接口<br>2. 查询该 task_id 关联的全部 execution_logs，按 created_at 升序排列<br>3. 构建时间线事件数组，每个事件包含：time、event_type、event_status、agent_id、model_id、summary、icon_type<br>4. 计算 summary 统计：total_duration_ms（首条到末条的时间差）、total_tokens（该 task 所有 model_call 的 token 总和）、model_call_count、handoff_count、error_count<br>5. 返回结构：`{ events: [...], summary: { total_duration_ms, total_tokens, model_call_count, handoff_count, error_count } }`<br>6. 只返回 task_id 匹配的日志（goal_id 不匹配的不返回） |
| **完成标准** | 1. 正常请求返回 200 + 时间线对象<br>2. events[] 按 created_at 升序排列<br>3. summary 统计数字正确（与数据库记录一致）<br>4. task_id 不存在或该 task 无日志时返回空 events 和全 0 summary<br>5. 集成测试覆盖 |
| **依赖任务** | LO-T1.1 / LO-T1.2 |
| **推荐顺序** | 5 |

---

## Feature 4: Workspace ExecutionLogPanel

> 对应 Story: US-LO-01 / US-LO-02 / US-LO-05
> 说明：先做 mock 数据让 UI 可独立运行，再对接真实 API。

### Task 4.1: ExecutionLogPanel 组件（mock 数据）

| 属性 | 值 |
|------|-----|
| **task_id** | LO-T4.1 |
| **story_id** | US-LO-01 / US-LO-02 / US-LO-05 |
| **任务类型** | frontend |
| **文件** | `src/components/ExecutionLogPanel.tsx`、`src/components/BottomConsole.tsx` |
| **任务说明** | 1. 实现 ExecutionLogPanel 组件，固定在 Workspace 底部<br>2. 展示日志列表，每行显示：时间、事件类型图标、event_status、agent_id、model_id、摘要（input_summary / output_summary 前 50 字）<br>3. 图标映射：model_call=🧠、agent_step=🤖、tool_call=🔧、handoff_created=🔄、handoff_completed=✓、error=⚠、quota_status_change=💰、task_status_change=📋、supervisor_review=👁、memory_write_candidate=📝<br>4. 日志按时间倒序排列，最新日志在顶部<br>5. 新日志追加时高亮显示 2 秒后恢复正常<br>6. failed/error 状态日志行背景为红色<br>7. 面板收起时只显示摘要条："运行中 · 12 次模型调用 · 5 个 Task · 1 次 Handoff"<br>8. 先使用 mock 数据（20-30 条假日志）让 UI 可独立运行和视觉验收 |
| **完成标准** | 1. 面板正确展示日志列表，时间倒序<br>2. 各事件类型图标与定义一致<br>3. 新日志追加时高亮 2 秒后恢复<br>4. error/failed 状态行背景为红色<br>5. 收起状态摘要条数字正确（基于当前日志统计）<br>6. 组件测试覆盖 |
| **依赖任务** | 无（与后端并行） |
| **推荐顺序** | 6 |

---

### Task 4.2: 日志筛选 UI + 对接真实 API

| 属性 | 值 |
|------|-----|
| **task_id** | LO-T4.2 |
| **story_id** | US-LO-01 / US-LO-02 |
| **任务类型** | frontend |
| **文件** | `src/hooks/useExecutionLogs.ts`、`src/api/logs.ts`、`src/components/ExecutionLogPanel.tsx` |
| **任务说明** | 1. 实现 `api.getLogs(params)` 封装 `GET /logs`<br>2. useExecutionLogs hook：轮询获取日志（每 2 秒），支持增量更新（只拉取最新 created_at 之后的日志）<br>3. 快速筛选按钮：[仅错误] [仅模型调用] [仅 Handoff] [全部]，点击后立即过滤列表<br>4. 搜索框：输入关键词后调用 `GET /logs?search=xxx`<br>5. 筛选条件可组合：类型 + 时间范围 + 关键词<br>6. 筛选参数通过 query string 传递给后端 |
| **完成标准** | 1. 轮询间隔 2 秒，新日志自动追加到列表顶部<br>2. [仅错误] 按钮只显示 event_status = failed/error 的日志<br>3. 搜索框输入 "429" 后只显示包含 "429" 的日志<br>4. 组合筛选调用真实 API，不是前端过滤<br>5. 切换 Goal/Task 时日志列表自动刷新<br>6. API 错误时显示降级提示 "日志加载失败" |
| **依赖任务** | LO-T2.1 / LO-T4.1 |
| **推荐顺序** | 7 |

---

### Task 4.3: 错误日志自动展开与高亮

| 属性 | 值 |
|------|-----|
| **task_id** | LO-T4.3 |
| **story_id** | US-LO-05 |
| **任务类型** | frontend |
| **文件** | `src/components/ExecutionLogPanel.tsx`、`src/components/ErrorPanel.tsx` |
| **任务说明** | 1. 当新写入的日志 event_status 为 error 或 failed 时，ExecutionLogPanel 自动从收起状态展开（1 秒内）<br>2. 自动切换到 Error Logs Tab（如果有 Tab 切换）<br>3. 错误日志行显示完整 error_message（不截断），背景为红色，文字为白色<br>4. 每条错误日志提供 [查看详情] 按钮，点击打开 LogDetailDrawer<br>5. 提供 [快速修复] 按钮，点击弹出操作建议（Retry / Handoff），操作为预留事件回调<br>6. ErrorPanel 组件：独立展示当前 Goal 的全部错误日志，按时间倒序 |
| **完成标准** | 1. error 日志写入后，ExecutionLogPanel 在 1 秒内自动展开<br>2. Error Logs Tab 自动激活<br>3. 错误日志行背景为红色，error_message 完整显示<br>4. [查看详情] 按钮打开 LogDetailDrawer<br>5. [快速修复] 按钮弹出 Retry / Handoff 选项<br>6. 组件测试覆盖错误自动展开和高亮 |
| **依赖任务** | LO-T4.1 / LO-T4.2 |
| **推荐顺序** | 8 |

---

## Feature 5: 单条日志详情

> 对应 Story: US-LO-03

### Task 5.1: LogDetailDrawer 组件

| 属性 | 值 |
|------|-----|
| **task_id** | LO-T5.1 |
| **story_id** | US-LO-03 |
| **任务类型** | frontend |
| **文件** | `src/components/LogDetailDrawer.tsx` |
| **任务说明** | 1. 实现 LogDetailDrawer 组件，从右侧滑出（300ms 动画）<br>2. 展示内容：事件类型、状态、关联 Goal/Task/Agent/Model（可点击跳转）、input_summary、output_summary、token_usage、metadata<br>3. model_call 类型额外显示：latency_ms、routing_info（routing_reason、confidence）<br>4. error 类型额外显示：error_type、error_code、error_message<br>5. output_summary 中的代码块保留语法高亮和复制按钮<br>6. 对接 `GET /logs/:logId` 真实 API |
| **完成标准** | 1. Drawer 从右侧滑出，300ms CSS transition<br>2. 关联实体（Goal/Task/Agent/Model）可点击跳转<br>3. model_call 类型正确显示 latency_ms 和 routing_info<br>4. error 类型正确显示 error_type、error_code、error_message<br>5. 代码块有语法高亮和复制按钮<br>6. 组件测试覆盖 |
| **依赖任务** | LO-T2.2 |
| **推荐顺序** | 9 |

---

## Feature 6: Task 执行时间线

> 对应 Story: US-LO-04

### Task 6.1: TaskTimeline 组件（mock 数据）

| 属性 | 值 |
|------|-----|
| **task_id** | LO-T6.1 |
| **story_id** | US-LO-04 |
| **任务类型** | frontend |
| **文件** | `src/components/TaskTimeline.tsx` |
| **任务说明** | 1. 实现 TaskTimeline 组件，垂直布局，事件节点用连线串联<br>2. 每个节点显示：时间、事件图标、类型、状态、Agent、Model、摘要<br>3. 不同事件类型用不同颜色节点：model_call=蓝、tool_call=青、handoff=紫、error=红、task_status_change=灰、agent_step=绿<br>4. 底部显示统计栏：总耗时、总 token、模型调用次数、Handoff 次数、错误次数<br>5. 点击节点可展开查看详情<br>6. 先使用 mock 数据 |
| **完成标准** | 1. 时间线采用垂直布局，节点用连线串联<br>2. 各事件类型颜色节点与定义一致<br>3. 底部统计栏数字正确（基于 mock 数据）<br>4. 节点点击可展开详情<br>5. 组件测试覆盖 |
| **依赖任务** | 无（与后端并行） |
| **推荐顺序** | 10 |

---

### Task 6.2: LogsPage Task 时间线页面 + 对接真实 API

| 属性 | 值 |
|------|-----|
| **task_id** | LO-T6.2 |
| **story_id** | US-LO-04 |
| **任务类型** | frontend |
| **文件** | `src/pages/LogsPage.tsx`、`src/hooks/useTaskTimeline.ts` |
| **任务说明** | 1. 实现 LogsPage 页面，路由 `/logs`<br>2. 页面包含：左侧 Task 列表、右侧 TaskTimeline 视图<br>3. 点击 Task 列表中的 [查看时间线] 按钮，右侧加载该 Task 的时间线<br>4. useTaskTimeline hook 对接 `GET /logs/task/:taskId/timeline`<br>5. 时间线加载时有 loading 状态，空时间线时显示 "该 Task 暂无执行日志"<br>6. 支持在时间线中点击节点打开 LogDetailDrawer |
| **完成标准** | 1. LogsPage 可访问 `/logs`<br>2. 点击 [查看时间线] 后右侧加载真实时间线数据<br>3. 时间线事件按时间升序排列<br>4. 底部统计栏数字与后端返回一致<br>5. 空时间线有友好提示<br>6. 组件测试覆盖 |
| **依赖任务** | LO-T3.1 / LO-T6.1 / LO-T5.1 |
| **推荐顺序** | 11 |

---

## Feature 7: Token 使用统计（P1）

> 对应 Story: US-LO-06

### Task 7.1: GET /logs/aggregate 聚合统计 API

| 属性 | 值 |
|------|-----|
| **task_id** | LO-T7.1 |
| **story_id** | US-LO-06 |
| **任务类型** | backend |
| **文件** | `src/routes/logs.ts`、`src/services/log/log-aggregate.service.ts` |
| **任务说明** | 1. 实现 `GET /logs/aggregate` 接口<br>2. 支持参数：`group_by=agent|model`、`metric=total_tokens|request_count|avg_latency`<br>3. `group_by=agent` 时按 agent_id 聚合，返回每个 Agent 的 token 总和、调用次数、平均延迟<br>4. `group_by=model` 时按 model_id 聚合，返回每个 Model 的 token 总和、调用次数、平均延迟<br>5. 只统计 event_type = model_call 或 agent_step 的日志<br>6. 返回结构：`{ items: [{ group_id, group_name, total_tokens, request_count, avg_latency_ms }], total_tokens, total_requests }` |
| **完成标准** | 1. `group_by=agent&metric=total_tokens` 返回各 Agent 的 token 总和<br>2. `group_by=model&metric=total_tokens` 返回各 Model 的 token 总和<br>3. 统计数字与数据库记录一致<br>4. 无记录时返回空数组和全 0 总计<br>5. 集成测试覆盖 |
| **依赖任务** | LO-T1.1 / LO-T1.2 |
| **推荐顺序** | 12（P1，延后） |

---

### Task 7.2: TokenUsageSummary 组件

| 属性 | 值 |
|------|-----|
| **task_id** | LO-T7.2 |
| **story_id** | US-LO-06 |
| **任务类型** | frontend |
| **文件** | `src/components/TokenUsageSummary.tsx` |
| **任务说明** | 1. 实现 TokenUsageSummary 组件，在 LogsPage 中以 Tab 形式展示<br>2. 展示两个统计图表：按 Agent 聚合的 token 消耗柱状图、按 Model 聚合的 token 消耗柱状图<br>3. 使用简单 CSS/SVG 柱状图（不引入重量级图表库如 ECharts/D3，MVP 阶段用 div 高度模拟柱状图）<br>4. 显示总 token、总模型调用次数、平均延迟<br>5. 对接 `GET /logs/aggregate` |
| **完成标准** | 1. 柱状图正确展示各 Agent/Model 的 token 占比<br>2. 总 token、总调用次数、平均延迟数字正确<br>3. 无数据时显示 "暂无 token 使用记录"<br>4. 组件测试覆盖 |
| **依赖任务** | LO-T7.1 |
| **推荐顺序** | 13（P1，延后） |

---

## Feature 8: 测试与质量保障

### Task 8.1: 日志枚举与写入服务单元测试

| 属性 | 值 |
|------|-----|
| **task_id** | LO-T8.1 |
| **story_id** | US-LO-01 / US-LO-02 / US-LO-05 |
| **任务类型** | test |
| **文件** | `tests/logs/log-writer.test.ts` |
| **任务说明** | 1. LogEventType 枚举值完整性测试（10 个类型）<br>2. LogEventStatus 枚举值完整性测试（14 个状态）<br>3. 日志写入服务测试：正常写入 / 非法类型拒绝 / 批量写入 / 队列溢出处理<br>4. 便捷封装函数测试：`logModelCall()`、`logError()` 等 |
| **完成标准** | 1. 全部枚举值有测试用例<br>2. 批量写入逻辑正确（batchSize 触发和 flushInterval 触发）<br>3. 测试覆盖率 ≥ 85% |
| **依赖任务** | LO-T1.2 |
| **推荐顺序** | 14（与开发并行） |

---

### Task 8.2: API 集成测试

| 属性 | 值 |
|------|-----|
| **task_id** | LO-T8.2 |
| **story_id** | US-LO-01 / US-LO-02 / US-LO-03 / US-LO-04 / US-LO-06 |
| **任务类型** | test |
| **文件** | `tests/logs.api.test.ts` |
| **任务说明** | 1. `GET /logs` — 正常/筛选/event_type多值/search模糊匹配/时间范围/分页/空列表<br>2. `GET /logs/:logId` — 正常/不存在/model_call详情/error详情<br>3. `GET /logs/task/:taskId/timeline` — 正常/空时间线/统计正确<br>4. `GET /logs/aggregate` — agent分组/model分组/无记录（P1） |
| **完成标准** | 1. 全部 4 个 API 的 happy path 和错误 path 都有测试<br>2. 每个 API 至少 3 个测试用例<br>3. 筛选组合测试覆盖 AND 逻辑<br>4. 数据库状态在每次测试后正确清理 |
| **依赖任务** | LO-T2.1 / LO-T2.2 / LO-T3.1 / LO-T7.1 |
| **推荐顺序** | 15（与开发并行） |

---

### Task 8.3: 前端组件测试

| 属性 | 值 |
|------|-----|
| **task_id** | LO-T8.3 |
| **story_id** | US-LO-01 / US-LO-02 / US-LO-03 / US-LO-04 / US-LO-05 / US-LO-06 |
| **任务类型** | test |
| **文件** | `tests/components/ExecutionLogPanel.test.tsx`、`tests/components/LogDetailDrawer.test.tsx`、`tests/components/TaskTimeline.test.tsx`、`tests/components/TokenUsageSummary.test.tsx` |
| **任务说明** | 1. ExecutionLogPanel：日志列表渲染、图标映射、时间倒序、高亮动画、收起状态、筛选按钮点击<br>2. LogDetailDrawer：字段展示、model_call 额外信息、error 额外信息、代码块复制<br>3. TaskTimeline：垂直布局、节点颜色、统计栏、节点点击<br>4. TokenUsageSummary：柱状图渲染、数字展示、空状态（P1）<br>5. ErrorPanel：错误自动展开、红色高亮、按钮点击 |
| **完成标准** | 1. 全部 5 个组件有独立测试文件<br>2. 每个组件覆盖主要渲染状态和用户交互<br>3. 快照测试覆盖关键 UI 状态 |
| **依赖任务** | LO-T4.1 / LO-T5.1 / LO-T6.1 / LO-T7.2 / LO-T4.3 |
| **推荐顺序** | 16（与开发并行） |

---

## 推荐开发顺序

```
Phase 1 — 数据模型 + 写入服务 + 查询 API（1 周）
  LO-T1.1   创建 execution_logs 表
  LO-T1.2   LogEventType/LogEventStatus 枚举 + 日志写入服务
  LO-T2.1   GET /logs 列表 + 筛选 API
  LO-T2.2   GET /logs/:logId 详情 API
  LO-T3.1   GET /logs/task/:taskId/timeline API
  LO-T8.1   日志写入单元测试（与开发并行）

Phase 2 — Workspace 日志面板（3-4 天）
  LO-T4.1   ExecutionLogPanel 组件（mock 数据）
  LO-T4.2   对接真实日志 API + 筛选 UI
  LO-T4.3   错误日志自动展开 + 高亮
  LO-T5.1   LogDetailDrawer 组件
  LO-T8.3   前端组件测试（与开发并行）

Phase 3 — Task 时间线页面（2-3 天）
  LO-T6.1   TaskTimeline 组件（mock 数据）
  LO-T6.2   LogsPage + 对接真实 timeline API
  LO-T8.2   API 集成测试（与开发并行）

Phase 4 — Token 统计（P1，2 天，可选）
  LO-T7.1   GET /logs/aggregate API
  LO-T7.2   TokenUsageSummary 组件
```

---

## 按 Phase 排期的任务看板

### Phase 1 — 数据模型 + 查询 API（1 周）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| LO-T1.1 | execution_logs 表结构 | database | 无 | LO-01~06 |
| LO-T1.2 | 枚举 + 日志写入服务 | backend | LO-T1.1 | LO-01~06 |
| LO-T2.1 | GET /logs 列表 + 筛选 | backend | LO-T1.2 | LO-01/02/05 |
| LO-T2.2 | GET /logs/:logId 详情 | backend | LO-T1.2 | LO-03 |
| LO-T3.1 | GET /logs/task/:taskId/timeline | backend | LO-T1.2 | LO-04 |
| LO-T8.1 | 日志写入单元测试 | test | LO-T1.2 | LO-01/02/05 |

**Phase 1 交付物：** 完整的日志表结构和写入服务，可通过 HTTP 工具查询日志列表、单条详情、Task 时间线。其他模块（Handoff、Runtime、Quota）可调用日志写入服务记录事件。

### Phase 2 — Workspace 日志面板（3-4 天）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| LO-T4.1 | ExecutionLogPanel（mock） | frontend | 无 | LO-01/02/05 |
| LO-T4.2 | 对接真实 API + 筛选 | frontend | LO-T2.1/4.1 | LO-01/02 |
| LO-T4.3 | 错误日志自动展开 + 高亮 | frontend | LO-T4.1/4.2 | LO-05 |
| LO-T5.1 | LogDetailDrawer | frontend | LO-T2.2 | LO-03 |
| LO-T8.3 | 前端组件测试 | test | LO-T4/5.x | LO-01~05 |

**Phase 2 交付物：** Workspace 底部实时显示执行日志，支持筛选和搜索，点击可查看详情，错误日志自动高亮并展开。

### Phase 3 — Task 时间线页面（2-3 天）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| LO-T6.1 | TaskTimeline 组件（mock） | frontend | 无 | LO-04 |
| LO-T6.2 | LogsPage + 对接真实 API | frontend | LO-T3.1/6.1/5.1 | LO-04 |
| LO-T8.2 | API 集成测试 | test | LO-T2/3.x | LO-01~04/06 |

**Phase 3 交付物：** Logs 页面可查看 Task 完整执行时间线，包含事件节点和统计栏。

### Phase 4 — Token 统计（P1，2 天，可选）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| LO-T7.1 | GET /logs/aggregate | backend | LO-T1.2 | LO-06 |
| LO-T7.2 | TokenUsageSummary 组件 | frontend | LO-T7.1 | LO-06 |

**Phase 4 交付物：** 可查看按 Agent 和 Model 聚合的 token 消耗统计。

---

## 风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| 日志高频写入导致数据库压力 | Phase 1 性能问题 | LO-T1.2 使用内存队列 + 批量写入（每 100 条或 1 秒 flush），MVP 不引入 Kafka/ELK |
| 前端轮询 2 秒对服务端造成压力 | Phase 2 性能问题 | 先实现轮询，后续可改为 SSE 推送；API 响应优化到 < 50ms |
| TaskTimeline 需要多表关联查询 | Phase 3 查询慢 | LO-T3.1 先用单表查询（execution_logs），关联信息通过已有索引快速查找；复杂聚合后续加物化视图 |
| 日志量增长后查询变慢 | 后期体验差 | MVP 阶段不处理，数据量超过 10 万条后考虑按时间分区或归档 |
| Token 柱状图需要图表库 | LO-T7.2 引入依赖 | 用简单 div 高度模拟柱状图，不引入 ECharts/D3，MVP 后根据需求决定是否引入 |
| 其他模块未就绪导致日志来源不足 | Phase 2 UI 空旷 | LO-T4.1 使用丰富的 mock 数据（30+ 条），覆盖 10 种事件类型；等 Runtime/Handoff 等模块就绪后自然产生真实日志 |

---

## Story → Task 映射表

| Story | 涉及 Task | 是否完整覆盖 |
|-------|-----------|--------------|
| US-LO-01 查看实时执行日志 | LO-T1.1 / LO-T1.2 / LO-T2.1 / LO-T4.1 / LO-T4.2 | 是 |
| US-LO-02 筛选特定类型日志 | LO-T1.1 / LO-T2.1 / LO-T4.2 | 是 |
| US-LO-03 查看单条日志详情 | LO-T1.1 / LO-T2.2 / LO-T5.1 | 是 |
| US-LO-04 查看 Task 完整执行时间线 | LO-T1.1 / LO-T3.1 / LO-T6.1 / LO-T6.2 | 是 |
| US-LO-05 查看错误日志定位失败原因 | LO-T1.2 / LO-T2.1 / LO-T4.1 / LO-T4.3 | 是 |
| US-LO-06 查看 Token 使用统计 | LO-T1.1 / LO-T7.1 / LO-T7.2 | 是 |

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
>
> 相关文档：
> - `docs/stories/logs-observability-stories.md` — 用户故事来源
> - `docs/prd/logs-observability-prd.md` — 产品需求
> - `docs/architecture/数据结构与数据库Schema.md` — Schema 定义
