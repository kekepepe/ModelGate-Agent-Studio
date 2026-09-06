# Handoff Manager 用户故事

> 所属产品：ModelGate Agent Studio
>
> 来源文档：`docs/prd/handoff-manager-prd.md`
>
> 文档定位：将 Handoff Manager PRD 转化为可开发、可测试的用户故事与验收标准。

---

## 故事清单

| 编号 | 优先级 | 故事摘要 | 涉及页面 | 涉及接口 | 数据对象 |
|------|--------|----------|----------|----------|----------|
| US-HM-01 | P0 | 手动触发任务交接 | Workspace, TaskDetailPanel | `POST /tasks/:taskId/handoff` | HandoffRecord, Task |
| US-HM-02 | P0 | 查看交接状态流转 | Workspace, TaskCard | `GET /handoffs/:handoffId` | HandoffRecord |
| US-HM-03 | P0 | 查看完整交接摘要 | HandoffDetailModal | `GET /handoffs/:handoffId` | HandoffRecord, HandoffSummary |
| US-HM-04 | P0 | 接手 Agent 接受交接 | Workspace | `POST /handoffs/:handoffId/accept` | HandoffRecord, WorkerSession |
| US-HM-05 | P0 | 交接完成后记录结果 | Workspace | `PATCH /handoffs/:handoffId/result` | HandoffRecord |
| US-HM-06 | P0 | 交接事件写入日志 | ExecutionLogPanel | `GET /logs` | ExecutionLog |
| US-HM-07 | P0 | 防止重复触发交接 | Workspace | `POST /tasks/:taskId/handoff` | HandoffRecord |
| US-HM-08 | P1 | 额度不足时提示交接 | Workspace, TopStatusBar | `GET /quota/models/:modelId/status` | QuotaRecord, HandoffRecord |
| US-HM-09 | P1 | 模型错误后建议交接 | Workspace, TaskCard | `POST /tasks/:taskId/handoff` | HandoffRecord |
| US-HM-10 | P1 | 查看交接记录列表 | HandoffPage | `GET /handoffs` | HandoffRecord |
| US-HM-11 | P1 | 标记交接结果为成功/失败 | HandoffDetailModal | `PATCH /handoffs/:handoffId/result` | HandoffRecord |
| US-HM-12 | P1 | 重新生成交接摘要 | HandoffDetailModal | `POST /handoffs/:handoffId/regenerate-summary` | HandoffRecord, HandoffSummary |
| US-HM-13 | P2 | Handoff 前后上下文对比 | HandoffDetailModal | `GET /handoffs/:handoffId` | HandoffRecord, HandoffSummary |
| US-HM-14 | P2 | 筛选和搜索交接记录 | HandoffPage | `GET /handoffs` | HandoffRecord |

---

## P0 用户故事

### US-HM-01：手动触发任务交接

- **Summary:** 用户在 Workspace 中对正在执行或失败的任务触发 Handoff，选择接手 Agent 和交接原因。

#### Use Case:
- **As a** 多模型重度使用的开发者
- **I want to** 在任务执行过程中手动触发 Handoff，选择接手 Agent 并填写交接原因
- **so that** 当当前模型不适合继续时，可以安全地将任务转移给其他 Agent 或模型，而不丢失上下文

#### Acceptance Criteria:

- **Scenario:** 用户从 Workspace 手动触发 Handoff
- **Given:** 我正在 Workspace 中查看一个状态为 `running` 或 `failed` 的 Task
- **and Given:** 该 Task 当前没有被其他进行中的 Handoff（状态不为 requested/generating_summary/ready/accepted）
- **When:** 我点击 TaskCard 上的 [Handoff] 按钮（或在 TaskDetailPanel 中点击 [Generate Handoff]）
- **Then:** 系统弹出 Handoff 确认面板，让我选择接手 Agent（to_agent_id）和交接原因（reason/reason_description）
- **and Then:** 我确认后，后端创建 HandoffRecord，状态为 `requested`，并返回 `handoff_id`
- **and Then:** Workspace 中该 TaskCard 状态变为 `handoff`，边框变为紫色，显示 HandoffStatusIndicator

**涉及页面：** Workspace / AgentStationBoard / TaskCard / TaskDetailPanel
**涉及接口：** `POST /tasks/:taskId/handoff`
**数据对象：** HandoffRecord, Task

