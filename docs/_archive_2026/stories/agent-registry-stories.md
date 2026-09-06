# Agent Registry 用户故事

> 所属产品：ModelGate Agent Studio
>
> 来源文档：`docs/prd/agent-registry-prd.md`
>
> 文档定位：将 Agent Registry PRD 转化为可开发、可测试的用户故事与验收标准。

---

## 故事清单

| 编号 | 优先级 | 故事摘要 | 涉及页面 | 涉及接口 | 数据对象 |
|------|--------|----------|----------|----------|----------|
| US-AR-01 | P0 | 查看 Agent Station 列表 | AgentRegistryPage | `GET /agents` | AgentStation |
| US-AR-02 | P0 | 创建自定义 Agent Station | AgentRegistryPage | `POST /agents` | AgentStation |
| US-AR-03 | P0 | 编辑 Agent Station 配置 | AgentRegistryPage | `PATCH /agents/:id` | AgentStation |
| US-AR-04 | P0 | 启用/禁用 Agent Station | AgentRegistryPage | `PATCH /agents/:id/status` | AgentStation |
| US-AR-05 | P0 | 使用默认模板创建 Agent | AgentRegistryPage | `GET /agents/templates`, `POST /agents` | AgentStation |
| US-AR-06 | P1 | 查看 Agent 使用统计 | AgentRegistryPage | `GET /agents/:id/stats` | AgentStation, WorkerSession |

---

## P0 用户故事

### US-AR-01：查看 Agent Station 列表

- **Summary:** 用户在 Agent Registry 页面看到所有 Agent Station 的列表，包含角色、状态、默认模型等信息。

#### Use Case:
- **As a** 多模型协作平台用户
- **I want to** 查看系统中所有已配置的 Agent Station 列表
- **so that** 我了解有哪些 Agent 角色可用、各自的状态和绑定的模型

#### Acceptance Criteria:

- **Scenario:** 查看 Agent Station 列表
- **Given:** 系统中已存在若干 Agent Station（默认模板 + 用户自定义）
- **When:** 我进入 Agent Registry 页面
- **Then:** 页面展示 Agent 列表，每行包含：名称、角色、状态、默认模型、是否允许 Handoff
- **and Then:** 列表支持按角色、状态筛选，支持按名称搜索
- **and Then:** 点击 Agent 行可进入编辑页面

**涉及页面：** AgentRegistryPage / AgentList
**涉及接口：** `GET /agents`
**数据对象：** AgentStation

**可转测试的验收点：**
1. 前端：列表正确展示所有 Agent 的名称、角色标签（Planner/Coder/Reviewer 等）、状态指示灯
2. 前端：状态筛选器支持选择 idle/running/error 等状态
3. 前端：搜索框支持按 Agent 名称实时过滤
4. 后端：`GET /agents` 返回 `agents[]`，包含 `id`、`name`、`role`、`status`、`default_model_id`
5. 后端：返回的 Agent 按 `role` 分组排序

---

### US-AR-02：创建自定义 Agent Station

- **Summary:** 用户在 Agent Registry 中创建新的 Agent Station，配置角色、名称、系统提示词、默认模型等参数。

#### Use Case:
- **As a** 需要自定义 Agent 角色的开发者
- **I want to** 创建一个新的 Agent Station 并配置其参数
- **so that** 我可以根据特定任务需求定制 Agent 的行为和能力

#### Acceptance Criteria:

- **Scenario:** 创建自定义 Agent
- **Given:** 我正在 Agent Registry 页面
- **When:** 我点击 [创建 Agent] 按钮，填写表单并确认
- **Then:** 系统创建新的 AgentStation，返回 `agent_id`
- **and Then：** 表单字段至少包含：名称、角色（下拉选择）、系统提示词（文本域）、默认模型（下拉选择）、是否允许 Handoff（Switch）
- **and Then：** 创建成功后 Agent 列表自动刷新，新 Agent 显示在列表中

**涉及页面：** AgentRegistryPage / AgentConfigForm
**涉及接口：** `POST /agents`
**数据对象：** AgentStation

**可转测试的验收点：**
1. 前端：[创建 Agent] 按钮在列表页顶部可见
2. 前端：表单中角色下拉包含 6 个选项：planner、coder、reviewer、research、summarizer、supervisor
3. 前端：名称为空时提交按钮禁用
4. 后端：`POST /agents` 接收 `{ name, role, system_prompt, default_model_id, allow_handoff }`
5. 后端：必填字段缺失时返回 400 和明确错误信息
6. 后端：创建成功后返回 `{ agent_id, status: "idle" }`
7. 后端：新 Agent 的 `total_tasks_completed` = 0

---

### US-AR-03：编辑 Agent Station 配置

- **Summary:** 用户修改已有 Agent Station 的配置（名称、提示词、模型绑定、Handoff 开关等）。

#### Use Case:
- **As a** 需要调整 Agent 行为的开发者
- **I want to** 编辑已有 Agent Station 的配置
- **so that** 我可以根据实际使用效果优化 Agent 的提示词或切换默认模型

#### Acceptance Criteria:

- **Scenario:** 编辑 Agent 配置
- **Given:** 我正在 Agent Registry 列表页
- **When:** 我点击某个 Agent 的 [编辑] 按钮，修改配置并保存
- **Then:** 系统更新 AgentStation 的配置
- **and Then：** 可编辑字段：名称、系统提示词、默认模型、备用模型列表、最大 Step 数、是否允许 Handoff、交接阈值 token 数
- **and Then：** 如果 Agent 当前正在运行任务（status = running），修改提示词时显示警告提示

