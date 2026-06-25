# Handoff Manager 开发任务拆解

> 基于 `docs/stories/handoff-manager-stories.md` 的 7 条 P0 + 1 条 P1 用户故事拆解
>
> 拆分模式：Workflow Steps (Pattern 1) + Simple/Complex (Pattern 7)
> ——先做数据模型 + 核心 API 让 Handoff 可触发和查询，再叠加 Summary 生成，最后补前端页面。

---

## Epic: Handoff Manager

**目标：** 让任务可在不同 Agent/模型间安全交接，不丢失上下文。

**Epic 验收标准：**
1. 用户可在 Workspace 中对 running/failed 的 Task 手动触发 Handoff
2. Handoff 状态（requested → generating_summary → ready → accepted → completed）在 Workspace 实时可视化
3. 交接摘要包含完整的上下文结构，接手 Agent 可继续执行任务
4. Handoff 全过程事件写入 ExecutionLog，可在 Bottom Console 查看
5. 同一 Task 在 Handoff 完成前不可重复触发

---

## Feature 1: Handoff 数据模型与状态机

> 对应 Story: US-HM-01 / US-HM-02 / US-HM-03 / US-HM-04 / US-HM-05 / US-HM-07
> 说明：所有 Story 共享 HandoffRecord 表、HandoffSummary 结构和状态机，合并为同一 Feature。

### Task 1.1: 创建 handoff_records 数据库表

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T1.1 |
| **story_id** | US-HM-01 / US-HM-02 / US-HM-03 / US-HM-04 / US-HM-05 / US-HM-07 |
| **任务类型** | database |
| **文件** | `migrations/00x_create_handoff_records.sql` |
| **任务说明** | 创建 `handoff_records` 表，字段对齐 HandoffRecord 接口：id, goal_id, task_id, from_agent_id, from_model_id, from_worker_id, to_agent_id, to_model_id, reason, reason_description, handoff_summary (JSONB), status, result_after_handoff, result_note, tokens_before_handoff, tokens_after_handoff, created_at, summary_generated_at, accepted_at, completed_at, updated_at。创建索引：idx_task_id_status、idx_goal_id、idx_from_agent_id、idx_to_agent_id。 |
| **完成标准** | 1. 迁移脚本执行成功，表结构符合接口定义<br>2. provider + model_id 组合唯一约束<br>3. 索引覆盖高频查询场景（按 task + status 查 active handoff）<br>4. handoff_summary 字段类型为 JSONB |
| **依赖任务** | 无 |
| **推荐顺序** | 1 |

---

### Task 1.2: 定义 HandoffStatus 状态机与转换规则

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T1.2 |
| **story_id** | US-HM-02 / US-HM-04 / US-HM-05 / US-HM-07 |
| **任务类型** | backend |
| **文件** | `src/domain/handoff.ts` 或 `src/models/handoff.ts` |
| **任务说明** | 1. 定义 HandoffStatus 枚举：requested / generating_summary / ready / accepted / completed / failed<br>2. 实现状态机校验器，只允许合法转换：requested → generating_summary / failed；generating_summary → ready / failed；ready → accepted / failed；accepted → completed / failed；completed / failed 为终态<br>3. 非法转换抛 400 InvalidStateTransition<br>4. 实现 isActiveHandoff 工具函数：status ∈ [requested, generating_summary, ready, accepted] 时返回 true，用于防重复校验 |
| **完成标准** | 1. 状态机代码有明确的转换矩阵，非法转换返回 400<br>2. 单元测试覆盖全部 6 个状态 × 所有可能事件<br>3. 终态（completed/failed）不可再被修改<br>4. isActiveHandoff 测试覆盖全部状态 |
| **依赖任务** | HM-T1.1 |
| **推荐顺序** | 2 |

---

### Task 1.3: 创建 HandoffSummary 数据结构与兜底生成

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T1.3 |
| **story_id** | US-HM-03 |
| **任务类型** | backend |
| **文件** | `src/domain/handoff.ts` |
| **任务说明** | 1. 定义 HandoffSummary 接口：original_goal, current_task, completed_work[], unfinished_work[], important_constraints[], key_decisions[], errors_and_risks[], next_suggested_steps[], context_needed[]<br>2. 实现兜底摘要生成函数：当 LLM 生成失败时，自动组装包含 task_id、from_agent、to_agent、reason、当前 task 描述的基本摘要<br>3. JSON Schema 校验规则，确保字段类型正确<br>4. 兜底摘要不依赖 LLM，保证 Summary 永远不会完全为空 |
| **完成标准** | 1. TypeScript 接口与数据库 JSONB 字段对齐<br>2. JSON Schema 校验覆盖全部 9 个字段<br>3. 兜底摘要生成函数可独立测试，输出非空 JSON<br>4. 单元测试覆盖：正常 JSON / 缺字段 / 兜底生成 |
| **依赖任务** | HM-T1.1 |
| **推荐顺序** | 3 |

