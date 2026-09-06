# Agent Registry 开发任务拆解

> 基于 `docs/stories/agent-registry-stories.md` 的 5 条 P0 + 1 条 P1 用户故事拆解
>
> 拆分模式：Operations (Pattern 2 — CRUD) + Simple/Complex (Pattern 7)
> ——先打通数据模型 + 完整 CRUD API，再叠加模板能力和前端页面。

---

## Epic: Agent Registry

**目标：** 让用户可以查看、创建、编辑、启禁用 Agent Station，并通过模板快速初始化常用角色。

**Epic 验收标准：**
1. 用户可在 Agent Registry 页面查看所有 Agent Station 列表（名称、角色、状态、默认模型）
2. 用户可创建自定义 Agent Station，填写名称、角色、系统提示词、默认模型
3. 用户可编辑已有 Agent Station 的配置
4. 用户可通过开关启用/禁用 Agent Station
5. 用户可从 6 个预设模板快速创建 Agent
6. 禁用的 Agent 不再被 Model Router 选为任务候选

---

## Feature 1: Agent Station 数据模型与状态定义

> 对应 Story: US-AR-01 / US-AR-02 / US-AR-03 / US-AR-04 / US-AR-05
> 说明：所有 Story 共享同一张表和同一套状态枚举，合并为同一 Feature。

### Task 1.1: 创建 agent_stations 数据库表

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T1.1 |
| **story_id** | US-AR-01 / US-AR-02 / US-AR-03 / US-AR-04 / US-AR-05 |
| **任务类型** | database |
| **文件** | `migrations/00x_create_agent_stations.sql` |
| **任务说明** | 创建 `agent_stations` 表，字段对齐 `AgentStation` 接口及 PRD 定义。包含：id, name, role, status, system_prompt, default_model_id, backup_model_ids, allowed_tools, max_steps_per_task, allow_handoff, handoff_threshold_tokens, current_task_id, total_tasks_completed, is_enabled, created_at, updated_at。 |
| **完成标准** | 1. 迁移脚本可正确执行，无报错<br>2. 字段类型、NOT NULL 约束、默认值正确<br>3. 创建索引：`idx_role`、`idx_status`、`idx_is_enabled`、`idx_current_task_id` |
| **依赖任务** | 无 |
| **推荐顺序** | 1 |

---

### Task 1.2: 定义 AgentStatus 枚举与领域校验规则

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T1.2 |
| **story_id** | US-AR-01 / US-AR-02 / US-AR-03 / US-AR-04 |
| **任务类型** | backend |
| **文件** | `src/domain/agent.ts` 或 `src/models/agent.ts` |
| **任务说明** | 1. 定义 `AgentStatus` 枚举：idle / running / error / disabled / queued / reviewing / blocked / done<br>2. 定义 `AgentRole` 枚举：planner / coder / reviewer / research / summarizer / supervisor<br>3. 实现 `AgentStation` 的创建/更新校验逻辑：name 非空、role 合法、max_steps_per_task > 0<br>4. `is_enabled` 与 `status` 的联动：禁用后 status 不变，但 `is_enabled = false` 时 Model Router 不可选 |
| **完成标准** | 1. 枚举值与 PRD / Schema 文档完全一致<br>2. 创建校验：name 为空返回 400，role 非法返回 400<br>3. 更新校验：max_steps_per_task ≤ 0 返回 400<br>4. 单元测试覆盖全部校验规则 |
| **依赖任务** | AG-T1.1 |
| **推荐顺序** | 2 |

---

## Feature 2: Agent CRUD API

> 对应 Story: US-AR-01 / US-AR-02 / US-AR-03 / US-AR-04
> 说明：按 CRUD 拆分 4 个 API Task，每个 Task 独立可测。

