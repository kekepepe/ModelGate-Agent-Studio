# Model Router 开发任务拆解

> 基于 `docs/stories/model-router-stories.md` 的 5 条 P0 + 1 条 P1 用户故事拆解
>
> 拆分模式：Simple/Complex (Pattern 7) + Major Effort (Pattern 6)
> ——先做最简单的规则匹配让路由 API 可运行，再叠加多维度评分算法；先做 mock 前端卡片，再对接真实数据。

---

## Epic: Model Router

**目标：** 系统根据 Task 特征、Agent 角色、模型能力和额度状态，自动选择最合适的模型，并让用户看到决策依据和手动覆盖。

**Epic 验收标准：**
1. Task 分配时系统自动返回推荐模型、置信度、备用模型列表
2. LIMITED/COOLDOWN 额度状态的模型被自动排除
3. 用户可在 Workspace 看到路由决策卡片（模型名、置信度、理由、风险标记）
4. 用户可手动切换为备用模型
5. 评分拆解展示 6 个维度的具体分数
6. 路由规则配置可查看（P1）

---

## Feature 1: 模型路由数据结构与基础配置

> 对应 Story: US-MR-01 / US-MR-05 / US-MR-06
> 说明：所有 Story 共享同一套数据结构（RoutingRequest、RoutingResult、评分维度、权重），合并为同一 Feature。

### Task 1.1: 定义模型能力标签与 Routing 核心数据结构

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T1.1 |
| **story_id** | US-MR-01 / US-MR-05 / US-MR-06 |
| **任务类型** | backend |
| **文件** | `src/domain/router.ts`、`src/domain/model.ts` |
| **任务说明** | 1. 定义 `ModelCapability` 枚举/标签：code_generation、long_context、reasoning、multimodal、speed、cost_efficient<br>2. 定义 `RoutingRequest` 接口：task_id、task_type、task_complexity、required_capabilities[]、agent_role<br>3. 定义 `RoutingResult` 接口：selected_model_id、backup_model_ids[]、confidence、routing_reason、risk_flags[]、score_breakdown<br>4. 定义 `ScoreBreakdown` 接口：capability_match、role_match、context_fit、cost_fit、speed_fit、quota_health（均为 0-1 浮点数）<br>5. 在代码中 hard-code 模型能力标签映射（如 gpt-4o → [code_generation, multimodal]），MVP 阶段不建独立配置表 |
| **完成标准** | 1. TypeScript 类型定义完整，与 PRD 完全一致<br>2. 至少 hard-code 4-6 个常用模型的能力标签<br>3. `confidence` 计算逻辑可验证：各维度分数 × 权重之和 ≈ confidence<br>4. 有单元测试验证类型定义和基本计算 |
| **依赖任务** | 无 |
| **推荐顺序** | 1 |

---

### Task 1.2: 定义路由规则配置（权重 + 硬约束）

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T1.2 |
| **story_id** | US-MR-01 / US-MR-05 / US-MR-06 |
| **任务类型** | backend |
| **文件** | `src/config/router.config.ts` |
| **任务说明** | 1. 在代码中 hard-code 6 个维度的默认权重：capability_match=0.25、role_match=0.20、context_fit=0.15、cost_fit=0.15、speed_fit=0.10、quota_health=0.10<br>2. 定义硬约束规则列表：is_enabled 必须为 true、quota_status 不能为 LIMITED 或 COOLDOWN<br>3. 定义角色-模型偏好映射：coder 偏好 code_generation 强的模型、planner 偏好 long_context 强的模型<br>4. 配置以 TypeScript 对象形式存在，MVP 不暴露给用户修改 |
| **完成标准** | 1. 权重总和为 1.0（允许浮点误差 ±0.001）<br>2. 硬约束规则可被独立调用和测试<br>3. 角色偏好映射覆盖 6 个角色<br>4. 单元测试验证权重总和和约束逻辑 |
| **依赖任务** | MR-T1.1 |
| **推荐顺序** | 2 |

---

## Feature 2: 评分引擎

> 对应 Story: US-MR-01 / US-MR-04 / US-MR-05
> 说明：评分引擎是 Model Router 的核心。先做最简单的规则匹配让 API 能跑通，再叠加完整的 6 维度评分。