**可转测试的验收点：**
1. 前端：只有 `running` 或 `failed` 状态的 TaskCard 才显示 [Handoff] 按钮
2. 前端：点击 [Handoff] 后弹出选择面板，包含 Agent 列表和原因输入框
3. 前端：确认后 TaskCard 边框变紫色，状态标签变为 "handoff"
4. 后端：`POST /tasks/:taskId/handoff` 返回 `{ handoff_id, status: "requested" }`
5. 后端：HandoffRecord 的 `from_agent_id`、`from_model_id`、`task_id`、`goal_id` 正确填充
6. 后端：Task 的 `status` 从 `running` 更新为 `handoff`

---

### US-HM-02：查看交接状态流转

- **Summary:** 用户在 Workspace 中实时看到 Handoff 从 requested → generating_summary → ready → accepted → completed 的完整状态流转。

#### Use Case:
- **As a** 需要长时间推进复杂任务的开发者
- **I want to** 在 Workspace 中实时看到 Handoff 的当前状态和进度
- **so that** 我知道交接进行到哪一步，是否需要等待或介入

#### Acceptance Criteria:

- **Scenario:** Handoff 状态在 Workspace 中实时更新
- **Given:** 存在一个状态为 `requested` 的 HandoffRecord
- **When:** Handoff 状态从 `requested` 变为 `generating_summary`，再变为 `ready`，然后被接受变为 `accepted`，最后完成变为 `completed`
- **Then:** Workspace 中的 HandoffStatusIndicator 同步更新对应的状态标签、图标和颜色
- **and Then:** 每个状态变化在 ExecutionLogPanel 中生成一条对应日志

**涉及页面：** Workspace / AgentStationBoard / TaskCard / HandoffStatusIndicator / ExecutionLogPanel
**涉及接口：** `GET /handoffs/:handoffId`（轮询或 SSE）
**数据对象：** HandoffRecord

**可转测试的验收点：**
1. 前端：HandoffStatusIndicator 显示当前状态文本（如 "Generating Summary..."）
2. 前端：`requested` 状态显示黄色图标，`generating_summary` 显示紫色脉冲图标，`ready` 显示紫色静态图标，`accepted` 显示蓝色图标，`completed` 显示绿色图标
3. 前端：状态变化时有 300ms 过渡动画
4. 后端：HandoffRecord 的 `status` 字段每次变化后持久化
5. 后端：状态变化触发 `handoff_status_updated` 事件（SSE 或轮询可感知）
6. 后端：`accepted_at`、`completed_at` 等时间戳在对应状态时被正确记录

---

### US-HM-03：查看完整交接摘要

- **Summary:** 用户点击 Handoff Summary Card 后，可以查看包含 original_goal、current_task、completed_work、unfinished_work、constraints、decisions、risks、next_steps 的完整结构化摘要。

#### Use Case:
- **As a** 需要排查任务中断原因的开发者
- **I want to** 查看 Handoff 生成的完整交接摘要
- **so that** 我可以验证接手 Agent 是否获得了足够的上下文来继续执行任务

#### Acceptance Criteria:

- **Scenario:** 用户查看 Handoff Summary 详情
- **Given:** 存在一个状态为 `ready`、`accepted` 或 `completed` 的 HandoffRecord
- **When:** 我点击 Workspace 中的 Handoff Summary Card 或 HandoffStatusIndicator
- **Then:** 系统打开 Handoff Detail Modal/Drawer，展示完整的 HandoffSummary 字段
- **and Then:** 摘要包含：original_goal、current_task、completed_work[]、unfinished_work[]、important_constraints[]、key_decisions[]、errors_and_risks[]、next_suggested_steps[]、context_needed[]

**涉及页面：** Workspace / HandoffDetailModal / HandoffDetailDrawer
**涉及接口：** `GET /handoffs/:handoffId`
**数据对象：** HandoffRecord, HandoffSummary

**可转测试的验收点：**
1. 前端：Handoff Detail Modal 中所有 9 个 Summary 字段都有对应的展示区域
2. 前端：数组类型字段（completed_work[] 等）以列表形式展示
3. 前端：摘要内容支持复制
4. 后端：`GET /handoffs/:handoffId` 返回的 JSON 中包含完整的 `handoff_summary` 对象
5. 后端：每个字段类型正确（string 或 string[]）
6. 后端：如果 summary 生成失败，`handoff_summary` 包含兜底简版数据或错误说明