### Task 2.1: GET /agents 列表查询 API

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T2.1 |
| **story_id** | US-AR-01 |
| **任务类型** | backend |
| **文件** | `src/routes/agents.ts`、`src/services/agent.service.ts` |
| **任务说明** | 1. 实现 `GET /agents` 接口，返回全部 Agent Station 列表<br>2. 支持查询参数：role、status、is_enabled、search（模糊匹配 name）<br>3. 支持排序：按 role 分组，组内按 name 排序<br>4. 返回字段：id, name, role, status, default_model_id, is_enabled, current_task_id, total_tasks_completed |
| **完成标准** | 1. 无参数时返回全部 Agent，按 role 分组排序<br>2. `?role=coder` 只返回 coder 角色<br>3. `?search=plan` 模糊匹配 name 包含 "plan" 的记录<br>4. 返回 JSON 结构：`{ agents: [...], total: number }`<br>5. 集成测试覆盖 |
| **依赖任务** | AG-T1.1 / AG-T1.2 |
| **推荐顺序** | 3 |

---

### Task 2.2: POST /agents 创建 API

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T2.2 |
| **story_id** | US-AR-02 |
| **任务类型** | backend |
| **文件** | `src/routes/agents.ts`、`src/services/agent.service.ts` |
| **任务说明** | 1. 接收 `{ name, role, system_prompt, default_model_id, allow_handoff, max_steps_per_task? }`<br>2. 必填校验：name、role、default_model_id 不可为空<br>3. 校验 default_model_id 对应模型存在且 enabled<br>4. 创建记录，status 默认为 idle，is_enabled 默认为 true，total_tasks_completed = 0<br>5. 返回 `{ agent_id, status: "idle" }` |
| **完成标准** | 1. 正常请求返回 201 + `{ agent_id, status }`<br>2. 缺少必填字段返回 400 + 明确错误信息<br>3. default_model_id 不存在或禁用时返回 400<br>4. 创建成功后数据库记录完整<br>5. 集成测试覆盖 |
| **依赖任务** | AG-T1.1 / AG-T1.2 |
| **推荐顺序** | 4 |

---

### Task 2.3: PATCH /agents/:id 编辑 API

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T2.3 |
| **story_id** | US-AR-03 |
| **任务类型** | backend |
| **文件** | `src/routes/agents.ts`、`src/services/agent.service.ts` |
| **任务说明** | 1. 接收部分更新字段（只传修改的字段）<br>2. 支持更新：name, system_prompt, default_model_id, backup_model_ids, max_steps_per_task, allow_handoff, handoff_threshold_tokens<br>3. default_model_id 变更时校验模型存在且 enabled<br>4. max_steps_per_task 变更时校验 > 0<br>5. 返回更新后的完整 AgentStation |
| **完成标准** | 1. 只传 name 时，只更新 name，其他字段不变<br>2. default_model_id 非法返回 400<br>3. max_steps_per_task ≤ 0 返回 400<br>4. Agent 不存在返回 404<br>5. 返回 200 + 更新后的完整对象<br>6. 集成测试覆盖 |
| **依赖任务** | AG-T2.2 |
| **推荐顺序** | 5 |

---

### Task 2.4: PATCH /agents/:id/status 启用禁用 API

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T2.4 |
| **story_id** | US-AR-04 |
| **任务类型** | backend |
| **文件** | `src/routes/agents.ts`、`src/services/agent.service.ts` |
| **任务说明** | 1. 接收 `{ is_enabled: boolean }`<br>2. 更新 AgentStation 的 `is_enabled` 字段<br>3. 禁用后 Model Router 不再将该 Agent 作为候选（通过 `is_enabled = true` 筛选）<br>4. 返回更新后的完整 AgentStation |
| **完成标准** | 1. `is_enabled = false` 后，GET /agents 列表中该记录 is_enabled = false<br>2. 切换后返回 200 + 更新后的对象<br>3. Agent 不存在返回 404<br>4. 集成测试覆盖 |
| **依赖任务** | AG-T2.1 / AG-T2.2 |
| **推荐顺序** | 6 |

---