### Task 2.1: 模型候选池筛选（硬约束过滤）

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T2.1 |
| **story_id** | US-MR-04 |
| **任务类型** | backend |
| **文件** | `src/services/router/candidate-filter.ts` |
| **任务说明** | 1. 实现候选池筛选器：从 models 表中获取所有 is_enabled = true 的模型<br>2. 查询每个模型的 QuotaStatus，排除 LIMITED 和 COOLDOWN 的模型<br>3. 如果没有可用模型，返回空数组，并标记 risk_flag = "all_models_limited"<br>4. 被排除的模型记录排除原因（用于后续调试和前端展示）<br>5. MVP 阶段 quota_status 查询可先用 mock 数据或简单查询，不依赖 Quota Manager 的实时推送 |
| **完成标准** | 1. LIMITED 模型不在候选池中<br>2. COOLDOWN 模型不在候选池中<br>3. disabled 模型不在候选池中<br>4. 全部候选模型 LIMITED 时返回空数组 + risk_flag "all_models_limited"<br>5. 单元测试覆盖：正常过滤 / 全部 LIMITED / 混合状态 |
| **依赖任务** | MR-T1.1 / MR-T1.2 |
| **推荐顺序** | 3 |

---

### Task 2.2: 简单评分实现（规则匹配优先，让 API 先跑通）

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T2.2 |
| **story_id** | US-MR-01 |
| **任务类型** | backend |
| **文件** | `src/services/router/simple-scorer.ts` |
| **任务说明** | 1. 实现最简单的评分逻辑（非最终算法，仅用于让 API 可运行）：<br>   - 根据 task_type 和 agent_role 匹配模型能力标签，匹配一个标签 +0.3 分，上限 1.0<br>   - 所有候选模型只计算 capability_match 一个维度，其余 5 个维度先固定为 0.5<br>   - confidence = capability_match × 0.25 + 0.5 × 0.75 = 简化计算<br>2. 返回排序后的候选列表，取最高分作为 selected_model，取第 2-3 名作为 backup_models<br>3. 生成简单的 routing_reason（如 "代码生成任务，GPT-4o 能力匹配度最高"）<br>4. 这个 Task 的目的是让 `POST /router/select-model` 能返回可用结果，不追求评分精度 |
| **完成标准** | 1. 给定 task_type="code" 时，优先返回有 code_generation 标签的模型<br>2. 返回的 RoutingResult 包含 selected_model_id、backup_model_ids、confidence、routing_reason<br>3. confidence 在 0-1 范围内<br>4. 单元测试覆盖：代码任务 / 规划任务 / 无匹配任务 |
| **依赖任务** | MR-T2.1 |
| **推荐顺序** | 4 |

---

### Task 2.3: 完整 6 维度评分算法

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T2.3 |
| **story_id** | US-MR-01 / US-MR-05 |
| **任务类型** | backend |
| **文件** | `src/services/router/score-engine.ts` |
| **任务说明** | 1. 实现 6 个维度的独立评分函数：<br>   - `capability_match`: 任务 required_capabilities 与模型能力标签的交集比例<br>   - `role_match`: agent_role 与模型偏好角色的匹配度（硬编码映射表）<br>   - `context_fit`: 根据 task_complexity 和模型 context_window 计算（简单规则：complexity 高 → 偏好 long_context 模型）<br>   - `cost_fit`: 根据模型定价估算，便宜模型得分高（MVP 先 hard-code 定价）<br>   - `speed_fit`: 根据模型平均响应时间评分（MVP 先 hard-code 基准值）<br>   - `quota_health`: 根据 quota_status 评分（normal=1.0, warning=0.7, near_limit=0.4, unknown=0.8）<br>2. 加权求和计算 confidence：Σ(维度分数 × 权重)<br>3. 各维度分数和 confidence 保留 4 位小数<br>4. 生成更精确的 routing_reason（自然语言描述） |
| **完成标准** | 1. 6 个维度都有独立评分函数，可单独测试<br>2. 加权求和结果在 0-1 范围内<br>3. `score_breakdown` 包含全部 6 个字段，值精确到小数点后 4 位<br>4. 各维度分数 × 权重之和 ≈ confidence（误差 < 0.001）<br>5. quota_health 对 LIMITED 模型返回 0（与 Task 2.1 的过滤形成双重保险）<br>6. 单元测试覆盖每个维度的评分逻辑 |
| **依赖任务** | MR-T2.2 |
| **推荐顺序** | 8（Phase 2 开始） |

---