---

### US-HM-04：接手 Agent 接受交接

- **Summary:** 系统或用户确认接手 Agent 后，HandoffRecord 状态变为 accepted，创建新的 WorkerSession，新 Worker 加载 Handoff Summary 继续执行 Task。

#### Use Case:
- **As a** 多模型协作平台用户
- **I want to** 在 Handoff Summary 生成后，让接手 Agent 接受交接并继续执行任务
- **so that** 任务可以在不中断的情况下由新的 Agent/模型继续执行

#### Acceptance Criteria:

- **Scenario:** 接手 Agent 接受 Handoff 并继续执行
- **Given:** 存在一个状态为 `ready` 的 HandoffRecord
- **When:** 系统或用户触发接受交接（调用 accept 接口）
- **Then:** HandoffRecord 状态更新为 `accepted`，并记录 `accepted_at` 时间戳
- **and Then:** 系统为接手 Agent 创建新的 WorkerSession，`inherited_from_handoff_id` 指向该 HandoffRecord
- **and Then:** 新 WorkerSession 的 `agent_id` = `to_agent_id`，`model_id` = `to_model_id`
- **and Then:** Task 状态从 `handoff` 更新为 `running`
- **and Then:** Workspace 中原 Agent Card 状态释放（变 idle/done），接手 Agent Card 进入 running

**涉及页面：** Workspace / AgentStationBoard / WorkerBadge / TaskCard
**涉及接口：** `POST /handoffs/:handoffId/accept`
**数据对象：** HandoffRecord, WorkerSession, Task

**可转测试的验收点：**
1. 前端：Handoff 完成后，原 TaskCard 的 HandoffStatusIndicator 消失，状态变为 `running`（由接手 Agent 接管）
2. 前端：原 Agent Station Card 的 WorkerBadge 状态变为 idle/done
3. 前端：接手 Agent Station Card 的 WorkerBadge 显示新模型名，状态变为 running
4. 后端：`POST /handoffs/:handoffId/accept` 返回 `{ worker_id, status: "accepted" }`
5. 后端：新 WorkerSession 的 `inherited_from_handoff_id` = `handoff_id`
6. 后端：Task 的 `assigned_agent_id` 和 `assigned_worker_id` 更新为接手 Agent 和 Worker
7. 后端：原 WorkerSession 的 `status` 更新为 `handoff_required` 或 `completed`

---

### US-HM-05：交接完成后记录结果

- **Summary:** Handoff 完成后，系统记录交接结果（success / partial / failed），更新 HandoffRecord 状态为 completed。

#### Use Case:
- **As a** 需要复盘任务执行过程的开发者
- **I want to** 在 Handoff 完成后看到交接是否成功
- **so that** 我可以评估 Handoff 的效果，决定是否需要再次交接或调整策略

#### Acceptance Criteria:

- **Scenario:** 记录 Handoff 执行结果
- **Given:** 存在一个状态为 `accepted` 的 HandoffRecord
- **and Given:** 接手 Worker 已完成或失败该 Task
- **When:** 系统根据接手 Worker 的执行结果更新 HandoffRecord
- **Then:** HandoffRecord 状态更新为 `completed`
- **and Then:** `result_after_handoff` 字段被设置为 `success`、`partial` 或 `failed`
- **and Then:** `completed_at` 时间戳被记录
- **and Then:** Workspace 中 HandoffStatusIndicator 显示最终状态（绿色 success / 黄色 partial / 红色 failed）

**涉及页面：** Workspace / HandoffDetailModal / ExecutionLogPanel
**涉及接口：** `PATCH /handoffs/:handoffId/result`
**数据对象：** HandoffRecord

**可转测试的验收点：**
1. 前端：Handoff 完成后，TaskCard 显示交接结果标记（如 "Handoff: ✓ Success"）
2. 前端：Handoff Detail Modal 的 Result 区域显示 `result_after_handoff` 和 `completed_at`
3. 后端：`PATCH /handoffs/:handoffId/result` 接收 `{ result_after_handoff, status }` 并持久化
4. 后端：`result_after_handoff` 枚举值只能是 `success`、`partial`、`failed`
5. 后端：只有状态为 `accepted` 的 HandoffRecord 才能被标记为 `completed`

---