---

## Feature 2: Handoff 核心工作流 API

> 对应 Story: US-HM-01 / US-HM-04 / US-HM-05 / US-HM-07
> 说明：按操作拆分 4 个 API Task，先实现触发+查询让工作流可运行，再叠加 accept 和 result。

### Task 2.1: POST /tasks/:taskId/handoff（手动触发 + 防重复）

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T2.1 |
| **story_id** | US-HM-01 / US-HM-07 |
| **任务类型** | backend |
| **文件** | `src/routes/handoffs.ts`、`src/services/handoff/handoff-trigger.service.ts` |
| **任务说明** | 1. 接收 { to_agent_id, to_model_id, reason, reason_description }<br>2. 校验：Task 存在且 status 为 running 或 failed<br>3. 校验：该 Task 没有 active Handoff（通过 HM-T1.2 的 isActiveHandoff），否则返回 409<br>4. 创建 HandoffRecord，status = requested，自动填充 from_agent_id、from_model_id、from_worker_id<br>5. 更新 Task.status = handoff<br>6. 返回 { handoff_id, status: "requested" }<br>7. 触发 handoff_status_updated 事件（简单 EventEmitter，不引入消息队列） |
| **完成标准** | 1. 正常请求返回 201 + { handoff_id, status }<br>2. Task 不存在返回 404，状态非法返回 400<br>3. 已有 active Handoff 返回 409，error.code = "CONFLICT"<br>4. 创建成功后 Task.status 更新为 handoff<br>5. 集成测试覆盖 |
| **依赖任务** | HM-T1.1 / HM-T1.2 |
| **推荐顺序** | 4 |

---

### Task 2.2: GET /handoffs/:handoffId（查询单条 + 完整摘要）

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T2.2 |
| **story_id** | US-HM-02 / US-HM-03 |
| **任务类型** | backend |
| **文件** | `src/routes/handoffs.ts`、`src/services/handoff/handoff-query.service.ts` |
| **任务说明** | 1. 根据 handoffId 返回完整 HandoffRecord，包含 handoff_summary 对象<br>2. 如果 handoff_summary 为空且 status 为 requested，返回提示 "Summary generating..."<br>3. 同时返回关联的 Task 基本信息（title、description）和 Agent 信息（name、role），减少前端多次请求<br>4. 如果 handoff 有关联的 WorkerSession（to_worker_id），一并返回 Worker 状态 |
| **完成标准** | 1. 正常请求返回 200 + 完整 HandoffRecord JSON<br>2. handoffId 不存在返回 404<br>3. 返回字段包含全部 HandoffSummary 9 个字段（或兜底数据）<br>4. 关联的 Task 和 Agent 信息正确填充<br>5. 集成测试覆盖 |
| **依赖任务** | HM-T1.1 / HM-T1.3 |
| **推荐顺序** | 5 |

---

### Task 2.3: POST /handoffs/:handoffId/accept（接受交接 + 创建 Worker）

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T2.3 |
| **story_id** | US-HM-04 |
| **任务类型** | backend |
| **文件** | `src/routes/handoffs.ts`、`src/services/handoff/handoff-accept.service.ts` |
| **任务说明** | 1. 校验：HandoffRecord 存在且 status = ready<br>2. 更新 status = accepted，记录 accepted_at<br>3. 创建新的 WorkerSession：agent_id = to_agent_id，model_id = to_model_id，task_id = 原 Task，inherited_from_handoff_id = handoff_id<br>4. 更新 Task：status = running，assigned_agent_id = to_agent_id，assigned_worker_id = 新 worker_id<br>5. 原 WorkerSession 状态更新为 handoff_required 或 completed（简单标记，不阻塞）<br>6. 触发 handoff_status_updated 事件<br>7. 返回 { worker_id, status: "accepted" } |
| **完成标准** | 1. 正常 accept 返回 200 + { worker_id, status }<br>2. status 不是 ready 时返回 400<br>3. 新 WorkerSession 的 inherited_from_handoff_id 正确指向 handoff_id<br>4. Task 的 assigned_agent_id / assigned_worker_id 已更新<br>5. 三表更新使用数据库事务，失败时回滚<br>6. 集成测试覆盖 |
| **依赖任务** | HM-T2.1 / HM-T2.2 |
| **推荐顺序** | 7 |

---

### Task 2.4: PATCH /handoffs/:handoffId/result（记录结果）

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T2.4 |
| **story_id** | US-HM-05 |
| **任务类型** | backend |
| **文件** | `src/routes/handoffs.ts` |
| **任务说明** | 1. 接收 { result_after_handoff, result_note?, status?: "completed" }<br>2. 校验：HandoffRecord 存在且 status = accepted<br>3. 更新 result_after_handoff、result_note、status = completed、completed_at<br>4. result_after_handoff 枚举校验：只能是 success / partial / failed<br>5. 返回完整 HandoffRecord |
| **完成标准** | 1. 正常请求返回 200 + 更新后的 HandoffRecord<br>2. 枚举校验非法值返回 400<br>3. 只有 status = accepted 的 Handoff 才能被标记 completed<br>4. completed_at 时间戳被正确记录<br>5. 集成测试覆盖 |
| **依赖任务** | HM-T2.1 / HM-T1.2 |
| **推荐顺序** | 6 |

