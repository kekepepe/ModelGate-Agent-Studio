# Model Router 用户故事

> 所属产品：ModelGate Agent Studio
>
> 来源文档：`docs/prd/model-router-prd.md`
>
> 文档定位：将 Model Router PRD 转化为可开发、可测试的用户故事与验收标准。

---

## 故事清单

| 编号 | 优先级 | 故事摘要 | 涉及页面 | 涉及接口 | 数据对象 |
|------|--------|----------|----------|----------|----------|
| US-MR-01 | P0 | 自动路由选择模型 | Workspace | `POST /router/select-model` | RoutingRequest, RoutingResult |
| US-MR-02 | P0 | 查看路由决策详情 | Workspace, RoutingResultCard | `POST /router/select-model` | RoutingResult |
| US-MR-03 | P0 | 手动覆盖路由决策 | Workspace, RoutingResultCard | `POST /router/override-model` | RoutingResult, WorkerSession |
| US-MR-04 | P0 | 额度不足模型自动排除 | ModelRouter | `POST /router/select-model` | RoutingResult, QuotaRecord |
| US-MR-05 | P0 | 查看评分拆解矩阵 | Workspace, RoutingResultCard | `POST /router/select-model` | RoutingResult |
| US-MR-06 | P1 | 查看路由规则配置 | RouterRulesPage | `GET /router/rules` | RoutingRule |

---

## P0 用户故事

### US-MR-01：自动路由选择模型

- **Summary:** 系统根据 Task 特征、Agent 角色、模型能力和额度状态，自动选择最合适的模型驱动 Worker。

#### Use Case:
- **As a** 多模型重度使用的开发者
- **I want to** 系统自动为每个 Task 选择最合适的模型
- **so that** 我不需要手动判断哪个模型更适合当前任务，减少选错模型的成本

#### Acceptance Criteria:

- **Scenario:** Task 分配时自动路由
- **Given:** 一个 Task 已分配给某个 Agent Station，系统需要为该 Task 选择模型
- **When:** Agent Runtime 调用 Model Router
- **Then：** Model Router 返回 `RoutingResult`，包含 `selected_model_id`、`backup_model_ids`、`confidence`
- **and Then：** 如果存在额度状态为 `LIMITED` 或 `COOLDOWN` 的模型，该模型被排除（hard constraint）
- **and Then：** 选择的模型与 Agent 角色的默认偏好匹配

**涉及页面：** Workspace / AgentStationBoard / WorkerBadge
**涉及接口：** `POST /router/select-model`
**数据对象：** RoutingRequest, RoutingResult, Model

**可转测试的验收点：**
1. 后端：`POST /router/select-model` 接收 `{ task_id, task_type, task_complexity, required_capabilities, agent_role }`
2. 后端：返回的 `selected_model_id` 对应的模型 `is_enabled = true`
3. 后端：`LIMITED`/`COOLDOWN` 状态的模型不在 `selected_model_id` 和 `backup_model_ids` 中
4. 后端：`confidence` 为 0-1 之间的浮点数
5. 后端：代码生成任务优先返回代码能力强的模型（如 gpt-4o / deepseek）
6. 后端：复杂规划任务优先返回长上下文能力强的模型（如 claude-3-5）

---

### US-MR-02：查看路由决策详情

- **Summary:** Workspace 弹出 RoutingResultCard，展示推荐模型、置信度、路由理由和风险标记。

#### Use Case:
- **As a** 需要理解系统决策的开发者
- **I want to** 看到 Model Router 为什么选择了某个模型
- **so that** 我信任系统的决策，或在有疑虑时手动覆盖

#### Acceptance Criteria:

- **Scenario：** 查看路由决策
- **Given：** Model Router 已完成路由决策
- **When：** Workspace 展示 RoutingResultCard
- **Then：** Card 显示：推荐模型名、置信度进度条、路由理由文本、备用模型列表
- **and Then：** 如果有风险标记（如 `near_quota_limit`），显示 RiskFlagBanner

**涉及页面：** Workspace / RoutingResultCard
**涉及接口：** `POST /router/select-model`
**数据对象：** RoutingResult

**可转测试的验收点：**
1. 前端：RoutingResultCard 以浮层弹出，不阻塞主流程
2. 前端：置信度条可视化显示（如 0.95 = 95% 填充）
3. 前端：路由理由以自然语言展示（如 "代码生成任务，GPT-4o 能力匹配度最高"）
4. 后端：返回的 `routing_reason` 为非空字符串
5. 后端：`risk_flags` 为空数组或包含有效的 risk_flag 枚举值

---

### US-MR-03：手动覆盖路由决策

- **Summary:** 用户可以不接受系统推荐的模型，手动选择备用模型继续执行任务。

#### Use Case:
- **As a** 对模型选择有偏好的开发者
- **I want to** 手动覆盖 Model Router 的推荐，选择我认为更适合的模型
- **so that** 当系统推荐不符合我的预期时，我可以按自己的判断执行

#### Acceptance Criteria:

- **Scenario：** 手动覆盖路由
- **Given：** RoutingResultCard 正在展示，推荐模型为 A
- **When：** 我点击 [切换模型]，从备用列表中选择模型 B，确认
- **Then：** 系统使用模型 B 创建 WorkerSession，替代推荐模型 A
- **and Then：** Workspace 中 WorkerBadge 显示模型 B
- **and Then：** 覆盖记录写入 ExecutionLog（`event_type: model_override`）

**涉及页面：** Workspace / RoutingResultCard
**涉及接口：** `POST /router/override-model`
**数据对象：** RoutingResult, WorkerSession, ExecutionLog

**可转测试的验收点：**
1. 前端：点击 [切换模型] 后弹出备用模型选择列表
2. 前端：选择备用模型后 WorkerBadge 更新为新模型名
3. 后端：`POST /router/override-model` 接收 `{ task_id, selected_model_id, original_model_id, reason }`
4. 后端：覆盖的模型在 `backup_model_ids` 列表中时才允许
5. 后端：覆盖后新 Worker 的 `model_id` = 用户选择的模型

---

### US-MR-04：额度不足模型自动排除

- **Summary:** Model Router 在评分时自动排除额度状态为 LIMITED 或 COOLDOWN 的模型，避免任务分配给即将耗尽的模型。

#### Use Case:
- **As a** 不希望任务因额度中断的开发者
- **I want to** 系统在选择模型时自动避开额度不足的模型
- **so that** 任务不会因为模型额度耗尽而突然中断

#### Acceptance Criteria:

- **Scenario：** 额度不足模型被排除
- **Given：** 模型 A 的 `quota_status` 为 `LIMITED`，模型 B 的 `quota_status` 为 `NORMAL`
- **When：** Model Router 为 Task 选择模型
- **Then：** 模型 A 被排除，即使它在其他维度评分最高
- **and Then：** 如果所有候选模型都 LIMITED/COOLDOWN，RoutingResult 的 `risk_flags` 包含 `"all_models_limited"`
- **and Then：** 如果没有可用模型，返回错误，任务暂停

**涉及页面：** Workspace / RoutingResultCard / ErrorBanner
**涉及接口：** `POST /router/select-model`
**数据对象：** RoutingResult, QuotaRecord

**可转测试的验收点：**
1. 后端：模型 `quota_status = LIMITED` 时 `quota_health_score = 0`
2. 后端：所有候选模型 `quota_health = 0` 时返回 `risk_flags: ["all_models_limited"]`
3. 后端：无可用模型时返回 HTTP 503 或特定错误码
4. 前端："all_models_limited" 时 ErrorBanner 显示 "无可用的模型，请检查额度配置"

---

### US-MR-05：查看评分拆解矩阵

- **Summary:** RoutingResultCard 展示 6 个评分维度的拆解（capability_match、role_match、context_fit、cost_fit、speed_fit、quota_health）。

#### Use Case:
- **As a** 需要深入理解模型选择逻辑的开发者
- **I want to** 看到每个评分维度的具体分数
- **so that** 我理解为什么模型 A 比模型 B 得分高，哪些维度影响了决策

#### Acceptance Criteria:

- **Scenario：** 查看评分拆解
- **Given：** RoutingResultCard 已弹出
- **When：** 我点击 [查看详情] 或展开评分区域
- **Then：** 展示 6 个维度的评分条：capability_match、role_match、context_fit、cost_fit、speed_fit、quota_health
- **and Then：** 每个维度显示原始分数和权重（如 capability_match: 0.95 × 0.25 = 0.2375）
- **and Then：** 各维度分数用不同颜色区分

**涉及页面：** Workspace / RoutingResultCard
**涉及接口：** `POST /router/select-model`
**数据对象：** RoutingResult

**可转测试的验收点：**
1. 前端：评分区域默认收起，点击展开
2. 前端：每个维度显示为水平进度条，0-1 范围
3. 后端：`score_breakdown` 包含全部 6 个字段，值为 0-1 的浮点数
4. 后端：各维度分数 × 权重之和 ≈ `confidence`

---

## P1 用户故事

### US-MR-06：查看路由规则配置

- **Summary:** 用户查看当前 Model Router 的路由规则配置，包括各维度的默认权重和 hard constraints。

#### Use Case:
- **As a** 需要调整路由策略的高级用户
- **I want to** 查看当前的路由规则配置
- **so that** 我理解系统如何评分，并为后续自定义权重做准备

#### Acceptance Criteria:

- **Scenario：** 查看路由规则
- **Given：** 我进入 Router Rules 页面
- **When：** 页面加载
- **Then：** 展示当前规则：各维度权重、hard constraints 列表、模型能力标签映射

**涉及页面：** RouterRulesPage
**涉及接口：** `GET /router/rules`
**数据对象：** RoutingRule

**可转测试的验收点：**
1. 前端：页面展示权重配置表格
2. 后端：`GET /router/rules` 返回 `{ weights: { capability_match: 0.25, role_match: 0.20, ... }, hard_constraints: [...] }`

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