## Feature 3: 路由 API

> 对应 Story: US-MR-01 / US-MR-03 / US-MR-04 / US-MR-05

### Task 3.1: POST /router/select-model API（先接入简单评分）

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T3.1 |
| **story_id** | US-MR-01 / US-MR-04 / US-MR-05 |
| **任务类型** | backend |
| **文件** | `src/routes/router.ts`、`src/services/router.service.ts` |
| **任务说明** | 1. 实现 `POST /router/select-model` 接口<br>2. 接收 `{ task_id, task_type, task_complexity, required_capabilities, agent_role }`<br>3. 先调用 Task 2.1 的候选池筛选，排除 LIMITED/disabled 模型<br>4. 先接入 Task 2.2 的简单评分（让 API 可运行），后续替换为 Task 2.3 的完整评分<br>5. 返回完整 RoutingResult：selected_model_id、backup_model_ids、confidence、routing_reason、risk_flags、score_breakdown（先用简化版，完整版在 Task 3.2 替换）<br>6. 候选池为空时返回 503 + risk_flags: ["all_models_limited"] |
| **完成标准** | 1. 正常请求返回 200 + 完整 RoutingResult<br>2. selected_model_id 对应的模型 is_enabled = true<br>3. LIMITED/COOLDOWN 模型不在 selected_model_id 和 backup_model_ids 中<br>4. 无可用模型时返回 503，body 包含 risk_flags<br>5. confidence 为 0-1 之间的浮点数<br>6. 集成测试覆盖：正常路由 / 额度排除 / 全部 LIMITED |
| **依赖任务** | MR-T2.1 / MR-T2.2 |
| **推荐顺序** | 5 |

---

### Task 3.2: POST /router/select-model API（升级为完整 6 维度评分）

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T3.2 |
| **story_id** | US-MR-01 / US-MR-05 |
| **任务类型** | backend |
| **文件** | `src/services/router.service.ts` |
| **任务说明** | 1. 将 Task 3.1 中的简单评分替换为 Task 2.3 的完整 6 维度评分引擎<br>2. score_breakdown 返回全部 6 个维度分数<br>3. routing_reason 升级为基于最高评分维度的自然语言描述<br>4. 增加 risk_flags 判定逻辑：near_quota_limit（推荐模型 quota_status = warning/near_limit 时）、all_models_limited（候选池为空时）<br>5. API 接口定义不变，仅替换内部实现 |
| **完成标准** | 1. 返回的 score_breakdown 包含 6 个字段，值为 0-1 浮点数<br>2. 各维度分数 × 权重之和 ≈ confidence<br>3. near_quota_limit 的模型被选中时，risk_flags 包含 "near_quota_limit"<br>4. 代码生成任务的 selected_model 优先为代码能力强的模型<br>5. 复杂规划任务优先为长上下文能力强的模型<br>6. 集成测试覆盖各 task_type 的路由结果 |
| **依赖任务** | MR-T2.3 / MR-T3.1 |
| **推荐顺序** | 9 |

---

### Task 3.3: POST /router/override-model API（手动覆盖）

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T3.3 |
| **story_id** | US-MR-03 |
| **任务类型** | backend |
| **文件** | `src/routes/router.ts`、`src/services/router.service.ts` |
| **任务说明** | 1. 实现 `POST /router/override-model` 接口<br>2. 接收 `{ task_id, selected_model_id, original_model_id, reason }`<br>3. 校验 selected_model_id 在原始 RoutingResult 的 backup_model_ids 列表中（才允许覆盖）<br>4. 校验 selected_model_id 的 quota_status 不是 LIMITED/COOLDOWN<br>5. 创建新的 WorkerSession，model_id = selected_model_id<br>6. 记录覆盖事件到 ExecutionLog（event_type = model_override）<br>7. 返回 `{ worker_id, model_id, status: "override_accepted" }` |
| **完成标准** | 1. 正常请求返回 200 + `{ worker_id, model_id, status }`<br>2. selected_model_id 不在 backup_model_ids 中时返回 400<br>3. selected_model_id 为 LIMITED 时返回 400<br>4. 覆盖后新 Worker 的 model_id = 用户选择的模型<br>5. ExecutionLog 中可查询到 model_override 事件<br>6. 集成测试覆盖 |
| **依赖任务** | MR-T3.1 |
| **推荐顺序** | 10 |

---