---

## Feature 3: Handoff Summary 生成引擎

> 对应 Story: US-HM-03
> 说明：先做 Prompt 模板和简单 mock 生成让 Summary 有内容，再做真实 LLM 调用和上下文收集。

### Task 3.1: Summary Prompt 模板 + 简单 mock 生成

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T3.1 |
| **story_id** | US-HM-03 |
| **任务类型** | backend |
| **文件** | `src/services/handoff/summary-generator.ts` |
| **任务说明** | 1. 设计 Handoff Summary Prompt，要求 LLM 输出严格 JSON 格式（对应 HandoffSummary 的 9 个字段）<br>2. 实现 LLM 调用封装：支持指定模型、超时控制（30 秒）、重试机制（最多 2 次）<br>3. 实现 JSON 解析容错：LLM 输出非严格 JSON 时，用正则/二次校正提取字段<br>4. **MVP 第一阶段**：先实现 mock 生成器——不调用真实 LLM，而是基于 Task 描述和 Agent 角色生成固定格式的结构化摘要（确保 UI 有内容可展示）<br>5. mock 生成器逻辑：original_goal = goal 描述，current_task = task 描述，completed_work = ["已执行步骤1", "已执行步骤2"]（从 execution_logs 中提取 agent_step 类型日志），unfinished_work = [task 描述中的未完成部分]，errors_and_risks = ["当前无错误"] 或从 error 日志提取 |
| **完成标准** | 1. Prompt 模板定义完整，包含 9 个字段的示例<br>2. mock 生成器可独立运行，输出符合 HandoffSummary 结构<br>3. mock 生成不依赖外部 LLM 服务，响应时间 < 100ms<br>4. JSON 解析失败时有 fallback 机制<br>5. 单元测试覆盖 mock 生成和 JSON 解析容错 |
| **依赖任务** | HM-T1.3 |
| **推荐顺序** | 8 |

---

### Task 3.2: 上下文数据收集服务

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T3.2 |
| **story_id** | US-HM-03 |
| **任务类型** | backend |
| **文件** | `src/services/handoff/context-collector.ts` |
| **任务说明** | 1. 从 tasks 表读取：task 描述、完成标准、当前输出、已用 token、已耗时<br>2. 从 agents 表读取：from_agent 的系统提示词、角色、配置<br>3. 从 execution_logs 表读取：该 task 相关的 model_call / agent_step / tool_call / error 日志<br>4. 从 handoff_records 表读取：该 task 是否有历史 handoff（如果有，合并历史上下文）<br>5. 上下文长度超过模型上下文窗口时，有截断策略（优先保留最近日志和 task 描述）<br>6. 收集到的上下文用于填充 Prompt 变量 |
| **完成标准** | 1. 上下文数据包含 Task、Agent、Logs 三个维度<br>2. 日志只收集与该 task_id / goal_id 相关的记录<br>3. 超长上下文有截断策略，优先保留最近 10 条日志和完整 task 描述<br>4. 单元测试覆盖上下文组装逻辑 |
| **依赖任务** | HM-T3.1 |
| **推荐顺序** | 10 |

---

### Task 3.3: 集成 Summary 生成到 Handoff 工作流（异步）

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T3.3 |
| **story_id** | US-HM-03 |
| **任务类型** | backend |
| **文件** | `src/services/handoff/handoff-trigger.service.ts`、`src/services/handoff/summary-generator.ts` |
| **任务说明** | 1. 在 POST /tasks/:taskId/handoff 成功后，异步触发 Summary 生成（使用 setImmediate / 内存队列，不引入 Kafka/RabbitMQ）<br>2. HandoffRecord status 从 requested → generating_summary → ready<br>3. Summary 生成完成后，将结果写入 handoff_summary 字段，更新 summary_generated_at<br>4. 如果生成失败，status → failed，记录错误原因，并写入 HM-T1.3 的兜底摘要（保证 UI 永远有内容）<br>5. 整个生成过程不阻塞 HTTP 响应（响应 < 500ms）<br>6. 状态变化触发 handoff_status_updated 事件（EventEmitter） |
| **完成标准** | 1. Handoff 创建后，Summary 在后台异步生成<br>2. 状态正确流转：requested → generating_summary → ready<br>3. 生成失败时状态变为 failed，但有兜底摘要保证 UI 不空<br>4. HTTP 接口不等待 Summary 生成完成<br>5. 生成完成后触发 handoff_status_updated 事件<br>6. 端到端测试覆盖完整工作流 |
| **依赖任务** | HM-T2.1 / HM-T3.1 / HM-T3.2 |
| **推荐顺序** | 11 |