## Feature 3: Agent 模板系统

> 对应 Story: US-AR-05

### Task 3.1: 实现 Agent 模板数据与 GET /agents/templates API

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T3.1 |
| **story_id** | US-AR-05 |
| **任务类型** | backend |
| **文件** | `src/data/agent-templates.ts`、`src/routes/agents.ts` |
| **任务说明** | 1. 在代码中定义 6 个角色模板（planner / coder / reviewer / research / summarizer / supervisor）<br>2. 每个模板包含：role、system_prompt、default_model_id 建议、allowed_tools、max_steps_per_task、output_format<br>3. 实现 `GET /agents/templates` 返回模板列表<br>4. 模板数据 hard-coded 在代码中（MVP 无需数据库表） |
| **完成标准** | 1. `GET /agents/templates` 返回 6 个模板对象<br>2. 每个模板包含 role、system_prompt、default_model_id、allowed_tools<br>3. Coder 模板的 system_prompt 包含代码生成相关指令<br>4. Reviewer 模板的 system_prompt 包含代码审查相关指令<br>5. 集成测试覆盖 |
| **依赖任务** | AG-T1.2 |
| **推荐顺序** | 7 |

---

### Task 3.2: 模板创建集成（POST /agents 支持模板初始化）

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T3.2 |
| **story_id** | US-AR-05 |
| **任务类型** | backend |
| **文件** | `src/services/agent.service.ts` |
| **任务说明** | 1. `POST /agents` 支持可选参数 `template_id`<br>2. 如果传入 `template_id`，用模板数据预填充未提供的字段<br>3. 用户可覆盖模板中的任何字段（如自定义 system_prompt）<br>4. 模板创建后生成的 Agent 与普通 Agent 无区别 |
| **完成标准** | 1. `POST /agents { template_id: "coder", name: "My Coder" }` 自动填充 coder 模板的 system_prompt 等字段<br>2. 同时传入 name 和 template_id 时，以传入的 name 为准<br>3. 非法 template_id 返回 400<br>4. 集成测试覆盖 |
| **依赖任务** | AG-T2.2 / AG-T3.1 |
| **推荐顺序** | 8 |

---

## Feature 4: Agent Registry 前端页面

> 对应 Story: US-AR-01 / US-AR-02 / US-AR-03 / US-AR-04 / US-AR-05
> 说明：先做列表页（可读），再做表单和交互（可写）。先做 mock 数据跑通页面，再对接真实 API。

### Task 4.1: AgentRegistryPage 页面框架 + AgentList 列表（含 mock 数据）

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T4.1 |
| **story_id** | US-AR-01 |
| **任务类型** | frontend |
| **文件** | `src/pages/AgentRegistryPage.tsx`、`src/components/AgentList.tsx`、`src/hooks/useAgents.ts` |
| **任务说明** | 1. 创建 AgentRegistryPage 页面路由 `/agents`<br>2. 实现 AgentList 组件：展示 Agent 列表，每行显示 name、role 标签、status 指示灯、default_model、is_enabled 开关<br>3. 实现搜索框（按 name 实时过滤）和 role/status 筛选器<br>4. 先使用 mock 数据（5-6 条假数据）让页面可独立运行和视觉验收<br>5. 预留 API 对接接口（useAgents hook），切换 mock/real 只需改一行配置 |
| **完成标准** | 1. 页面可访问 `/agents`，展示列表<br>2. 每行正确显示 name、role 标签（如 Planner/Coder）、status 指示灯（绿/蓝/红/灰）<br>3. 搜索框输入后列表实时过滤<br>4. 筛选器支持 role 和 status 多选<br>5. 点击 Agent 行可展开/进入编辑（预留事件）<br>6. mock 数据与真实 API 返回结构一致 |
| **依赖任务** | 无（与后端并行） |
| **推荐顺序** | 9（可与 AG-T2.1 并行） |

---