**涉及页面：** AgentRegistryPage / AgentConfigForm
**涉及接口：** `PATCH /agents/:id`
**数据对象：** AgentStation

**可转测试的验收点：**
1. 前端：点击 [编辑] 后弹出表单，字段预填当前值
2. 前端：running 状态的 Agent 编辑时显示警告横幅
3. 前端：保存成功后显示 toast 提示，列表数据刷新
4. 后端：`PATCH /agents/:id` 支持部分更新（只传修改的字段）
5. 后端：`default_model_id` 变更时校验模型是否存在且启用
6. 后端：`max_steps_per_task` 变更时校验为大于 0 的整数

---

### US-AR-04：启用/禁用 Agent Station

- **Summary:** 用户可以启用或禁用某个 Agent Station，禁用的 Agent 不再接收新任务分配。

#### Use Case:
- **As a** 需要临时停用某个 Agent 的开发者
- **I want to** 禁用某个 Agent Station
- **so that** 系统不再将任务分配给该 Agent，例如当该 Agent 的模型额度不足时

#### Acceptance Criteria:

- **Scenario:** 启用/禁用 Agent
- **Given:** 我正在 Agent Registry 列表页，某个 Agent 当前状态为 `enabled`
- **When:** 我点击该 Agent 的启用/禁用开关
- **Then：** Agent 状态切换为 `disabled`，不再接收新任务分配
- **and Then：** 如果该 Agent 当前有正在执行的任务，显示警告："该 Agent 有正在执行的任务，禁用后将不再接收新任务"
- **and Then：** 已禁用的 Agent 在 Workspace 中显示为灰色，WorkerBadge 不可交互

**涉及页面：** AgentRegistryPage / AgentList
**涉及接口：** `PATCH /agents/:id/status`
**数据对象：** AgentStation

**可转测试的验收点：**
1. 前端：列表中每个 Agent 行有启用/禁用 Switch
2. 前端：Switch 切换时显示确认弹窗（如果 Agent 有 running 任务）
3. 前端：禁用后 Agent 行变灰，状态标签显示 "disabled"
4. 后端：`PATCH /agents/:id/status` 接收 `{ status: "enabled" | "disabled" }`
5. 后端：禁用后 Model Router 不再将该 Agent 作为候选
6. 后端：禁用的 Agent 的 `current_task_id` 完成后不再接收新任务

---

### US-AR-05：使用默认模板创建 Agent

- **Summary:** 用户可以从 6 个默认角色模板快速创建 Agent Station，无需从零配置。

#### Use Case:
- **As a** 刚接触平台的新用户
- **I want to** 使用系统预设的 Agent 模板快速创建常用角色
- **so that** 我不需要从零编写系统提示词，可以快速启动多 Agent 协作

#### Acceptance Criteria:

- **Scenario:** 从模板创建 Agent
- **Given:** 我正在 Agent Registry 页面
- **When:** 我点击 [从模板创建]，选择 Planner/Coder/Reviewer/Research/Summarizer/Supervisor 之一
- **Then：** 系统使用对应模板的默认配置创建 AgentStation
- **and Then：** 模板预填字段：系统提示词、默认模型建议、允许的工具列表、输出格式、最大 Step 数
- **and Then：** 创建后我可以进一步编辑模板生成的配置

**涉及页面：** AgentRegistryPage / AgentList
**涉及接口：** `GET /agents/templates`, `POST /agents`
**数据对象：** AgentStation

**可转测试的验收点：**
1. 前端：[从模板创建] 按钮展示 6 个角色卡片
2. 前端：点击模板后表单自动预填对应角色的默认配置
3. 后端：`GET /agents/templates` 返回 6 个模板，每个包含 `role`、`system_prompt`、`default_model_id`、`allowed_tools`
4. 后端：Coder 模板的 `system_prompt` 包含代码生成相关指令
5. 后端：Reviewer 模板的 `system_prompt` 包含代码审查相关指令

---

## P1 用户故事

### US-AR-06：查看 Agent 使用统计

- **Summary:** 用户在 Agent Registry 中查看每个 Agent Station 的历史使用统计（完成任务数、Token 消耗、平均耗时等）。

#### Use Case:
- **As a** 需要评估 Agent 效率的开发者
- **I want to** 查看每个 Agent Station 的使用统计
- **so that** 我可以判断哪些 Agent 配置效果好，哪些需要优化

#### Acceptance Criteria:

- **Scenario:** 查看 Agent 统计
- **Given:** 我正在 Agent Registry 列表页
- **When：** 我点击某个 Agent 的 [查看统计] 按钮
- **Then：** 弹出统计面板，显示：历史完成任务数、失败任务数、平均 Token 消耗、平均执行时长、最近 Handoff 次数

**涉及页面：** AgentRegistryPage / AgentStatsPanel
**涉及接口：** `GET /agents/:id/stats`
**数据对象：** AgentStation, WorkerSession, ExecutionLog

**可转测试的验收点：**
1. 前端：统计面板以卡片形式展示关键指标
2. 后端：`GET /agents/:id/stats` 返回 `{ total_completed, total_failed, avg_tokens, avg_duration_ms, recent_handoffs }`

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