## Feature 4: Workspace 路由可视化

> 对应 Story: US-MR-02 / US-MR-03 / US-MR-05
> 说明：先做 mock 卡片让 UI 可独立验收，再对接真实 API。

### Task 4.1: RoutingResultCard 组件（mock 数据）

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T4.1 |
| **story_id** | US-MR-02 |
| **任务类型** | frontend |
| **文件** | `src/components/RoutingResultCard.tsx`、`src/components/RoutingResultCard.stories.tsx` |
| **任务说明** | 1. 实现 RoutingResultCard 组件，以浮层/卡片形式展示<br>2. 展示内容：推荐模型名、置信度进度条（0-100% 填充）、路由理由文本、备用模型列表<br>3. 如果有 risk_flags（如 near_quota_limit），显示 RiskFlagBanner（黄色警告条）<br>4. 卡片不阻塞主流程，5 秒后自动收起（用户未操作时）<br>5. 先使用 mock RoutingResult 数据，让 UI 可独立运行和视觉验收 |
| **完成标准** | 1. 组件可独立渲染，不依赖全局状态<br>2. 置信度条正确显示百分比（如 0.95 → 95% 填充）<br>3. RiskFlagBanner 在 risk_flags 非空时显示<br>4. 卡片有 [接受] 和 [切换模型] 两个按钮（先预留事件回调）<br>5. 5 秒无操作后自动收起（可通过 hover 重置计时器）<br>6. 组件测试覆盖 |
| **依赖任务** | 无（与后端并行） |
| **推荐顺序** | 6 |

---

### Task 4.2: 对接真实路由 API + 卡片交互

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T4.2 |
| **story_id** | US-MR-02 |
| **任务类型** | frontend |
| **文件** | `src/hooks/useModelRouter.ts`、`src/api/router.ts`、`src/components/RoutingResultCard.tsx` |
| **任务说明** | 1. 实现 `api.selectModel(params)` 封装 `POST /router/select-model`<br>2. useModelRouter hook：在 Task 分配给 Agent 时自动调用 selectModel，获取 RoutingResult<br>3. 获取结果后弹出 RoutingResultCard，展示真实数据<br>4. 点击 [接受] 按钮后卡片关闭，WorkerBadge 显示推荐模型<br>5. 点击 [切换模型] 按钮后弹出备用模型选择列表 |
| **完成标准** | 1. Task 分配时自动调用 API 并弹出卡片<br>2. 卡片展示真实模型名、置信度、理由<br>3. 点击 [接受] 后卡片关闭，无异常<br>4. 点击 [切换模型] 后弹出备用模型列表（从 backup_model_ids 获取）<br>5. API 错误时显示 ErrorBanner "模型路由失败，请重试"<br>6. 503 all_models_limited 时显示特殊提示 "无可用的模型，请检查额度配置" |
| **依赖任务** | MR-T3.1 / MR-T4.1 |
| **推荐顺序** | 7 |

---

### Task 4.3: 评分拆解矩阵 UI（6 维度展开区域）

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T4.3 |
| **story_id** | US-MR-05 |
| **任务类型** | frontend |
| **文件** | `src/components/ScoreBreakdownPanel.tsx` |
| **任务说明** | 1. 在 RoutingResultCard 中增加 [查看详情] 按钮或展开区域<br>2. 展开后展示 6 个维度的评分条：capability_match、role_match、context_fit、cost_fit、speed_fit、quota_health<br>3. 每个维度显示：维度名、原始分数（0-1）、权重（如 ×0.25）、加权得分<br>4. 各维度分数用不同颜色区分（capability=蓝、role=绿、context=紫、cost=黄、speed=青、quota=橙）<br>5. 默认收起，点击展开 |
| **完成标准** | 1. 评分区域默认收起，点击后展开（300ms 动画）<br>2. 6 个维度都显示为水平进度条，0-1 范围映射为 0-100% 宽度<br>3. 每个维度显示原始分数、权重和加权得分（如 0.95 × 0.25 = 0.2375）<br>4. 各维度颜色与定义一致<br>5. 加权得分之和显示在底部，≈ confidence<br>6. 组件测试覆盖展开/收起和数值显示 |
| **依赖任务** | MR-T3.2（需要完整 score_breakdown）/ MR-T4.2 |
| **推荐顺序** | 11 |

---