---

## Feature 4: Handoff 日志与事件

> 对应 Story: US-HM-06
> 说明：日志写入和前端展示拆为两个 Task，后端先实现，前端并行开发。

### Task 4.1: Handoff 事件写入 ExecutionLog

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T4.1 |
| **story_id** | US-HM-06 |
| **任务类型** | backend |
| **文件** | `src/services/handoff/handoff-event-logger.ts` |
| **任务说明** | 1. 在 Handoff 状态每次变化时，异步写入 ExecutionLog（复用已有日志写入接口，不新建表）<br>2. event_type 枚举：handoff_requested / handoff_summary_generating / handoff_summary_ready / handoff_accepted / handoff_completed / handoff_failed<br>3. event_status 映射：非 failed 状态 = info，failed = error<br>4. 日志内容包含：handoff_id、task_id、goal_id、from_agent_id、to_agent_id、action、状态描述<br>5. 日志写入不阻塞主流程（异步，setImmediate） |
| **完成标准** | 1. 每个 Handoff 状态变化都触发一条 ExecutionLog 写入<br>2. event_type 枚举值正确<br>3. failed 状态的日志 event_level = error，其余为 info<br>4. 可通过 GET /logs?handoff_id=xxx 查询到全部关联日志<br>5. 日志写入不阻塞主流程<br>6. 单元测试覆盖全部 6 种事件类型 |
| **依赖任务** | HM-T1.2 / HM-T2.1 |
| **推荐顺序** | 9 |

---

### Task 4.2: ExecutionLogPanel Handoff 日志渲染

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T4.2 |
| **story_id** | US-HM-06 |
| **任务类型** | frontend |
| **文件** | `src/components/ExecutionLogPanel.tsx` |
| **任务说明** | 1. ExecutionLogPanel 中 Handoff 事件显示紫色标签<br>2. 点击 Handoff 日志可高亮对应 TaskCard 或打开 HandoffDetailDrawer<br>3. handoff_failed 事件显示红色背景<br>4. 日志摘要显示："Handoff requested: Agent A → Agent B (reason: quota_exceeded)"<br>5. 双击日志打开 HandoffDetailDrawer |
| **完成标准** | 1. Handoff 事件在 Event Log Tab 中显示紫色标签<br>2. 错误 Handoff 显示红色背景<br>3. 点击 Handoff 日志行，对应 TaskCard 高亮（border flash）<br>4. 日志摘要文本包含 from_agent、to_agent、reason 信息<br>5. 前端组件测试覆盖 |
| **依赖任务** | HM-T4.1 |
| **推荐顺序** | 14 |

---

## Feature 5: Workspace Handoff 可视化

> 对应 Story: US-HM-01 / US-HM-02 / US-HM-03 / US-HM-04
> 说明：先做 mock UI 让页面可独立验收，再对接真实 API。

### Task 5.1: TaskCard Handoff 状态展示 + HandoffStatusIndicator（mock 数据）

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T5.1 |
| **story_id** | US-HM-02 |
| **任务类型** | frontend |
| **文件** | `src/components/TaskCard.tsx`、`src/components/HandoffStatusIndicator.tsx` |
| **任务说明** | 1. TaskCard 在 handoff 状态时显示紫色边框 + 紫色状态标签，状态变化时有 300ms CSS 过渡动画<br>2. running → handoff 时触发紫色 pulse 动画，handoff → running（accepted 后）时触发平滑过渡<br>3. HandoffStatusIndicator 组件显示在 TaskCard 底部，展示状态进度条：[✓ requested] → [✍ generating_summary] → [○ ready] → [○ accepted] → [○ completed]<br>4. 各状态对应图标：requested=黄色🔄、generating_summary=紫色脉冲✍、ready=紫色📋、accepted=蓝色▶、completed=绿色✓<br>5. Handoff 完成后（completed/failed），Indicator 3 秒后自动消失<br>6. 先使用 mock 数据让 UI 可独立运行和视觉验收 |
| **完成标准** | 1. TaskCard handoff 状态下边框为紫色（#9333ea）<br>2. 状态切换有 300ms CSS transition<br>3. Indicator 进度条正确显示当前状态节点和待完成节点<br>4. generating_summary 状态的 ✍ 图标有 pulse 动画<br>5. completed 后 3 秒自动消失<br>6. 组件测试覆盖 6 种状态渲染 |
| **依赖任务** | 无（与后端并行） |
| **推荐顺序** | 12 |

---