### Task 4.2: 对接真实 API（AgentList 数据层）

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T4.2 |
| **story_id** | US-AR-01 |
| **任务类型** | frontend |
| **文件** | `src/hooks/useAgents.ts`、`src/api/agents.ts` |
| **任务说明** | 1. 实现 `api.getAgents(params)` 封装 `GET /agents`<br>2. useAgents hook 从 mock 切换到真实 API 调用<br>3. 处理 loading、error、empty 状态<br>4. 搜索和筛选参数通过 query string 传递给后端 |
| **完成标准** | 1. 页面加载时显示真实数据库中的 Agent 列表<br>2. 搜索和筛选调用真实 API，不是前端过滤<br>3. loading 状态有骨架屏或 spinner<br>4. API 错误时显示友好错误提示<br>5. 空列表时显示 "暂无 Agent，点击创建" 引导 |
| **依赖任务** | AG-T2.1 / AG-T4.1 |
| **推荐顺序** | 10 |

---

### Task 4.3: AgentConfigForm 组件（创建 + 编辑共用）

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T4.3 |
| **story_id** | US-AR-02 / US-AR-03 |
| **任务类型** | frontend |
| **文件** | `src/components/AgentConfigForm.tsx`、`src/components/AgentCreateModal.tsx`、`src/components/AgentEditModal.tsx` |
| **任务说明** | 1. 实现共用表单组件 AgentConfigForm，字段：name（输入）、role（下拉 6 选项）、system_prompt（文本域）、default_model_id（下拉，从 Model 列表获取）、allow_handoff（Switch）、max_steps_per_task（数字输入）<br>2. 创建模态框：点击 [创建 Agent] 弹出，表单为空<br>3. 编辑模态框：点击 Agent 行 [编辑] 弹出，表单预填当前值<br>4. 表单校验：name 为空时提交按钮禁用<br>5. 提交时调用 POST /agents 或 PATCH /agents/:id<br>6. 成功后关闭模态框，刷新列表，显示 toast |
| **完成标准** | 1. 创建模态框表单字段完整，name 为空时提交禁用<br>2. 编辑模态框预填数据正确<br>3. role 下拉包含 6 个选项：planner、coder、reviewer、research、summarizer、supervisor<br>4. default_model_id 下拉从 `GET /models` 获取可用模型列表<br>5. 提交成功后有 toast 提示 "创建成功" / "保存成功"<br>6. 提交失败后显示错误信息，不关闭模态框 |
| **依赖任务** | AG-T2.2 / AG-T2.3 / AG-T4.2 |
| **推荐顺序** | 11 |

---

### Task 4.4: 启用/禁用开关 + 状态变更反馈

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T4.4 |
| **story_id** | US-AR-04 |
| **任务类型** | frontend |
| **文件** | `src/components/AgentList.tsx`、`src/components/AgentStatusToggle.tsx` |
| **任务说明** | 1. AgentList 每行显示 is_enabled Switch<br>2. 点击 Switch 时：如果 Agent 有 current_task_id（正在运行任务），弹出确认框 "该 Agent 有正在执行的任务，禁用后将不再接收新任务"<br>3. 确认后调用 `PATCH /agents/:id/status`<br>4. 禁用后 Agent 行变灰，状态标签显示 "disabled"<br>5. 成功后显示 toast，列表状态更新 |
| **完成标准** | 1. 每行有 Switch，点击可切换 is_enabled<br>2. running 状态的 Agent 切换时弹出确认框<br>3. 禁用后行背景变灰，文字颜色变淡<br>4. 状态标签正确显示 "enabled" / "disabled"<br>5. API 调用失败时 Switch 回弹到原状态 |
| **依赖任务** | AG-T2.4 / AG-T4.2 |
| **推荐顺序** | 12 |

---