### Task 4.4: 手动覆盖模型 UI（备用模型选择 + 确认）

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T4.4 |
| **story_id** | US-MR-03 |
| **任务类型** | frontend |
| **文件** | `src/components/ModelOverrideModal.tsx`、`src/hooks/useModelRouter.ts` |
| **任务说明** | 1. 点击 RoutingResultCard 的 [切换模型] 后，弹出 ModelOverrideModal<br>2. Modal 展示备用模型列表（从 backup_model_ids 获取），每行显示模型名、Provider、置信度、额度状态<br>3. LIMITED 的备用模型显示为禁用状态，不可选<br>4. 用户选择模型后，显示确认信息 "将切换至模型 X，原推荐模型为 Y"<br>5. 确认后调用 `POST /router/override-model`<br>6. 成功后 WorkerBadge 更新为新模型名，显示 toast "已切换至模型 X" |
| **完成标准** | 1. 备用模型列表正确展示，包含模型名和额度状态<br>2. LIMITED 的模型不可选，显示红色标签<br>3. 选择后确认信息正确<br>4. API 调用成功后 WorkerBadge 平滑过渡到新模型名（300ms）<br>5. 覆盖后 ExecutionLog 中可看到 model_override 事件<br>6. 组件测试覆盖选择、确认、取消流程 |
| **依赖任务** | MR-T3.3 / MR-T4.2 |
| **推荐顺序** | 12 |

---

## Feature 5: 路由规则配置页面（P1）

> 对应 Story: US-MR-06
> 说明：P1 功能，仅查看当前规则配置，MVP 阶段不开放编辑。

### Task 5.1: GET /router/rules API

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T5.1 |
| **story_id** | US-MR-06 |
| **任务类型** | backend |
| **文件** | `src/routes/router.ts` |
| **任务说明** | 1. 实现 `GET /router/rules` 接口<br>2. 返回当前路由规则：weights（6 个维度权重）、hard_constraints（硬约束列表）、model_capability_map（模型能力标签映射）、role_preference_map（角色偏好映射）<br>3. 数据从 Task 1.2 的 hard-code 配置中读取 |
| **完成标准** | 1. 返回 200 + 完整规则配置 JSON<br>2. weights 包含全部 6 个维度，值在 0-1 之间，总和 ≈ 1.0<br>3. hard_constraints 以可读字符串列表返回<br>4. model_capability_map 包含已配置的全部模型 |
| **依赖任务** | MR-T1.2 |
| **推荐顺序** | 13（P1，延后） |

---

### Task 5.2: RouterRulesPage 前端

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T5.2 |
| **story_id** | US-MR-06 |
| **任务类型** | frontend |
| **文件** | `src/pages/RouterRulesPage.tsx` |
| **任务说明** | 1. 实现 RouterRulesPage 页面，路由 `/router/rules`<br>2. 展示权重配置表格（维度名、权重值、可视化进度条）<br>3. 展示硬约束列表（以标签/卡片形式）<br>4. 展示模型能力标签映射表（模型名 → 能力标签列表）<br>5. 仅只读展示，MVP 不开放编辑 |
| **完成标准** | 1. 页面正确展示权重表格，总和显示在底部<br>2. 硬约束以清晰的可读形式展示<br>3. 模型能力标签以彩色标签展示<br>4. 对接 `GET /router/rules` 真实数据 |
| **依赖任务** | MR-T5.1 |
| **推荐顺序** | 14（P1，延后） |

---

## Feature 6: 测试与质量保障

> 覆盖全部 P0 故事的测试矩阵。

### Task 6.1: 评分引擎单元测试

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T6.1 |
| **story_id** | US-MR-01 / US-MR-04 / US-MR-05 |
| **任务类型** | test |
| **文件** | `tests/router/score-engine.test.ts`、`tests/router/candidate-filter.test.ts` |
| **任务说明** | 1. 候选池筛选测试：正常过滤 / 全部 LIMITED / 混合状态 / disabled 排除<br>2. 简单评分测试：代码任务优先代码模型 / 规划任务优先长上下文模型 / 无匹配时的降级<br>3. 完整 6 维度评分测试：每个维度独立测试输入输出<br>4. 加权求和测试：验证 confidence = Σ(分数 × 权重)<br>5. 边界测试：空候选池 / 单个候选 / 全部同分 |
| **完成标准** | 1. 候选池筛选测试覆盖率 100%<br>2. 6 个维度评分函数都有独立单元测试<br>3. 加权求和误差 < 0.001<br>4. 测试覆盖率 ≥ 85% |
| **依赖任务** | MR-T2.1 / MR-T2.2 / MR-T2.3 |
| **推荐顺序** | 15（与开发并行） |