### Task 5.2: Handoff 触发面板（选择 Agent + 填写原因）

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T5.2 |
| **story_id** | US-HM-01 / US-HM-07 |
| **任务类型** | frontend |
| **文件** | `src/components/HandoffConfirmModal.tsx`、`src/hooks/useHandoff.ts` |
| **任务说明** | 1. TaskCard / TaskDetailPanel 上 [Handoff] 按钮：只在 running 或 failed 状态且没有 active Handoff 时显示<br>2. 点击后弹出 HandoffConfirmModal，包含：接手 Agent 下拉选择（从 AgentRegistry 获取可用 Agent 列表）、交接原因下拉（quota_exceeded / error / quality_issue / role_mismatch / manual / context_limit / other）、原因描述文本框（可选）、[确认]/[取消] 按钮<br>3. 确认后调用 POST /tasks/:taskId/handoff<br>4. 成功后 TaskCard 立即进入 handoff 状态，Indicator 显示 requested<br>5. 已有 active Handoff 时按钮禁用，Tooltip 提示 "已有进行中的 Handoff" |
| **完成标准** | 1. [Handoff] 按钮只在 running/failed 状态显示<br>2. 已有 active Handoff 时按钮禁用并提示<br>3. Agent 下拉列表排除当前 from_agent<br>4. 原因下拉包含全部 7 个枚举值<br>5. 确认后调用 API，成功则关闭 Modal 并更新 TaskCard 状态<br>6. API 返回 409 时显示 "该任务已有进行中的交接"<br>7. 组件测试覆盖 |
| **依赖任务** | HM-T2.1 / HM-T5.1 |
| **推荐顺序** | 13 |

---

### Task 5.3: Handoff Detail Drawer

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T5.3 |
| **story_id** | US-HM-03 / US-HM-05 |
| **任务类型** | frontend |
| **文件** | `src/components/HandoffDetailDrawer.tsx` |
| **任务说明** | 1. 实现 HandoffDetailDrawer（从右侧滑出，300ms 动画）<br>2. 展示 HandoffSummary 全部 9 个字段，数组类型以列表展示<br>3. 展示元数据：from_agent、to_agent、reason、status、时间线（created_at / summary_generated_at / accepted_at / completed_at）<br>4. Result 区域：显示 result_after_handoff（success/partial/failed）和 result_note<br>5. 内容支持复制<br>6. 点击日志中的 Handoff ID 或 TaskCard 上的 Summary Card 可打开 Drawer |
| **完成标准** | 1. Drawer 从右侧滑出，300ms CSS transition<br>2. 9 个 Summary 字段都有对应展示区域，空字段显示 "—"<br>3. 时间线按时间顺序展示，状态变化节点用颜色区分<br>4. Result 区域根据 result_after_handoff 显示绿/黄/红标签<br>5. 点击复制按钮可复制 Summary 内容到剪贴板<br>6. 组件测试覆盖 |
| **依赖任务** | HM-T2.2 / HM-T2.4 / HM-T3.3（Summary 生成完成后才有内容） |
| **推荐顺序** | 15 |

---

### Task 5.4: 接受交接 UI + Worker 切换展示

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T5.4 |
| **story_id** | US-HM-04 |
| **任务类型** | frontend |
| **文件** | `src/components/HandoffAcceptButton.tsx`、`src/components/AgentStationCard.tsx`、`src/components/WorkerBadge.tsx` |
| **任务说明** | 1. HandoffStatusIndicator 在 ready 状态时显示 [接受交接] 按钮<br>2. 点击后调用 POST /handoffs/:handoffId/accept<br>3. 成功后：原 TaskCard 的 Indicator 消失，状态变为 running（由接手 Agent 接管）；原 Agent Station Card 的 WorkerBadge 状态变为 idle/done；接手 Agent Station Card 的 WorkerBadge 显示新模型名，状态变为 running<br>4. WorkerBadge 模型名称切换有 300ms CSS transition<br>5. 自动 accept 场景（系统触发）也同步更新 UI |
| **完成标准** | 1. [接受交接] 按钮只在 ready 状态显示<br>2. 接受后原 TaskCard Indicator 消失，状态变为 running<br>3. 原 Agent Station Card WorkerBadge 状态变为 idle/done<br>4. 接手 Agent Station Card WorkerBadge 显示新模型名，状态 running<br>5. 模型名切换有 300ms transition<br>6. 组件测试覆盖 |
| **依赖任务** | HM-T2.3 / HM-T5.1 |
| **推荐顺序** | 16 |

---

## Feature 6: Handoff 管理页面（P1）

> 对应 Story: US-HM-10
> 说明：P1 功能，独立的 Handoff 历史查看入口。

### Task 6.1: GET /handoffs 列表 API

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T6.1 |
| **story_id** | US-HM-10 |
| **任务类型** | backend |
| **文件** | `src/routes/handoffs.ts` |
| **任务说明** | 1. 实现 GET /handoffs 接口<br>2. 支持查询参数：goal_id、task_id、reason、status、from_agent_id、to_agent_id、page、page_size<br>3. 返回 { items[], total, page, page_size }<br>4. status 筛选支持多选或精确匹配<br>5. 列表按 created_at 倒序排列 |
| **完成标准** | 1. 正常请求返回 200 + 分页结果<br>2. 筛选条件组合使用 AND 逻辑<br>3. 返回字段包含 Handoff ID、Goal、Task、From Agent、To Agent、Reason、Status、Result、Created At<br>4. 分页组件正常工作<br>5. 集成测试覆盖 |
| **依赖任务** | HM-T1.1 / HM-T2.2 |
| **推荐顺序** | 17（P1，延后） |