### Task 4.5: 模板创建 UI（模板卡片 + 快速创建）

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T4.5 |
| **story_id** | US-AR-05 |
| **任务类型** | frontend |
| **文件** | `src/components/AgentTemplateCards.tsx`、`src/components/AgentCreateModal.tsx` |
| **任务说明** | 1. 在 AgentRegistryPage 顶部添加 [从模板创建] 按钮<br>2. 点击后展示 6 个角色卡片（Planner/Coder/Reviewer/Research/Summarizer/Supervisor），每个卡片显示角色名、简介、建议模型<br>3. 点击卡片后弹出创建模态框，表单预填该模板的默认配置<br>4. 用户可修改预填内容后提交 |
| **完成标准** | 1. [从模板创建] 按钮可见<br>2. 6 个模板卡片布局整齐，有角色图标<br>3. 点击 Coder 卡片后，表单 system_prompt 预填代码生成指令<br>4. 用户修改 name 后可直接提交创建<br>5. 创建成功后列表刷新，新 Agent 显示在列表中 |
| **依赖任务** | AG-T3.1 / AG-T3.2 / AG-T4.3 |
| **推荐顺序** | 13 |

---

## Feature 5: Agent 使用统计（P1）

> 对应 Story: US-AR-06
> 说明：P1 功能，依赖其他模块（WorkerSession、ExecutionLog）已有数据。先只做前端展示 + 简单聚合查询。

### Task 5.1: GET /agents/:id/stats API

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T5.1 |
| **story_id** | US-AR-06 |
| **任务类型** | backend |
| **文件** | `src/routes/agents.ts`、`src/services/agent-stats.service.ts` |
| **任务说明** | 1. 实现 `GET /agents/:id/stats` 接口<br>2. 从 worker_sessions 表聚合：total_completed（status=completed 的数量）、total_failed（status=failed 的数量）、avg_duration_ms<br>3. 从 execution_logs 表聚合：avg_tokens（该 agent 相关 model_call 的 token 平均值）<br>4. 从 handoff_records 表聚合：recent_handoffs（最近 5 次交接记录）<br>5. 返回 `{ total_completed, total_failed, avg_tokens, avg_duration_ms, recent_handoffs }` |
| **完成标准** | 1. 正常请求返回 200 + 统计对象<br>2. Agent 不存在返回 404<br>3. 无历史数据时各字段返回 0 或空数组<br>4. 集成测试覆盖 |
| **依赖任务** | AG-T2.1（需要 Agent 表已存在） |
| **推荐顺序** | 14（P1，延后） |

---

### Task 5.2: AgentStatsPanel 组件

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T5.2 |
| **story_id** | US-AR-06 |
| **任务类型** | frontend |
| **文件** | `src/components/AgentStatsPanel.tsx` |
| **任务说明** | 1. 实现 AgentStatsPanel 组件，以卡片形式展示关键指标<br>2. 指标：完成任务数、失败任务数、平均 Token 消耗、平均执行时长、最近 Handoff 次数<br>3. 点击 Agent 行的 [查看统计] 按钮后弹出/展开该面板<br>4. 对接 `GET /agents/:id/stats` |
| **完成标准** | 1. 面板正确展示 5 个统计指标<br>2. 数据为 0 时显示 "—" 或 "暂无数据"<br>3. 最近 Handoff 以列表形式展示（时间、from→to、reason）<br>4. 加载中有 spinner，错误时有提示 |
| **依赖任务** | AG-T5.1 / AG-T4.2 |
| **推荐顺序** | 15（P1，延后） |

---

## Feature 6: 测试与质量保障

> 覆盖全部 P0 故事的测试矩阵。