---

### Task 6.2: API 集成测试

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T6.2 |
| **story_id** | US-MR-01 / US-MR-03 / US-MR-04 |
| **任务类型** | test |
| **文件** | `tests/router.api.test.ts` |
| **任务说明** | 1. `POST /router/select-model` — 正常路由 / 代码任务 / 规划任务 / 全部 LIMITED(503) / 缺少参数(400)<br>2. `POST /router/override-model` — 正常覆盖 / 非法 model_id(400) / LIMITED 模型(400) / 不在 backup 中(400)<br>3. `GET /router/rules` — 正常返回 / 字段完整性验证 |
| **完成标准** | 1. 全部 3 个 API 的 happy path 和主要错误 path 都有测试<br>2. 每个 API 至少 4 个测试用例<br>3. 数据库状态在每次测试后正确清理<br>4. 503 all_models_limited 时返回体结构正确 |
| **依赖任务** | MR-T3.1 / MR-T3.3 / MR-T5.1 |
| **推荐顺序** | 16（与开发并行） |

---

### Task 6.3: 前端组件测试

| 属性 | 值 |
|------|-----|
| **task_id** | MR-T6.3 |
| **story_id** | US-MR-02 / US-MR-03 / US-MR-05 |
| **任务类型** | test |
| **文件** | `tests/components/RoutingResultCard.test.tsx`、`tests/components/ScoreBreakdownPanel.test.tsx`、`tests/components/ModelOverrideModal.test.tsx` |
| **任务说明** | 1. RoutingResultCard：渲染、置信度条、risk flag 展示、自动收起、接受/切换按钮点击<br>2. ScoreBreakdownPanel：6 维度渲染、展开/收起、数值计算、颜色验证<br>3. ModelOverrideModal：备用列表渲染、LIMITED 禁用、选择确认、API 调用 |
| **完成标准** | 1. 全部 3 个组件有独立测试文件<br>2. 每个组件覆盖主要渲染状态和用户交互<br>3. 快照测试覆盖关键 UI 状态 |
| **依赖任务** | MR-T4.1 / MR-T4.3 / MR-T4.4 |
| **推荐顺序** | 17（与开发并行） |

---

## 推荐开发顺序

```
Phase 1 — 数据结构 + 简单路由 API（1 周）
  MR-T1.1  定义模型能力标签与 Routing 数据结构
  MR-T1.2  定义路由规则配置（权重 + 硬约束）
  MR-T2.1  候选池筛选（硬约束过滤）
  MR-T2.2  简单评分实现（规则匹配，让 API 先跑通）
  MR-T3.1  POST /router/select-model（接入简单评分）
  MR-T6.1  评分引擎单元测试（与开发并行）

Phase 2 — Workspace 可视化（3-4 天）
  MR-T4.1  RoutingResultCard（mock 数据）
  MR-T4.2  对接真实 API + 卡片交互
  MR-T6.2  API 集成测试（与开发并行）

Phase 3 — 完整评分 + 覆盖（3-4 天）
  MR-T2.3  完整 6 维度评分算法
  MR-T3.2  升级 select-model 为完整评分
  MR-T3.3  POST /router/override-model
  MR-T4.3  评分拆解矩阵 UI
  MR-T4.4  手动覆盖模型 UI
  MR-T6.3  前端组件测试（与开发并行）

Phase 4 — P1 规则页面（2 天，可选）
  MR-T5.1  GET /router/rules API
  MR-T5.2  RouterRulesPage
```

---

## 按 Phase 排期的任务看板

### Phase 1 — 数据结构 + 简单路由 API（1 周）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| MR-T1.1 | 模型能力标签 + Routing 数据结构 | backend | 无 | MR-01/05/06 |
| MR-T1.2 | 路由规则配置（权重 + 硬约束） | backend | MR-T1.1 | MR-01/05/06 |
| MR-T2.1 | 候选池筛选（排除 LIMITED/disabled） | backend | MR-T1.2 | MR-04 |
| MR-T2.2 | 简单评分（规则匹配，API 可运行） | backend | MR-T2.1 | MR-01 |
| MR-T3.1 | POST /router/select-model（简单评分版） | backend | MR-T2.2 | MR-01/04/05 |
| MR-T6.1 | 评分引擎单元测试 | test | MR-T2.x | MR-01/04/05 |