---

### Task 6.2: Handoff 列表页

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T6.2 |
| **story_id** | US-HM-10 |
| **任务类型** | frontend |
| **文件** | `src/pages/HandoffPage.tsx`、`src/components/HandoffList.tsx` |
| **任务说明** | 1. 实现 HandoffPage 页面，路由 /handoffs<br>2. 展示 Handoff 列表，每行显示：Handoff ID、Goal、Task、From Agent、To Agent、Reason、Status（彩色标签）、Result、Created At<br>3. 支持按 goal_id、task_id、reason、status、from_agent_id、to_agent_id 筛选<br>4. 点击行打开 HandoffDetailDrawer<br>5. 支持分页 |
| **完成标准** | 1. 列表正确展示全部字段<br>2. Status 列使用对应颜色标签（requested=黄、generating_summary=紫、ready=紫、accepted=蓝、completed=绿、failed=红）<br>3. Result 列 success=绿、partial=黄、failed=红<br>4. 分页组件正常工作<br>5. 筛选条件组合使用 AND 逻辑 |
| **依赖任务** | HM-T6.1 / HM-T5.3 |
| **推荐顺序** | 18（P1，延后） |

---

## Feature 7: 测试与质量保障

> 覆盖全部 P0 故事的测试矩阵。

### Task 7.1: 状态机与领域逻辑单元测试

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T7.1 |
| **story_id** | US-HM-02 / US-HM-03 / US-HM-07 |
| **任务类型** | test |
| **文件** | `tests/handoff/status-machine.test.ts`、`tests/handoff/summary-schema.test.ts`、`tests/handoff/context-collector.test.ts` |
| **任务说明** | 1. HandoffStatus 状态机全部合法/非法转换测试<br>2. HandoffSummary JSON Schema 校验测试（完整数据 / 缺字段 / 错误类型）<br>3. 重复 Handoff 检查逻辑测试（无 active / 有 requested / 有 ready / 有 completed）<br>4. 上下文数据收集服务的输入输出测试<br>5. 兜底摘要生成测试 |
| **完成标准** | 1. 状态机测试覆盖全部 6 个状态 × 所有可能事件<br>2. JSON Schema 测试覆盖完整数据、缺字段、错误类型<br>3. 重复 Handoff 测试覆盖 4 种场景<br>4. 单元测试总覆盖率 ≥ 80% |
| **依赖任务** | HM-T1.2 / HM-T1.3 |
| **推荐顺序** | 19（与开发并行） |

---

### Task 7.2: API 集成测试

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T7.2 |
| **story_id** | US-HM-01 / US-HM-02 / US-HM-03 / US-HM-04 / US-HM-05 / US-HM-07 |
| **任务类型** | test |
| **文件** | `tests/handoff.api.test.ts` |
| **任务说明** | 1. POST /tasks/:taskId/handoff — 正常/重复/Task不存在/状态非法<br>2. GET /handoffs/:handoffId — 正常/不存在/摘要未生成<br>3. POST /handoffs/:handoffId/accept — 正常/status非法/Worker创建验证<br>4. PATCH /handoffs/:handoffId/result — 正常/枚举非法/status非法<br>5. GET /handoffs — 正常/筛选/分页（P1） |
| **完成标准** | 1. 全部 5 个 API 的 happy path 和错误 path 都有测试<br>2. 每个 API 至少覆盖 3 个错误场景<br>3. 数据库状态在每次测试后正确清理<br>4. 事务回滚场景有测试 |
| **依赖任务** | HM-T2.1 / HM-T2.2 / HM-T2.3 / HM-T2.4 / HM-T6.1 |
| **推荐顺序** | 20（与开发并行） |

---

### Task 7.3: 前端组件测试

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T7.3 |
| **story_id** | US-HM-01 / US-HM-02 / US-HM-03 / US-HM-04 / US-HM-06 |
| **任务类型** | test |
| **文件** | `tests/components/TaskCard.test.tsx`、`tests/components/HandoffStatusIndicator.test.tsx`、`tests/components/HandoffConfirmModal.test.tsx`、`tests/components/HandoffDetailDrawer.test.tsx` |
| **任务说明** | 1. TaskCard：handoff 状态渲染、动画、按钮显隐<br>2. HandoffStatusIndicator：6 种状态渲染、进度条、自动消失<br>3. HandoffConfirmModal：表单验证、Agent 选择、API 调用、409 处理<br>4. HandoffDetailDrawer：字段展示、时间线、复制功能<br>5. ExecutionLogPanel：Handoff 日志紫色标签、点击交互 |
| **完成标准** | 1. 全部 5 个组件有独立测试文件<br>2. 每个组件覆盖主要渲染状态和用户交互<br>3. 快照测试覆盖关键 UI 状态 |
| **依赖任务** | HM-T5.1 / HM-T5.2 / HM-T5.3 / HM-T5.4 / HM-T4.2 |
| **推荐顺序** | 21（与开发并行） |