### Task 6.1: 后端 API 单元 + 集成测试

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T6.1 |
| **story_id** | US-AR-01 / US-AR-02 / US-AR-03 / US-AR-04 / US-AR-05 |
| **任务类型** | test |
| **文件** | `tests/agents.api.test.ts`、`tests/agents.service.test.ts` |
| **任务说明** | 1. `GET /agents` — 正常/筛选/搜索/空列表<br>2. `POST /agents` — 正常/缺字段/非法 role/非法 model_id<br>3. `PATCH /agents/:id` — 正常/部分更新/非法字段/不存在<br>4. `PATCH /agents/:id/status` — 启用/禁用/不存在<br>5. `GET /agents/templates` — 返回 6 个模板<br>6. `POST /agents` with template_id — 正常/非法 template_id |
| **完成标准** | 1. 全部 5 个 API 的 happy path 和主要错误 path 都有测试<br>2. 每个 API 至少 3 个测试用例<br>3. 数据库状态在每次测试后正确清理<br>4. 测试覆盖率 ≥ 80% |
| **依赖任务** | AG-T2.1 / AG-T2.2 / AG-T2.3 / AG-T2.4 / AG-T3.1 / AG-T3.2 |
| **推荐顺序** | 16（与开发并行） |

---

### Task 6.2: 前端组件测试

| 属性 | 值 |
|------|-----|
| **task_id** | AG-T6.2 |
| **story_id** | US-AR-01 / US-AR-02 / US-AR-03 / US-AR-04 / US-AR-05 |
| **任务类型** | test |
| **文件** | `tests/components/AgentList.test.tsx`、`tests/components/AgentConfigForm.test.tsx`、`tests/components/AgentStatusToggle.test.tsx` |
| **任务说明** | 1. AgentList：渲染、搜索过滤、筛选、点击事件<br>2. AgentConfigForm：表单渲染、校验、提交、预填数据<br>3. AgentStatusToggle：开关切换、确认框、禁用后样式<br>4. AgentTemplateCards：6 个卡片渲染、点击事件 |
| **完成标准** | 1. 全部 4 个组件有独立测试文件<br>2. 每个组件覆盖主要渲染状态和用户交互<br>3. 表单测试覆盖：空提交被阻止、合法提交调用 API |
| **依赖任务** | AG-T4.1 / AG-T4.3 / AG-T4.4 / AG-T4.5 |
| **推荐顺序** | 17（与开发并行） |

---

## 推荐开发顺序

```
Phase 1 — 数据模型 + API 骨架（1 周）
  AG-T1.1  创建 agent_stations 表
  AG-T1.2  定义状态枚举与校验
  AG-T2.1  GET /agents 列表 API
  AG-T2.2  POST /agents 创建 API
  AG-T2.3  PATCH /agents/:id 编辑 API
  AG-T2.4  PATCH /agents/:id/status 启用禁用 API
  AG-T6.1  后端 API 测试（与开发并行）

Phase 2 — 模板系统（3 天）
  AG-T3.1  模板数据 + GET /agents/templates API
  AG-T3.2  模板创建集成

Phase 3 — 前端页面 + 交互（1 周）
  AG-T4.1  AgentRegistryPage + AgentList（mock 数据）
  AG-T4.2  对接真实 API
  AG-T4.3  AgentConfigForm（创建 + 编辑）
  AG-T4.4  启用/禁用开关
  AG-T4.5  模板创建 UI
  AG-T6.2  前端组件测试（与开发并行）

Phase 4 — P1 统计（可选，3 天）
  AG-T5.1  GET /agents/:id/stats API
  AG-T5.2  AgentStatsPanel 组件
```

---

## 按 Phase 排期的任务看板

### Phase 1 — 数据模型与 API（1 周）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| AG-T1.1 | agent_stations 表结构 | database | 无 | AR-01~05 |
| AG-T1.2 | AgentStatus / AgentRole 枚举 + 校验 | backend | AG-T1.1 | AR-01~04 |
| AG-T2.1 | GET /agents 列表查询 | backend | AG-T1.2 | AR-01 |
| AG-T2.2 | POST /agents 创建 | backend | AG-T1.2 | AR-02 |
| AG-T2.3 | PATCH /agents/:id 编辑 | backend | AG-T2.2 | AR-03 |
| AG-T2.4 | PATCH /agents/:id/status 切换 | backend | AG-T2.1 | AR-04 |
| AG-T6.1 | 后端 API 测试 | test | AG-T2.x | AR-01~05 |