### US-HM-06：交接事件写入日志

- **Summary:** Handoff 全过程的关键事件（requested / generating_summary / ready / accepted / completed / failed）都被写入 ExecutionLog，可在 Bottom Console 中查看。

#### Use Case:
- **As a** 需要排查任务中断原因的开发者
- **I want to** 在日志中看到 Handoff 的全过程记录
- **so that** 当任务执行异常时，我可以追溯 Handoff 发生的时机、原因和结果

#### Acceptance Criteria:

- **Scenario:** Handoff 事件在日志中完整记录
- **Given:** 一个 Handoff 从创建到完成的全过程
- **When:** Handoff 状态每次变化时
- **Then:** 系统写入一条 ExecutionLog，level 为 `handoff` 或 `error`
- **and Then:** 日志包含 `handoff_id`、`task_id`、`goal_id`、`agent_id`、`action`（如 handoff_requested / handoff_summary_ready / handoff_completed）
- **and Then:** ExecutionLogPanel 以紫色标签展示 Handoff 事件，Error Logs 中以红色展示 handoff_failed

**涉及页面：** ExecutionLogPanel / BottomConsole
**涉及接口：** `GET /logs`（内部写入）
**数据对象：** ExecutionLog, HandoffRecord

**可转测试的验收点：**
1. 前端：ExecutionLogPanel 的 Event Log Tab 中，Handoff 事件显示紫色标签
2. 前端：点击 Handoff 日志可跳转对应 Handoff Detail
3. 后端：Handoff 每个状态变化都触发一条 ExecutionLog 写入
4. 后端：ExecutionLog 的 `action` 字段取值：`handoff_requested`、`handoff_summary_generating`、`handoff_summary_ready`、`handoff_accepted`、`handoff_completed`、`handoff_failed`
5. 后端：可以通过 `GET /logs?handoff_id=xxx` 查询到该 Handoff 的全部关联日志

---

### US-HM-07：防止重复触发交接

- **Summary:** 同一 Task 在已有进行中的 Handoff（requested / generating_summary / ready / accepted）时，禁止再次触发新的 Handoff。

#### Use Case:
- **As a** 使用多 Agent 协作平台的开发者
- **I want to** 系统阻止我在已有交接进行时重复触发 Handoff
- **so that** 避免产生冲突的 HandoffRecord，导致任务状态混乱

#### Acceptance Criteria:

- **Scenario:** 阻止重复 Handoff 触发
- **Given:** Task A 已经存在一个状态为 `requested`、`generating_summary`、`ready` 或 `accepted` 的 HandoffRecord
- **When:** 我尝试对该 Task 再次触发 Handoff
- **Then:** 前端 [Handoff] 按钮被禁用或点击后提示 "已有进行中的 Handoff"
- **and Then:** 后端 `POST /tasks/:taskId/handoff` 返回 409 Conflict，错误信息为 "Task already has an active handoff"
- **and Then:** 不会创建新的 HandoffRecord

**涉及页面：** Workspace / TaskCard / TaskDetailPanel
**涉及接口：** `POST /tasks/:taskId/handoff`
**数据对象：** HandoffRecord, Task

**可转测试的验收点：**
1. 前端：Task 存在 active Handoff 时，[Handoff] 按钮禁用或显示提示 Tooltip
2. 前端：用户点击禁用的 [Handoff] 按钮时，弹出提示 "已有进行中的 Handoff，请先取消或完成"
3. 后端：`POST /tasks/:taskId/handoff` 在 Task 已有 active Handoff 时返回 HTTP 409
4. 后端：返回的错误 JSON 包含 `error.code = "CONFLICT"` 和明确的错误消息
5. 后端：数据库中该 Task 的 active Handoff 数量始终 ≤ 1

---

## P1 用户故事

### US-HM-08：额度不足时提示交接

- **Summary:** 当 Quota Manager 检测到当前模型额度达到 warning 或 limited 时，Workspace 自动提示用户生成 Handoff，并推荐备用模型。

#### Use Case:
- **As a** 拥有多个 AI Coding Plan 的开发者
- **I want to** 在模型额度接近上限时收到系统提示，建议切换模型
- **so that** 我可以主动触发 Handoff，避免任务因额度耗尽而突然中断

#### Acceptance Criteria:

- **Scenario:** 额度不足时系统提示 Handoff
- **Given:** 一个 Task 正在由模型 M 执行
- **and Given:** Quota Manager 检测到模型 M 的 `quota_status` 变为 `warning` 或 `near_limit`
- **When:** 状态变化事件推送到 Workspace
- **Then:** Workspace 顶部显示 Quota 预警条："⚠️ 模型 M 额度预警（78%），建议 Handoff"
- **and Then:** TaskCard 上的 RiskBadge 从绿色变为黄色或橙色
- **and Then:** 预警条提供 [Generate Handoff] 和 [Continue Anyway] 两个按钮
- **and Then:** 点击 [Generate Handoff] 自动打开 Handoff 面板，to_agent 和 to_model 由 Model Router 推荐

**涉及页面：** Workspace / TopStatusBar / TaskCard / RiskBadge
**涉及接口：** `GET /quota/models/:modelId/status`（推送）, `POST /tasks/:taskId/handoff`
**数据对象：** QuotaRecord, HandoffRecord, RoutingResult

**可转测试的验收点：**
1. 前端：Quota 预警条在 `quota_status` 变为 `warning`/`near_limit` 时自动弹出
2. 前端：预警条显示模型名、当前使用率百分比和建议操作按钮
3. 前端：点击 [Generate Handoff] 后，Handoff 面板的 to_model 已预填 Model Router 推荐的备用模型
4. 后端：Quota Manager 状态变化触发 `quota.status_changed` 事件
5. 后端：Handoff Manager 监听该事件，在 `LIMITED` 时自动触发 auto_handoff（MVP-B 可选）

---

### US-HM-09：模型错误后建议交接

- **Summary:** 当 Task 因模型调用失败（429/500/timeout）进入 failed 状态时，Workspace 在 TaskCard 和 Error Banner 上提供 Retry 和 Generate Handoff 两个选项。

#### Use Case:
- **As a** 需要长时间推进复杂任务的开发者
- **I want to** 在模型调用失败后，除了重试还能选择 Handoff 到其他模型
- **so that** 当某个模型持续失败时，我可以快速切换到更稳定的模型继续任务

#### Acceptance Criteria:

- **Scenario:** 模型错误后提供 Handoff 选项
- **Given:** 一个 Task 因模型调用失败（如 429 rate limit）进入 `failed` 状态
- **When:** 错误事件推送到 Workspace
- **Then:** TaskCard 变红并显示错误信息
- **and Then:** Error Banner 弹出，显示错误详情和两个按钮：[Retry] 和 [Handoff to Backup Model]
- **and Then:** 点击 [Handoff to Backup Model] 自动打开 Handoff 面板，原因预填 `error`，to_model 预填备用模型
- **and Then:** Handoff Summary 自动包含错误原因和已尝试方案

**涉及页面：** Workspace / TaskCard / ErrorBanner / TaskDetailPanel
**涉及接口：** `POST /tasks/:taskId/handoff`
**数据对象：** HandoffRecord, ExecutionLog

**可转测试的验收点：**
1. 前端：Task failed 时 TaskCard 边框变红，显示错误类型（如 "429 rate limit"）
2. 前端：Error Banner 同时展示 [Retry] 和 [Handoff to Backup Model] 按钮
3. 前端：点击 [Handoff to Backup Model] 后，交接原因下拉框自动选中 `error`
4. 后端：错误触发的 Handoff，其 `handoff_summary.errors_and_risks` 包含原始错误信息
5. 后端：`handoff_summary.next_suggested_steps` 包含避免相同错误的建议

---

### US-HM-10：查看交接记录列表

- **Summary:** 用户在独立的 Handoff 页面中查看所有交接记录，支持按 Goal、Task、Reason、Status、Agent 筛选。

#### Use Case:
- **As a** 需要复盘多模型协作效果的开发者
- **I want to** 查看所有历史 Handoff 记录的列表
- **so that** 我可以分析哪些模型/Agent 之间经常交接、交接原因分布、交接成功率

#### Acceptance Criteria:

- **Scenario:** 查看和筛选 Handoff 列表
- **Given:** 系统中存在多条 HandoffRecord
- **When:** 我进入 Handoff 页面
- **Then:** 页面展示 Handoff 列表，每行包含：Handoff ID、Goal、Task、From Agent、To Agent、Reason、Status、Result、Created At
- **and Then:** 我可以通过筛选条件过滤列表：goal_id、task_id、reason、status、from_agent_id、to_agent_id
- **and Then:** 点击任意行可查看 Handoff Detail