---

### Task 7.4: Handoff 端到端工作流测试

| 属性 | 值 |
|------|-----|
| **task_id** | HM-T7.4 |
| **story_id** | US-HM-01 / US-HM-02 / US-HM-03 / US-HM-04 / US-HM-05 / US-HM-06 / US-HM-07 |
| **任务类型** | test |
| **文件** | `tests/e2e/handoff.workflow.spec.ts` |
| **任务说明** | 1. 完整手动 Handoff 工作流：创建 Goal → 启动 Task → 触发 Handoff → Summary 生成 → Accept → 记录 Result<br>2. 验证每一步的 UI 状态变化、API 响应、数据库状态<br>3. 验证重复 Handoff 被阻止<br>4. 验证 ExecutionLog 中可查询到完整 Handoff 事件链<br>5. 验证 Summary 生成失败后进入 failed 状态且有兜底数据 |
| **完成标准** | 1. 1 条完整 happy path E2E 测试通过<br>2. 1 条重复 Handoff 被阻止的 E2E 测试通过<br>3. 1 条 Summary 生成失败后进入 failed 状态的 E2E 测试通过<br>4. 每个 E2E 测试断言 ≥ 10 个检查点 |
| **依赖任务** | 全部 Feature（最后执行） |
| **推荐顺序** | 22 |

---

## 推荐开发顺序

```
Phase 1 — 数据模型 + 核心 API（1 周）
  HM-T1.1   创建 handoff_records 表
  HM-T1.2   定义 HandoffStatus 状态机与校验规则
  HM-T1.3   HandoffSummary 数据结构与兜底生成
  HM-T2.1   POST /tasks/:taskId/handoff（触发+防重复）
  HM-T2.2   GET /handoffs/:handoffId（查询单条+摘要）
  HM-T2.4   PATCH /handoffs/:handoffId/result（记录结果）
  HM-T7.1   状态机与领域逻辑单元测试（与开发并行）

Phase 2 — 日志 + Summary mock + 前端 mock（3-4 天）
  HM-T4.1   Handoff 事件写入 ExecutionLog
  HM-T3.1   Summary Prompt 模板 + 简单 mock 生成
  HM-T5.1   TaskCard Handoff 状态 + HandoffStatusIndicator（mock）
  HM-T5.2   Handoff 触发面板
  HM-T7.3   前端组件测试（与开发并行）

Phase 3 — Summary 完整生成 + Accept 流程（3-4 天）
  HM-T3.2   上下文数据收集服务
  HM-T3.3   集成 Summary 生成到 Handoff 工作流
  HM-T2.3   POST /handoffs/:handoffId/accept（接受+创建Worker）
  HM-T5.3   Handoff Detail Drawer
  HM-T5.4   接受交接 UI + Worker 切换展示
  HM-T4.2   ExecutionLogPanel Handoff 日志渲染
  HM-T7.2   API 集成测试（与开发并行）

Phase 4 — 管理页面（2 天，P1）
  HM-T6.1   GET /handoffs 列表 API
  HM-T6.2   Handoff 列表页

Phase 5 — E2E 验收（1 天）
  HM-T7.4   Handoff 端到端工作流测试
```

---

## 按 Phase 排期的任务看板

### Phase 1 — 数据模型 + 核心 API（1 周）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| HM-T1.1 | handoff_records 表结构 | database | 无 | HM-01~07 |
| HM-T1.2 | HandoffStatus 状态机 + 校验 | backend | HM-T1.1 | HM-02/04/05/07 |
| HM-T1.3 | HandoffSummary 结构 + 兜底 | backend | HM-T1.1 | HM-03 |
| HM-T2.1 | POST /tasks/:taskId/handoff | backend | HM-T1.2 | HM-01/07 |
| HM-T2.2 | GET /handoffs/:handoffId | backend | HM-T1.3 | HM-02/03 |
| HM-T2.4 | PATCH /handoffs/:handoffId/result | backend | HM-T1.2 | HM-05 |
| HM-T7.1 | 单元测试 | test | HM-T1.2/1.3 | HM-02/03/07 |

**Phase 1 交付物：** 用户可通过 HTTP 工具触发 Handoff、查询 Handoff、记录结果。状态机和防重复逻辑完整。