**Phase 1 交付物：** 完整的 Agent CRUD API，可通过 HTTP 工具（curl/Postman）创建、查询、编辑、启禁用 Agent。

### Phase 2 — 模板系统（3 天）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| AG-T3.1 | 6 个模板数据 + templates API | backend | AG-T1.2 | AR-05 |
| AG-T3.2 | 模板创建集成到 POST /agents | backend | AG-T3.1 | AR-05 |

**Phase 2 交付物：** 用户可通过模板快速创建 Agent，API 支持 template_id 参数。

### Phase 3 — 前端页面（1 周）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| AG-T4.1 | AgentRegistryPage + 列表（mock） | frontend | 无 | AR-01 |
| AG-T4.2 | 对接真实 API | frontend | AG-T2.1 | AR-01 |
| AG-T4.3 | 创建/编辑表单 | frontend | AG-T2.2/2.3 | AR-02/03 |
| AG-T4.4 | 启用/禁用开关 | frontend | AG-T2.4 | AR-04 |
| AG-T4.5 | 模板创建 UI | frontend | AG-T3.1 | AR-05 |
| AG-T6.2 | 前端组件测试 | test | AG-T4.x | AR-01~05 |

**Phase 3 交付物：** 完整的 Agent Registry 前端页面，用户可在浏览器中完成全部 CRUD 和模板创建操作。

### Phase 4 — P1 统计（3 天，可选）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| AG-T5.1 | GET /agents/:id/stats | backend | AG-T2.1 | AR-06 |
| AG-T5.2 | AgentStatsPanel 组件 | frontend | AG-T5.1 | AR-06 |

**Phase 4 交付物：** Agent 使用统计面板，展示任务完成数、Token 消耗等指标。

---

## 风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| default_model_id 校验依赖 Model 模块 | 如果 Model 模块未就绪，Agent 创建会失败 | AG-T2.2 中 model_id 校验先做成软校验（警告但不阻止），或允许传入任意字符串，等 Model 模块就绪后加硬校验 |
| 前端 Model 下拉列表需要 Model 模块的 GET /models | AgentConfigForm 的 model 下拉无数据 | AG-T4.3 中先 hard-code 几个常用模型作为 mock，等 Model 模块就绪后切换为真实 API |
| AgentStats 依赖 WorkerSession / ExecutionLog / Handoff 表 | 如果这些模块未就绪，stats API 无法查询 | AG-T5.1 延迟到 Phase 4，且查询逻辑做防御性编程（表不存在时返回 0） |
| 6 个角色的 system_prompt 质量 | 影响 Agent 实际执行效果 | 模板中的 prompt 先使用通用版本，后续由实际使用反馈迭代优化 |

---

## Story → Task 映射表

| Story | 涉及 Task | 是否完整覆盖 |
|-------|-----------|--------------|
| US-AR-01 查看列表 | AG-T1.1 / AG-T1.2 / AG-T2.1 / AG-T4.1 / AG-T4.2 | 是 |
| US-AR-02 创建 Agent | AG-T1.1 / AG-T1.2 / AG-T2.2 / AG-T4.3 | 是 |
| US-AR-03 编辑配置 | AG-T1.1 / AG-T2.3 / AG-T4.3 | 是 |
| US-AR-04 启用禁用 | AG-T1.1 / AG-T2.4 / AG-T4.4 | 是 |
| US-AR-05 模板创建 | AG-T1.2 / AG-T3.1 / AG-T3.2 / AG-T4.5 | 是 |
| US-AR-06 使用统计 | AG-T5.1 / AG-T5.2 | 是 |

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
>
> 相关文档：
> - `docs/stories/agent-registry-stories.md` — 用户故事来源
> - `docs/prd/agent-registry-prd.md` — 产品需求
> - `docs/architecture/数据结构与数据库Schema.md` — Schema 定义