**Phase 1 交付物：** `POST /router/select-model` 可运行，返回推荐模型、置信度、备用模型列表，支持额度排除。前端可用 mock 数据独立开发卡片 UI。

### Phase 2 — Workspace 可视化（3-4 天）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| MR-T4.1 | RoutingResultCard 组件（mock） | frontend | 无 | MR-02 |
| MR-T4.2 | 对接真实 API + 交互 | frontend | MR-T3.1 | MR-02 |
| MR-T6.2 | API 集成测试 | test | MR-T3.1 | MR-01/03/04 |

**Phase 2 交付物：** Workspace 中 Task 分配时自动弹出路由决策卡片，显示推荐模型和置信度，用户可点击接受。

### Phase 3 — 完整评分 + 覆盖（3-4 天）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| MR-T2.3 | 完整 6 维度评分算法 | backend | MR-T2.2 | MR-01/05 |
| MR-T3.2 | 升级 select-model 为完整评分 | backend | MR-T2.3 | MR-01/05 |
| MR-T3.3 | POST /router/override-model | backend | MR-T3.1 | MR-03 |
| MR-T4.3 | 评分拆解矩阵 UI | frontend | MR-T3.2 | MR-05 |
| MR-T4.4 | 手动覆盖模型 UI | frontend | MR-T3.3 | MR-03 |
| MR-T6.3 | 前端组件测试 | test | MR-T4.x | MR-02/03/05 |

**Phase 3 交付物：** 完整的 6 维度评分算法、评分拆解展示、手动覆盖模型功能。

### Phase 4 — P1 规则页面（2 天，可选）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| MR-T5.1 | GET /router/rules API | backend | MR-T1.2 | MR-06 |
| MR-T5.2 | RouterRulesPage | frontend | MR-T5.1 | MR-06 |

**Phase 4 交付物：** 独立的路由规则查看页面，展示权重和约束配置。

---

## 风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| 6 维度评分算法过于复杂，开发周期长 | Phase 3 延迟 | Task 2.2 先提供简单评分，让 API 在 Phase 1 就能跑通；Task 2.3 的完整算法可延后迭代 |
| 模型能力标签和定价需要持续维护 | 评分结果不准确 | MVP 阶段 hard-code 标签和定价，后续通过实际使用数据校准 |
| Quota Manager 未就绪，quota_health 无数据来源 | quota_health 维度失效 | Task 2.1 的硬过滤已排除 LIMITED 模型；Task 2.3 中 quota_health 先用 mock 值（normal=1.0），等 Quota Manager 就绪后接入真实数据 |
| WorkerSession 创建依赖其他模块 | override-model 无法创建 Worker | Task 3.3 中 Worker 创建先用最小实现（仅记录 model_id），等 Worker 模块就绪后补全 |
| 前端需要 Model 列表数据 | ModelOverrideModal 的备用模型信息不全 | 从 RoutingResult 的 backup_model_ids 获取基本信息，不额外调用 Model API |

---

## Story → Task 映射表

| Story | 涉及 Task | 是否完整覆盖 |
|-------|-----------|--------------|
| US-MR-01 自动路由选择模型 | MR-T1.1 / MR-T1.2 / MR-T2.1 / MR-T2.2 / MR-T2.3 / MR-T3.1 / MR-T3.2 | 是 |
| US-MR-02 查看路由决策详情 | MR-T3.1 / MR-T4.1 / MR-T4.2 | 是 |
| US-MR-03 手动覆盖路由决策 | MR-T3.3 / MR-T4.4 | 是 |
| US-MR-04 额度不足模型自动排除 | MR-T2.1 / MR-T3.1 | 是 |
| US-MR-05 查看评分拆解矩阵 | MR-T1.2 / MR-T2.3 / MR-T3.2 / MR-T4.3 | 是 |
| US-MR-06 查看路由规则配置 | MR-T1.2 / MR-T5.1 / MR-T5.2 | 是 |

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
>
> 相关文档：
> - `docs/stories/model-router-stories.md` — 用户故事来源
> - `docs/prd/model-router-prd.md` — 产品需求
> - `docs/architecture/数据结构与数据库Schema.md` — Schema 定义