### Phase 2 — 日志 + Summary mock + 前端 mock（3-4 天）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| HM-T4.1 | Handoff 事件写入 ExecutionLog | backend | HM-T1.2/2.1 | HM-06 |
| HM-T3.1 | Summary Prompt + mock 生成 | backend | HM-T1.3 | HM-03 |
| HM-T5.1 | TaskCard 状态 + Indicator（mock） | frontend | 无 | HM-02 |
| HM-T5.2 | Handoff 触发面板 | frontend | HM-T2.1/5.1 | HM-01/07 |
| HM-T7.3 | 前端组件测试 | test | HM-T5.x | HM-01/02/06 |

**Phase 2 交付物：** Workspace 中可看到 Handoff 状态变化、触发 Handoff、查看 mock Summary 和日志。Summary 先用 mock 数据填充，不依赖 LLM。

### Phase 3 — Summary 完整生成 + Accept 流程（3-4 天）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| HM-T3.2 | 上下文数据收集 | backend | HM-T3.1 | HM-03 |
| HM-T3.3 | Summary 生成集成（异步） | backend | HM-T2.1/3.1/3.2 | HM-03 |
| HM-T2.3 | POST /handoffs/:handoffId/accept | backend | HM-T2.1/2.2 | HM-04 |
| HM-T5.3 | Handoff Detail Drawer | frontend | HM-T2.2/2.4/3.3 | HM-03/05 |
| HM-T5.4 | 接受交接 UI + Worker 切换 | frontend | HM-T2.3/5.1 | HM-04 |
| HM-T4.2 | ExecutionLogPanel Handoff 渲染 | frontend | HM-T4.1 | HM-06 |
| HM-T7.2 | API 集成测试 | test | HM-T2/3.x | HM-01~07 |

**Phase 3 交付物：** Summary 自动生成（基于 LLM 或兜底），用户可 Accept Handoff 并由新 Agent 继续执行，WorkerBadge 平滑切换。

### Phase 4 — 管理页面（2 天，P1）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| HM-T6.1 | GET /handoffs 列表 API | backend | HM-T1.1/2.2 | HM-10 |
| HM-T6.2 | Handoff 列表页 | frontend | HM-T6.1/5.3 | HM-10 |

**Phase 4 交付物：** 独立的 Handoff 管理页面，可查看和筛选历史交接记录。

### Phase 5 — E2E 验收（1 天）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| HM-T7.4 | 端到端工作流测试 | test | 全部 | HM-01~07 |

**Phase 5 交付物：** 完整工作流自动化测试通过。

---

## 风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| LLM Summary 生成超时/失败 | Phase 3 延迟 | HM-T1.3 兜底摘要机制保证 UI 永远有内容；HM-T3.1 先用 mock 生成器，LLM 集成可延后 |
| WorkerSession 创建与 Task 状态更新的事务一致性 | 数据不一致 | HM-T2.3 必须使用数据库事务，失败时回滚 |
| 前端状态与后端状态不同步 | 用户看到错误状态 | HM-T5.x 基于轮询实时刷新，不接受本地乐观更新 |
| 上下文过长超过 LLM 窗口 | Summary 质量差 | HM-T3.2 实现截断策略，优先保留最近日志和 task 描述 |
| Accept API 依赖 Worker 模块未就绪 | 无法创建 Worker | HM-T2.3 中 Worker 创建先用最小 stub 实现（仅记录 model_id 和 agent_id），等 Worker 模块就绪后补全完整逻辑 |
| ExecutionLog 模块未就绪 | Handoff 事件无处写入 | HM-T4.1 先实现事件触发逻辑，日志写入用 console.log 或内存数组兜底，等 ExecutionLog 模块就绪后对接真实写入接口 |

---

## Story → Task 映射表

| Story | 涉及 Task | 是否完整覆盖 |
|-------|-----------|--------------|
| US-HM-01 手动触发任务交接 | HM-T1.1 / HM-T1.2 / HM-T2.1 / HM-T5.2 | 是 |
| US-HM-02 查看交接状态流转 | HM-T1.2 / HM-T2.2 / HM-T5.1 | 是 |
| US-HM-03 查看完整交接摘要 | HM-T1.3 / HM-T2.2 / HM-T3.1 / HM-T3.2 / HM-T3.3 / HM-T5.3 | 是 |
| US-HM-04 接手 Agent 接受交接 | HM-T2.3 / HM-T5.4 | 是 |
| US-HM-05 交接完成后记录结果 | HM-T2.4 / HM-T5.3 | 是 |
| US-HM-06 交接事件写入日志 | HM-T4.1 / HM-T4.2 | 是 |
| US-HM-07 防止重复触发交接 | HM-T1.2 / HM-T2.1 / HM-T5.2 | 是 |
| US-HM-10 查看交接记录列表 | HM-T6.1 / HM-T6.2 | 是 |

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
>
> 相关文档：
> - `docs/stories/handoff-manager-stories.md` — 用户故事来源
> - `docs/prd/handoff-manager-prd.md` — 产品需求
> - `docs/architecture/数据结构与数据库Schema.md` — Schema 定义