**涉及页面：** HandoffPage
**涉及接口：** `GET /handoffs`
**数据对象：** HandoffRecord

**可转测试的验收点：**
1. 前端：Handoff 列表页正确展示所有字段，状态列使用对应颜色标签
2. 前端：筛选器支持多条件组合筛选
3. 前端：列表支持分页（page / page_size）
4. 后端：`GET /handoffs` 支持查询参数：goal_id、task_id、reason、status、from_agent_id、to_agent_id、page、page_size
5. 后端：返回结果包含 `items[]`、`total`、`page`、`page_size`
6. 后端：status 筛选支持多选或精确匹配

---

### US-HM-11：标记交接结果为成功/失败

- **Summary:** 用户在 Handoff Detail 中手动标记交接结果为 success、partial 或 failed，并添加备注。

#### Use Case:
- **As a** 需要评估 Handoff 效果的开发者
- **I want to** 在 Handoff 完成后手动标记交接结果
- **so that** 我可以记录接手 Agent 是否成功完成了任务，为后续模型选择提供数据

#### Acceptance Criteria:

- **Scenario:** 手动标记 Handoff 结果
- **Given:** 我正在查看一个状态为 `completed` 的 Handoff Detail
- **When:** 我在 Result 区域选择 `success` / `partial` / `failed`，填写备注，点击保存
- **Then:** 系统调用 `PATCH /handoffs/:handoffId/result` 更新记录
- **and Then:** Handoff Detail 中显示更新后的 result 和备注
- **and Then:** Handoff 列表中该行的 Result 列同步更新

**涉及页面：** HandoffDetailModal / HandoffPage
**涉及接口：** `PATCH /handoffs/:handoffId/result`
**数据对象：** HandoffRecord

**可转测试的验收点：**
1. 前端：Handoff Detail 的 Result 区域提供下拉选择框（success / partial / failed）和文本备注框
2. 前端：保存后显示成功提示，Result 标签颜色变化（绿/黄/红）
3. 后端：`PATCH /handoffs/:handoffId/result` 接收 `{ result_after_handoff, result_note }`
4. 后端：`result_after_handoff` 枚举校验，非法值返回 400
5. 后端：更新后返回完整 HandoffRecord

---

### US-HM-12：重新生成交接摘要

- **Summary:** 当用户发现 Handoff Summary 内容不完整时，可以触发重新生成，附加补充上下文。

#### Use Case:
- **As a** 对交接质量有要求的开发者
- **I want to** 在发现交接摘要缺失关键信息时重新生成
- **so that** 接手 Agent 可以获得更完整的上下文，减少信息丢失

#### Acceptance Criteria:

- **Scenario:** 重新生成 Handoff Summary
- **Given:** 我正在查看一个状态为 `ready` 或 `completed` 的 Handoff Detail
- **and Given:** 我发现 Summary 中某些字段为空或不完整
- **When:** 我点击 [Regenerate Summary] 按钮，填写补充上下文，确认
- **Then:** 系统调用 `POST /handoffs/:handoffId/regenerate-summary`
- **and Then:** HandoffRecord 状态变为 `generating_summary`
- **and Then:** 生成完成后状态回到 `ready`，Summary 内容更新
- **and Then:** Workspace 中 HandoffStatusIndicator 同步显示生成中状态

**涉及页面：** HandoffDetailModal / Workspace
**涉及接口：** `POST /handoffs/:handoffId/regenerate-summary`
**数据对象：** HandoffRecord, HandoffSummary

**可转测试的验收点：**
1. 前端：Handoff Detail 中 [Regenerate Summary] 按钮仅在 `ready` 或 `completed` 状态可见
2. 前端：点击后弹出输入框，允许用户填写 `additional_context`
3. 前端：重新生成过程中显示 loading 状态
4. 后端：`POST /handoffs/:handoffId/regenerate-summary` 接收 `{ reason, additional_context }`
5. 后端：状态变为 `generating_summary`，生成完成后回到 `ready`
6. 后端：新的 Summary 合并原有内容和补充上下文

---

## P2 用户故事

### US-HM-13：Handoff 前后上下文对比

- **Summary:** 用户在 Handoff Detail 中查看交接前后的上下文对比，评估信息传递完整度。

#### Use Case:
- **As a** 关注任务连续性的开发者
- **I want to** 对比 Handoff 前后 Agent 接收到的上下文差异
- **so that** 我可以评估交接是否丢失了关键信息，并决定是否需要补充

#### Acceptance Criteria:

- **Scenario:** 查看 Handoff 前后上下文对比
- **Given:** 我正在查看一个状态为 `completed` 的 Handoff Detail
- **When:** 我点击 [View Compare] 或切换到 Compare Tab
- **Then:** 页面展示左右对比视图：左侧为 Handoff 前原 Agent 的上下文（completed_work、unfinished_work、constraints），右侧为 Handoff 后接手 Agent 接收到的上下文
- **and Then:** 系统高亮显示差异部分（如丢失的约束、被截断的上下文）
- **and Then:** 显示上下文损失估算：`tokens_before_handoff` vs `tokens_after_handoff`

**涉及页面：** HandoffDetailModal
**涉及接口：** `GET /handoffs/:handoffId`（扩展返回上下文快照）
**数据对象：** HandoffRecord, ContextSnapshot

**可转测试的验收点：**
1. 前端：对比视图采用左右分栏布局，差异部分用颜色高亮
2. 前端：显示 token 损失数量和百分比
3. 后端：`GET /handoffs/:handoffId` 返回中包含 `tokens_before_handoff` 和 `tokens_after_handoff`
4. 后端：差异计算基于 HandoffSummary 的字段对比

---

### US-HM-14：筛选和搜索交接记录

- **Summary:** 用户在 Handoff 页面中通过关键词搜索交接记录，或按时间段、成功率筛选。

#### Use Case:
- **As a** 需要分析多模型协作效率的开发者
- **I want to** 通过关键词或高级条件搜索历史交接记录
- **so that** 我可以快速找到特定类型的交接事件进行分析

#### Acceptance Criteria:

- **Scenario:** 高级筛选 Handoff 记录
- **Given:** Handoff 列表页已加载
- **When:** 我在搜索框输入关键词（如模型名、Agent 名），或选择高级筛选条件（时间段、result_after_handoff）
- **Then:** 列表实时过滤，只显示匹配的记录
- **and Then:** 筛选条件可以组合使用（如：reason=quota_exceeded + result_after_handoff=success）
- **and Then:** 清空筛选后恢复完整列表

**涉及页面：** HandoffPage
**涉及接口：** `GET /handoffs`
**数据对象：** HandoffRecord

**可转测试的验收点：**
1. 前端：搜索框支持关键词搜索（匹配 Handoff ID、Agent 名、模型名、Task 名）
2. 前端：高级筛选面板支持时间段选择器和 result 多选
3. 后端：`GET /handoffs` 支持 `search`、`start_time`、`end_time`、`result_after_handoff` 参数
4. 后端：组合筛选使用 AND 逻辑
5. 后端：`search` 参数支持模糊匹配

---

## 附录：数据对象速查

### HandoffRecord

```typescript
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
  reason: 'quota_exceeded' | 'error' | 'quality_issue' | 'role_mismatch' | 'manual' | 'context_limit' | 'other';
  reason_description?: string;
  handoff_summary: HandoffSummary;
  status: 'requested' | 'generating_summary' | 'ready' | 'accepted' | 'completed' | 'failed';
  result_after_handoff?: 'success' | 'failed' | 'partial';
  result_note?: string;
  tokens_before_handoff: number;
  tokens_after_handoff: number;
  created_at: Date;
  summary_generated_at?: Date;
  accepted_at?: Date;
  completed_at?: Date;
  updated_at: Date;
}
```

### HandoffSummary

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

### WorkerSession（扩展字段）

```typescript
interface WorkerSession {
  id: string;
  agent_id: string;
  model_id: string;
  goal_id: string;
  task_id: string;
  inherited_from_handoff_id?: string;  // 关联 HandoffRecord
  status: 'idle' | 'running' | 'handoff_required' | 'completed' | 'failed';
  // ...
}
```

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
>
> 相关文档：
> - `docs/prd/handoff-manager-prd.md` — 完整产品需求
> - `docs/prd/agent-workspace-prd.md` — Workspace 中的 Handoff 表达
> - `docs/prd/logs-observability-prd.md` — Handoff 日志事件
