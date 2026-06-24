# Model Router 技术型 PRD

> 所属产品：ModelGate Agent Studio
>
> 所属阶段：MVP-A / MVP-B 核心模块
>
> 文档定位：Model Router 的产品与技术需求说明，用于任务级模型智能调度、路由解释、备用模型选择和额度感知。

---

## 1. 功能背景

ModelGate Agent Studio 区别于普通多 API 工具的核心能力之一是：系统不是让用户手动切换模型，而是根据任务特征自动选择最合适的模型。

当一个 Goal 被拆解成多个 Task 后，每个 Task 的类型、复杂度、上下文长度、所需能力都不相同。不同模型在不同任务上的表现也差异巨大：

- Claude 擅长复杂规划和长上下文理解
- GPT-4 擅长通用任务和工具调用
- DeepSeek Coder 擅长代码生成
- Kimi 擅长超长文档阅读
- GLM 擅长中文场景和视觉理解

如果让用户手动为每个 Task 选择模型，操作成本高、容易选错、上下文管理混乱。Model Router 的目标是把"手动选模型"变成"自动路由"：

```text
Task 特征 + Agent 角色 + 模型能力 + 额度状态
↓
Model Router 评分计算
↓
推荐模型 + 备用模型 + 路由理由 + 置信度 + 风险提示
↓
Runtime 调用模型
↓
Workspace 展示路由决策
```

Model Router 不是简单的 if-else 规则，而是一套基于规则引擎 + 加权评分的路由系统。MVP 阶段用规则 + 分数即可，不需要复杂 ML，但必须为后续模型表现学习预留扩展口。

---

## 2. 用户问题

### 2.1 主要用户

- 多模型重度使用的开发者
- 同时使用多个 AI Coding Plan 或 API 的开发者
- 需要长时间推进复杂任务的独立开发者 / AI 产品经理 / 研究者

### 2.2 用户痛点

#### 痛点一：手动选模型效率低

用户同时拥有 Claude、GPT、DeepSeek、Kimi 等多个模型，每次执行不同任务时：

- 需要自己判断哪个模型更适合当前任务。
- 需要复制粘贴上下文到不同平台。
- 需要手动管理每个模型的额度。
- 选错模型后，输出质量差，需要重新来。

#### 痛点二：模型能力不透明

用户不清楚：

- 当前模型是否支持代码生成。
- 当前模型是否支持工具调用。
- 当前模型上下文窗口够不够。
- 当前模型对特定任务的擅长程度。

#### 痛点三：额度管理不可控

用户无法预知：

- 当前模型还剩多少额度。
- 任务执行到一半模型额度不足怎么办。
- 哪个备用模型可以无缝接手。
- 交接后上下文会不会丢失。

#### 痛点四：路由决策不可解释

即使系统推荐了某个模型，用户也想知道：

- 为什么选这个模型而不是另一个。
- 这个模型的优势和劣势是什么。
- 有没有更好的选择。
- 如果推荐错了，能不能手动覆盖。

### 2.3 核心问题

Model Router 要回答的问题是：

> 给定一个 Task 的特征、Agent 的角色、可用模型的能力和额度状态，系统如何选择最合适的模型，并让用户理解和信任这个选择？

---

## 3. 产品目标

### 3.1 核心目标

1. 根据 Task 类型、复杂度、所需能力自动判断路由需求。
2. 根据 Agent 角色和默认模型偏好进行初步筛选。
3. 根据模型能力标签评估模型匹配度。
4. 根据上下文长度排除窗口不足的模型。
5. 根据成本和速度偏好调整评分权重。
6. 根据额度状态降低或排除不可用模型。
7. 生成结构化路由结果：推荐模型 + 备用模型 + 路由理由 + 置信度 + 风险提示。
8. 支持用户手动覆盖推荐结果。
9. 路由决策在 Workspace 中可展示、可解释。
10. 路由失败时有明确的降级策略。

### 3.2 非目标

当前阶段不追求：

- 复杂 ML 模型自动学习路由策略。
- 实时市场模型价格比较和自动竞价。
- 多模型并行调用后自动选择最佳结果。
- 完全自动无人工干预的路由（必须可解释、可覆盖）。
- 跨平台模型性能实时监控。

### 3.3 成功判断

Model Router 成功的标志：

> 系统为一个 Task 推荐模型时，用户可以在 Agent Detail 或 Task Detail 中看到"为什么选这个模型"的清晰理由，并且当推荐不合适时，用户可以手动切换到其他模型或备用模型。

---

## 4. 路由输入

Model Router 的输入是一个结构化的路由请求，包含任务特征、Agent 偏好、用户偏好和系统状态。

### 4.1 输入对象

```typescript
interface RoutingRequest {
  // 任务标识
  task_id: string;
  goal_id: string;

  // 任务特征
  task_type: TaskType;
  task_complexity: ComplexityLevel;
  task_description: string;
  required_capabilities: ModelCapability[];

  // Agent 偏好
  preferred_agent_id: string;
  preferred_model_id?: string; // 用户手动指定时传入

  // 上下文估计
  context_length_estimate: number; // 预估 token 数
  has_vision_input: boolean;
  requires_tool_calling: boolean;

  // 用户偏好
  budget_preference: 'low' | 'medium' | 'high' | 'unlimited';
  speed_preference: 'fast' | 'balanced' | 'quality';

  // 系统状态
  quota_status: QuotaStatus[];

  // 历史表现（MVP-B 及以后）
  model_performance_hint?: ModelPerformanceHint;
}

type TaskType =
  | 'planning'
  | 'coding'
  | 'review'
  | 'research'
  | 'summarization'
  | 'supervision'
  | 'debugging'
  | 'documentation'
  | 'testing'
  | 'general';

type ComplexityLevel = 'simple' | 'moderate' | 'complex' | 'very_complex';

type ModelCapability =
  | 'code'
  | 'vision'
  | 'tool_calling'
  | 'long_context'
  | 'planning'
  | 'reasoning'
  | 'summarization'
  | 'fast'
  | 'low_cost';

interface QuotaStatus {
  model_id: string;
  token_usage_percent: number;
  request_usage_percent: number;
  status: 'normal' | 'warning' | 'blocked';
}

interface ModelPerformanceHint {
  model_id: string;
  success_rate: number;
  average_latency_ms: number;
  average_tokens_used: number;
}
```

### 4.2 输入来源

| 字段 | 来源 |
|------|------|
| task_id, goal_id | Task 对象 |
| task_type | Planner 拆解时标注，或 Router Agent 判断 |
| task_complexity | Router Agent 判断，或基于 Task 描述分析 |
| required_capabilities | AgentStation 配置 + Task 类型推导 |
| preferred_agent_id | Task.assigned_agent_id |
| preferred_model_id | 用户手动指定（覆盖） |
| context_length_estimate | 基于 Goal + Task 历史上下文估算 |
| has_vision_input | Task 描述或附件分析 |
| requires_tool_calling | AgentStation.allowed_tools 非空 |
| budget_preference | Goal 运行配置或用户全局偏好 |
| speed_preference | Goal 运行配置或用户全局偏好 |
| quota_status | Quota Manager 实时查询 |
| model_performance_hint | Model Performance Service（MVP-B） |

---

## 5. 路由输出

### 5.1 输出对象

```typescript
interface RoutingResult {
  // 推荐结果
  selected_model_id: string;
  selected_agent_id: string;

  // 备用方案
  backup_model_ids: string[];
  backup_agent_ids?: string[];

  // 解释与评估
  routing_reason: RoutingReason;
  confidence: number; // 0-1
  risk_flags: RiskFlag[];

  // 评分详情（用于展示和调试）
  score_breakdown: ScoreBreakdown[];

  // 用户覆盖信息
  is_user_override: boolean;
  override_note?: string;
}

interface RoutingReason {
  summary: string; // 一句话总结，如 "Claude 3 Opus 被选为编码任务的首选模型"
  primary_factors: string[]; // 主要决策因素
  secondary_factors: string[]; // 次要决策因素
  quota_impact?: string; // 额度影响说明
  tradeoffs: string[]; // 权衡说明
}

interface RiskFlag {
  type: 'quota_warning' | 'context_limit' | 'cost_high' | 'speed_slow' | 'untested_model' | 'low_confidence';
  severity: 'low' | 'medium' | 'high';
  message: string;
  suggestion?: string;
}

interface ScoreBreakdown {
  model_id: string;
  model_name: string;
  total_score: number;
  dimension_scores: DimensionScore[];
}

interface DimensionScore {
  dimension: string;
  score: number; // 0-100
  weight: number; // 0-1
  weighted_score: number;
  reason: string;
}
```

### 5.2 输出使用方

| 字段 | 使用方 |
|------|--------|
| selected_model_id | Runtime（调用模型）、Workspace（展示 WorkerBadge） |
| selected_agent_id | Runtime（确认 Agent 分配）、Workspace（展示 Agent Station） |
| backup_model_ids | Handoff Manager（备用模型选择）、Runtime（失败重试） |
| routing_reason | Workspace（Agent Detail / Task Detail 展示） |
| confidence | Workspace（展示路由可信度） |
| risk_flags | Workspace（展示风险提示）、Runtime（决策参考） |
| score_breakdown | Workspace（调试/详情展示）、Log（记录路由决策） |

---

## 6. 路由规则设计

### 6.1 路由流程

```text
RoutingRequest
↓
Step 1: 硬约束筛选（排除法）
  - 额度 blocked 的模型 → 排除
  - 未启用的模型 → 排除
  - 上下文窗口不足的模型 → 排除
  - 不支持必需能力的模型 → 排除
  - Agent 配置中不允许的模型 → 排除
↓
Step 2: Agent 默认模型优先
  - 如果 Agent.default_model_id 通过硬约束 → 进入评分
  - 如果 Agent.default_model_id 被排除 → 标记为不可用
↓
Step 3: 多维度评分
  - 能力匹配度
  - Agent 角色匹配度
  - 成本适配度
  - 速度适配度
  - 额度健康度
  - 上下文适配度
  - 历史表现（MVP-B）
↓
Step 4: 权重调整
  - 根据 budget_preference 调整成本权重
  - 根据 speed_preference 调整速度权重
  - 根据 task_complexity 调整能力权重
↓
Step 5: 排序与选择
  - 按总分排序
  - 选最高分作为 selected_model
  - 选第 2-3 名作为 backup_models
↓
Step 6: 生成路由理由
  - 总结主要决策因素
  - 生成风险提示
  - 计算置信度
↓
RoutingResult
```

### 6.2 硬约束规则

| 约束条件 | 排除逻辑 |
|----------|----------|
| 模型未启用 | `is_enabled === false` → 排除 |
| 额度 blocked | `quota_status === 'blocked'` → 排除 |
| 上下文不足 | `context_window < context_length_estimate * 1.2` → 排除 |
| 不支持必需能力 | 必需能力不在 `capability_tags` 中 → 排除 |
| Agent 配置限制 | 模型不在 Agent 允许列表中 → 排除 |
| 用户手动指定 | `preferred_model_id` 存在且有效 → 直接选用，跳过评分 |

### 6.3 软约束评分维度

| 维度 | 说明 | 评分方式 |
|------|------|----------|
| 能力匹配度 | 模型能力标签与任务所需能力的匹配程度 | 匹配能力数 / 所需能力数 * 100 |
| 角色匹配度 | 模型历史在同类 Agent 角色上的表现 | 规则匹配 + 历史表现（MVP-B） |
| 成本适配度 | 模型成本等级与用户预算偏好的匹配 | 成本越低分数越高，按 budget_preference 调整 |
| 速度适配度 | 模型速度等级与用户速度偏好的匹配 | 速度越快分数越高，按 speed_preference 调整 |
| 额度健康度 | 模型当前额度使用比例 | 使用率越低分数越高 |
| 上下文适配度 | 模型上下文窗口与任务需求的匹配 | 窗口越大、余量越多分数越高 |
| 历史表现（MVP-B） | 模型在同类任务上的成功率、延迟、token 效率 | 成功率越高分数越高 |

---

## 7. 路由评分机制

### 7.1 评分公式

MVP 阶段使用加权评分：

```text
total_score = Σ(dimension_score_i * dimension_weight_i)
```

### 7.2 默认权重配置

```typescript
const DEFAULT_WEIGHTS = {
  capability_match: 0.25,
  role_match: 0.20,
  context_fit: 0.15,
  cost_fit: 0.15,
  speed_fit: 0.10,
  quota_health: 0.10,
  historical_performance: 0.05, // MVP-B 启用
};
```

### 7.3 权重动态调整

根据用户偏好调整：

| 偏好 | 调整方式 |
|------|----------|
| budget_preference = 'low' | cost_fit 权重 +0.10，capability_match -0.05 |
| budget_preference = 'high' | cost_fit 权重 -0.05，capability_match +0.05 |
| speed_preference = 'fast' | speed_fit 权重 +0.10，capability_match -0.05 |
| speed_preference = 'quality' | capability_match 权重 +0.10，speed_fit -0.05 |
| task_complexity = 'very_complex' | capability_match +0.10，cost_fit -0.05 |
| task_complexity = 'simple' | cost_fit +0.05，capability_match -0.05 |

### 7.4 各维度评分细则

#### 能力匹配度（capability_match）

```text
required_capabilities = ['code', 'reasoning']
model_capabilities = ['code', 'planning', 'reasoning', 'long_context']

匹配数 = 2（code + reasoning）
所需能力数 = 2
匹配度 = 2 / 2 = 100%

如果模型缺少必需能力 → 硬约束排除
```

#### 角色匹配度（role_match）

MVP 阶段使用规则映射：

```typescript
const ROLE_MODEL_PREFERENCES = {
  planner: ['claude-3-opus', 'gpt-4-turbo', 'deepseek-chat'],
  coder: ['deepseek-coder', 'claude-3-opus', 'gpt-4-turbo'],
  reviewer: ['gpt-4-turbo', 'claude-3-opus'],
  researcher: ['kimi-long-context', 'claude-3-opus'],
  summarizer: ['claude-3-haiku', 'gpt-3.5-turbo', 'deepseek-chat'],
  supervisor: ['claude-3-opus', 'gpt-4-turbo'],
};

// 模型在角色偏好列表中的排名决定基础分
// 第1名 = 100分，第2名 = 85分，第3名 = 70分，未在列表 = 50分
```

MVP-B 阶段加入历史表现：

```text
role_match_score = base_score * 0.7 + historical_success_rate * 0.3
```

#### 上下文适配度（context_fit）

```text
context_margin = model_context_window - context_length_estimate
context_margin_ratio = context_margin / model_context_window

if context_margin_ratio > 0.5:
  score = 100
elif context_margin_ratio > 0.2:
  score = 80
elif context_margin_ratio > 0:
  score = 60
else:
  score = 0（硬约束排除）
```

#### 成本适配度（cost_fit）

```text
// cost_level: 1-5，1=最便宜，5=最贵
cost_score = (6 - cost_level) / 5 * 100

// budget_preference 调整
if budget_preference === 'low':
  cost_level > 3 的模型额外扣分
if budget_preference === 'high':
  cost_level < 3 的模型不额外加分（能力优先）
```

#### 速度适配度（speed_fit）

```text
// speed_level: 1-5，1=最快，5=最慢
speed_score = (6 - speed_level) / 5 * 100

// speed_preference 调整
if speed_preference === 'fast':
  speed_level > 3 的模型额外扣分
if speed_preference === 'quality':
  speed 权重降低，能力权重提高
```

#### 额度健康度（quota_health）

```text
if quota_status === 'normal':
  score = 100
elif quota_status === 'warning':
  score = 60 - token_usage_percent * 0.4
elif quota_status === 'blocked':
  score = 0（硬约束排除）
```

#### 历史表现（MVP-B）

```text
historical_score = success_rate * 100 * 0.6 + (1 - latency_normalized) * 100 * 0.4
```

### 7.5 置信度计算

```text
confidence = total_score_of_selected / total_score_of_best_possible

// 如果 selected 就是最高分 → confidence 接近 1.0
// 如果 selected 与第二名差距很小 → confidence 降低
// 如果存在 risk_flags → confidence 降低

if risk_flags.length > 0:
  confidence *= 0.9
if score_gap_to_second < 10:
  confidence *= 0.85
```

---

## 8. 模型能力标签设计

### 8.1 能力标签定义

| 标签 | 类型 | 说明 | 示例模型 |
|------|------|------|----------|
| `code` | boolean | 擅长代码生成和理解 | DeepSeek Coder, Claude 3 Opus |
| `vision` | boolean | 支持图像输入和理解 | GLM-4V, GPT-4V, Claude 3 |
| `tool_calling` | boolean | 支持函数/工具调用 | GPT-4, Claude 3, GLM-4 |
| `planning` | boolean | 擅长任务规划和拆解 | Claude 3 Opus, GPT-4 |
| `reasoning` | boolean | 擅长逻辑推理 | Claude 3 Opus, GPT-4, o1 |
| `summarization` | boolean | 擅长文本压缩和摘要 | Claude 3 Haiku, GPT-3.5 |
| `long_context` | boolean | 支持长上下文（>64k） | Kimi, Claude 3, GPT-4 |
| `fast` | boolean | 响应速度快 | Claude 3 Haiku, GPT-3.5 |
| `low_cost` | boolean | 成本低 | DeepSeek Chat, GLM-4 |
| `multilingual` | boolean | 多语言能力强 | GLM-4, Claude 3 |

### 8.2 模型数值属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `context_window` | number | 最大上下文长度（tokens） |
| `cost_level` | number | 成本等级 1-5 |
| `speed_level` | number | 速度等级 1-5 |
| `reasoning_level` | number | 推理能力等级 1-5 |
| `coding_level` | number | 代码能力等级 1-5 |
| `summarization_level` | number | 摘要能力等级 1-5 |
| `long_context_level` | number | 长上下文处理能力 1-5 |

### 8.3 标签与 Schema 的对齐

与现有 `docs/architecture/数据结构与数据库Schema.md` 中的 Model 表对齐：

```typescript
interface Model {
  id: string;
  provider: string;
  model_name: string;
  display_name: string;
  capability_tags: string[]; // 对应能力标签
  max_context_tokens: number; // 对应 context_window
  supports_vision: boolean;
  supports_code_interpreter: boolean;
  supports_function_calling: boolean; // 对应 tool_calling
  cost_level: number; // 1-5
  speed_level: number; // 1-5
  // 扩展字段（MVP-B）
  reasoning_level?: number;
  coding_level?: number;
  summarization_level?: number;
  long_context_level?: number;
}
```

---

## 9. Agent 与 Model 的匹配规则

### 9.1 Agent 配置对路由的影响

```text
AgentStation
├── default_model_id: 首选模型（路由时优先评分）
├── backup_model_ids: 备用模型列表（路由时纳入评分池）
├── allowed_tools: 决定是否需要 tool_calling 能力
├── system_prompt: 不影响路由，影响 Runtime 执行
├── output_format: 不影响路由，影响 Runtime 执行
└── max_steps_per_task: 不影响路由，影响 Runtime 执行
```

### 9.2 匹配规则

1. **默认模型优先**：Agent 的 default_model_id 如果通过硬约束，基础分加成 +15%。
2. **备用模型纳入**：Agent 的 backup_model_ids 全部纳入评分池。
3. **工具能力过滤**：如果 Agent.allowed_tools 非空，模型必须支持 tool_calling。
4. **角色偏好映射**：使用 ROLE_MODEL_PREFERENCES 为角色匹配度提供基础分。

### 9.3 用户覆盖规则

1. 如果 RoutingRequest 传入 `preferred_model_id`：
   - 检查该模型是否通过硬约束。
   - 如果通过，直接选用，标记 `is_user_override = true`。
   - 如果未通过，返回错误，提示用户选择其他模型。
2. 如果用户在 Workspace 中手动切换模型：
   - 新模型作为 `preferred_model_id` 传入。
   - 系统记录用户覆盖行为，用于后续学习（MVP-B）。

---

## 10. Quota Manager 对 Model Router 的影响

### 10.1 额度状态查询

Model Router 在路由前必须查询 Quota Manager：

```typescript
quota_status = QuotaManager.getStatus(model_id);
```

### 10.2 额度对路由的影响

| 额度状态 | 路由处理 |
|----------|----------|
| normal | 正常评分，无额外扣分 |
| warning | quota_health 分数降低，risk_flags 添加 `quota_warning` |
| blocked | 硬约束排除，不进入评分 |

### 10.3 额度预警与 Handoff 联动

当模型额度进入 warning 时：

1. Model Router 在评分中降低该模型分数。
2. 如果该模型仍是最高分，添加 `quota_warning` risk_flag。
3. Handoff Manager 可以根据 Agent.handoff_threshold_tokens 和 quota_status 建议 Handoff。
4. Runtime 执行前再次检查额度，如果已 blocked，触发 Handoff。

### 10.4 额度统计字段

```typescript
interface QuotaStatus {
  model_id: string;
  today_tokens_used: number;
  today_token_limit?: number;
  token_usage_percent: number;
  today_requests_used: number;
  today_request_limit?: number;
  request_usage_percent: number;
  status: 'normal' | 'warning' | 'blocked';
}
```

---

## 11. Handoff Manager 对 Model Router 的影响

### 11.1 Handoff 时的路由

当 Handoff Manager 需要选择接手模型时：

1. Handoff Manager 调用 Model Router，传入 Handoff 特有的 RoutingRequest。
2. RoutingRequest 中：
   - `preferred_agent_id` = 接手 Agent（可能与原 Agent 相同角色）。
   - `context_length_estimate` = Handoff Summary 的 token 数 + 任务剩余上下文。
   - `required_capabilities` = 原 Task 所需能力。
   - `quota_status` = 排除原模型（如果因额度交接）。
3. Model Router 排除原模型（如果 Handoff 原因是额度不足）。
4. Model Router 从 backup_model_ids 和全局模型中选择最佳接手模型。

### 11.2 Handoff 路由的特殊规则

1. **排除原模型**：如果 Handoff 原因是 quota_exceeded 或 error，排除 from_model。
2. **上下文压缩**：Handoff Summary 可能大幅降低 context_length_estimate，使更多模型可用。
3. **备用模型优先**：优先从 Agent.backup_model_ids 中选择。
4. **角色保持**：尽量保持相同角色，确保 system_prompt 和工具权限一致。

### 11.3 Handoff 后的路由记录

Handoff 完成后，Model Router 记录：

- from_model_id 和 to_model_id。
- Handoff 原因。
- 接手模型的路由理由。
- 用于后续模型表现分析（MVP-B）。

---

## 12. 前端展示设计

### 12.1 路由结果展示位置

路由决策需要在以下位置展示：

1. **Agent Detail Modal / Task Detail Panel**：展示当前任务为什么选这个模型。
2. **Workspace WorkerBadge**：展示当前 Worker 绑定的模型。
3. **Bottom Console**：记录路由决策日志。
4. **Models 页面**：展示模型能力和当前路由使用情况。

### 12.2 路由结果组件

#### RoutingResultCard

**职责**：展示单个路由决策的结果和理由。

**Props**：

```typescript
interface RoutingResultCardProps {
  result: RoutingResult;
  models: Model[];
  onOverride: (modelId: string) => void;
  onViewDetails: () => void;
}
```

**展示内容**：

```text
┌─────────────────────────────────────────┐
│ 🎯 模型路由决策                          │
│                                         │
│ 推荐模型: Claude 3 Opus                 │
│ 置信度: 92%                             │
│                                         │
│ 路由理由:                               │
│ • 编码任务优先选择代码能力强的模型        │
│ • Claude 3 Opus 在 Coder 角色中排名第1  │
│ • 上下文窗口充足（200K > 15K 预估）     │
│ • 额度健康（使用率 23%）                │
│                                         │
│ 权衡:                                   │
│ • 成本较高（level 5），但预算偏好为高质量 │
│                                         │
│ 备用模型:                               │
│ 1. DeepSeek Coder (score: 87)           │
│ 2. GPT-4 Turbo (score: 82)              │
│                                         │
│ ⚠️ 风险提示: 无                          │
│                                         │
│ [切换模型 ▼] [查看评分详情]              │
└─────────────────────────────────────────┘
```

#### ModelScoreBreakdown

**职责**：展示各模型在各维度的评分详情。

**展示内容**：

```text
模型评分详情

Claude 3 Opus     总分: 92
├─ 能力匹配  95/100  权重 0.25  加权 23.75
├─ 角色匹配  100/100 权重 0.20  加权 20.00
├─ 上下文适配 90/100  权重 0.15  加权 13.50
├─ 成本适配   70/100  权重 0.15  加权 10.50
├─ 速度适配   75/100  权重 0.10  加权 7.50
├─ 额度健康   95/100  权重 0.10  加权 9.50
└─ 历史表现   --      权重 0.05  加权 --

DeepSeek Coder    总分: 87
├─ 能力匹配  100/100 ...
├─ 角色匹配  85/100 ...
...
```

#### RiskFlagBanner

**职责**：展示路由风险提示。

**展示内容**：

```text
⚠️ 额度警告
Claude 3 Opus 今日 token 使用量已达 85%，建议关注额度或准备交接。

💡 建议：已自动将 DeepSeek Coder 设为备用模型。
```

### 12.3 用户覆盖交互

1. 用户在 RoutingResultCard 中点击「切换模型」。
2. 下拉列表展示所有通过硬约束的模型，按分数排序。
3. 用户选择新模型。
4. 系统记录覆盖行为，`is_user_override = true`。
5. Workspace 更新 WorkerBadge 为新模型。
6. Task 后续执行使用新模型。
7. 覆盖记录用于后续模型表现学习（MVP-B）。

---

## 13. 后端接口设计

### 13.1 路由请求接口

```http
POST /router/select-model
```

请求体：

```json
{
  "task_id": "task-uuid",
  "goal_id": "goal-uuid",
  "task_type": "coding",
  "task_complexity": "complex",
  "task_description": "实现前端登录页面组件",
  "required_capabilities": ["code", "reasoning"],
  "preferred_agent_id": "agent-coder",
  "preferred_model_id": null,
  "context_length_estimate": 15000,
  "has_vision_input": false,
  "requires_tool_calling": true,
  "budget_preference": "medium",
  "speed_preference": "quality"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "selected_model_id": "model-claude-opus",
    "selected_agent_id": "agent-coder",
    "backup_model_ids": ["model-deepseek-coder", "model-gpt-4"],
    "routing_reason": {
      "summary": "Claude 3 Opus 被选为编码任务的首选模型",
      "primary_factors": [
        "编码任务优先选择代码能力强的模型",
        "Claude 3 Opus 在 Coder 角色中排名第1"
      ],
      "secondary_factors": [
        "上下文窗口充足",
        "额度健康"
      ],
      "tradeoffs": [
        "成本较高，但预算偏好为高质量"
      ]
    },
    "confidence": 0.92,
    "risk_flags": [],
    "score_breakdown": [
      {
        "model_id": "model-claude-opus",
        "model_name": "Claude 3 Opus",
        "total_score": 92,
        "dimension_scores": [
          {
            "dimension": "capability_match",
            "score": 95,
            "weight": 0.25,
            "weighted_score": 23.75,
            "reason": "支持 code 和 reasoning 能力"
          }
        ]
      }
    ]
  }
}
```

### 13.2 用户覆盖接口

```http
POST /router/override-model
```

请求体：

```json
{
  "task_id": "task-uuid",
  "preferred_model_id": "model-deepseek-coder",
  "reason": "用户手动切换为 DeepSeek Coder"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "task_id": "task-uuid",
    "selected_model_id": "model-deepseek-coder",
    "is_user_override": true,
    "override_note": "用户手动切换为 DeepSeek Coder"
  }
}
```

### 13.3 路由规则配置接口（MVP-B）

```http
GET /router/rules
```

响应：

```json
{
  "success": true,
  "data": {
    "weights": {
      "capability_match": 0.25,
      "role_match": 0.20,
      "context_fit": 0.15,
      "cost_fit": 0.15,
      "speed_fit": 0.10,
      "quota_health": 0.10,
      "historical_performance": 0.05
    },
    "role_preferences": {
      "coder": ["deepseek-coder", "claude-3-opus", "gpt-4-turbo"]
    },
    "hard_constraints": [
      "model must be enabled",
      "model quota not blocked",
      "context window sufficient"
    ]
  }
}
```

### 13.4 更新路由权重（MVP-B）

```http
PATCH /router/rules/weights
```

请求体：

```json
{
  "capability_match": 0.30,
  "cost_fit": 0.10
}
```

---

## 14. 数据对象设计

### 14.1 RoutingRequest

```typescript
interface RoutingRequest {
  task_id: string;
  goal_id: string;
  task_type: TaskType;
  task_complexity: ComplexityLevel;
  task_description: string;
  required_capabilities: ModelCapability[];
  preferred_agent_id: string;
  preferred_model_id?: string;
  context_length_estimate: number;
  has_vision_input: boolean;
  requires_tool_calling: boolean;
  budget_preference: 'low' | 'medium' | 'high' | 'unlimited';
  speed_preference: 'fast' | 'balanced' | 'quality';
  quota_status: QuotaStatus[];
  model_performance_hint?: ModelPerformanceHint;
}
```

### 14.2 RoutingResult

```typescript
interface RoutingResult {
  selected_model_id: string;
  selected_agent_id: string;
  backup_model_ids: string[];
  backup_agent_ids?: string[];
  routing_reason: RoutingReason;
  confidence: number;
  risk_flags: RiskFlag[];
  score_breakdown: ScoreBreakdown[];
  is_user_override: boolean;
  override_note?: string;
}

interface RoutingReason {
  summary: string;
  primary_factors: string[];
  secondary_factors: string[];
  quota_impact?: string;
  tradeoffs: string[];
}

interface RiskFlag {
  type: 'quota_warning' | 'context_limit' | 'cost_high' | 'speed_slow' | 'untested_model' | 'low_confidence';
  severity: 'low' | 'medium' | 'high';
  message: string;
  suggestion?: string;
}

interface ScoreBreakdown {
  model_id: string;
  model_name: string;
  total_score: number;
  dimension_scores: DimensionScore[];
}

interface DimensionScore {
  dimension: string;
  score: number;
  weight: number;
  weighted_score: number;
  reason: string;
}
```

### 14.3 RoutingRuleConfig

```typescript
interface RoutingRuleConfig {
  weights: Record<string, number>;
  role_preferences: Record<string, string[]>;
  hard_constraints: string[];
  task_type_capabilities: Record<string, ModelCapability[]>;
  complexity_thresholds: Record<string, number>;
}
```

### 14.4 ModelPerformanceRecord（MVP-B）

```typescript
interface ModelPerformanceRecord {
  id: string;
  model_id: string;
  task_type: TaskType;
  agent_role: string;
  success: boolean;
  latency_ms: number;
  tokens_used: number;
  user_rating?: number;
  was_overridden: boolean;
  routing_confidence: number;
  created_at: Date;
}
```

---

## 15. 异常状态

### 15.1 所有模型被硬约束排除

触发条件：

- 所有可用模型额度 blocked。
- 所有模型上下文窗口不足。
- 所有模型缺少必需能力。

处理：

- RoutingResult 返回空。
- 返回错误码 `NO_ELIGIBLE_MODEL`。
- Workspace 展示错误提示："没有可用模型，请检查模型配置或额度"。
- 建议用户：
  1. 检查 Models 页面模型状态。
  2. 检查 Quota 页面额度状态。
  3. 添加新模型或调整任务需求。

### 15.2 默认模型被排除

触发条件：

- Agent.default_model_id 额度 blocked。
- Agent.default_model_id 上下文不足。

处理：

- Model Router 自动从 backup_model_ids 中选择最高分模型。
- RoutingReason 中说明"默认模型不可用，已自动选择备用模型"。
- risk_flags 添加 `default_model_unavailable`。
- Workspace 展示提示："默认模型不可用，已自动切换"。

### 15.3 额度在路由后变为 blocked

触发条件：

- 路由时模型额度正常，执行时额度耗尽。

处理：

- Runtime 调用失败。
- 触发 Handoff Manager。
- Handoff 时 Model Router 排除该模型。
- 从 backup_model_ids 中选择接手模型。

### 15.4 用户覆盖无效模型

触发条件：

- 用户选择 disabled 或 blocked 模型。

处理：

- API 返回 400，提示"该模型当前不可用"。
- 前端展示可用模型列表。

### 15.5 评分差距过小

触发条件：

- 第一名和第二名模型分数差距 < 5 分。

处理：

- confidence 降低。
- risk_flags 添加 `low_confidence`。
- RoutingReason 中说明"多个模型评分接近，建议关注表现"。

### 15.6 上下文估计不准确

触发条件：

- context_length_estimate 远低于实际 token 数。

处理：

- Runtime 实际调用时检测到上下文超限。
- 返回错误，触发 Handoff。
- Handoff Summary 压缩上下文。
- Model Router 重新路由到上下文更大的模型。

---

## 16. MVP 范围

### 16.1 MVP-A 必须实现

| 功能 | 说明 |
|------|------|
| 硬约束筛选 | 排除 disabled、blocked、窗口不足、能力缺失的模型 |
| 多维度评分 | 能力匹配、角色匹配、上下文适配、成本、速度、额度健康 |
| 权重动态调整 | 根据 budget/speed/complexity 调整权重 |
| 默认模型优先 | Agent.default_model_id 基础分加成 |
| 备用模型选择 | 选第 2-3 名作为 backup_models |
| 路由理由生成 | 返回结构化 routing_reason |
| 置信度计算 | 基于分数差距和风险标志计算 |
| 风险提示 | quota_warning、context_limit、cost_high 等 |
| 用户手动覆盖 | 支持 preferred_model_id 覆盖推荐 |
| 路由结果展示 | Agent Detail / Task Detail 展示路由决策 |
| 额度联动 | 路由前查询 Quota Manager |
| Handoff 联动 | Handoff 时排除原模型，重新路由 |

### 16.2 MVP-B 建议实现

| 功能 | 说明 |
|------|------|
| 历史表现评分 | 基于 ModelPerformanceRecord 调整分数 |
| 路由规则配置 | 支持调整权重和角色偏好 |
| 评分详情展示 | Workspace 展示完整 score_breakdown |
| 自动权重优化 | 基于历史表现微调权重（简单规则） |
| 路由日志 | 记录每次路由决策用于分析 |
| 批量路由 | 支持为多个 Task 批量选择模型 |

---

## 17. 暂缓范围

当前阶段明确不做：

1. **复杂 ML 模型**：不做神经网络自动学习路由策略。
2. **实时市场价格比较**：不做多平台实时竞价。
3. **多模型并行调用后选择**：不做同时调用多个模型然后选最佳结果。
4. **自动 A/B 测试路由策略**：不做自动对比不同路由规则的效果。
5. **跨平台模型性能监控**：不做实时监控所有接入模型的延迟和可用性。
6. **模型自动发现**：不做自动扫描和注册新模型。
7. **动态定价优化**：不做基于市场价格的动态路由。
8. **用户行为深度学习**：不做基于用户长期行为的复杂个性化路由。
9. **模型性能预测**：不做预测模型在未来任务上的表现。
10. **完全自动无干预路由**：所有路由决策必须可解释、可覆盖。

---

## 18. 验收标准

### 18.1 功能验收

1. Model Router 可以接收 RoutingRequest 并返回 RoutingResult。
2. 硬约束可以正确排除 disabled、blocked、窗口不足、能力缺失的模型。
3. Agent.default_model_id 如果有效，在评分中获得优先。
4. 多维度评分可以正确计算各模型的分数。
5. 权重可以根据 budget_preference、speed_preference、task_complexity 动态调整。
6. 额度状态可以正确影响模型评分（warning 扣分，blocked 排除）。
7. 路由结果包含 selected_model_id、backup_model_ids、routing_reason、confidence、risk_flags。
8. 用户可以通过 preferred_model_id 手动覆盖推荐结果。
9. Handoff 时 Model Router 可以排除原模型并选择接手模型。
10. 路由理由必须清晰可读，包含主要因素、次要因素和权衡说明。

### 18.2 前端验收

1. Agent Detail 或 Task Detail 中展示当前任务的路由决策和理由。
2. WorkerBadge 展示当前绑定的模型名。
3. RoutingResultCard 可以展示推荐模型、置信度、路由理由和风险提示。
4. 用户可以点击「切换模型」手动覆盖推荐。
5. 额度 warning 时，Workspace 展示风险提示。
6. 路由失败时，前端展示明确的错误提示和建议。

### 18.3 后端验收

1. `POST /router/select-model` 返回正确的 RoutingResult。
2. `POST /router/override-model` 支持用户手动覆盖。
3. 路由前自动查询 Quota Manager。
4. Handoff 时自动排除原模型。
5. 所有路由决策记录到 ExecutionLog。
6. 用户覆盖行为记录到数据库（用于后续学习）。

### 18.4 数据验收

1. RoutingRequest 包含所有必需字段。
2. RoutingResult 包含所有必需字段。
3. ScoreBreakdown 包含每个模型的各维度评分。
4. RiskFlag 包含类型、严重程度和消息。
5. 用户覆盖记录包含 task_id、原模型、新模型、覆盖原因。

### 18.5 集成验收

1. Runtime 在执行 Task 前调用 Model Router 获取模型。
2. Model Router 的结果被 Workspace 正确展示。
3. Handoff Manager 在交接时调用 Model Router 选择接手模型。
4. Quota Manager 的额度变化实时影响 Model Router 评分。
5. Agent Registry 的 Agent 配置被 Model Router 正确读取。

### 18.6 Demo 验收

必须能稳定演示以下流程：

```text
1. 用户输入 Goal："帮我设计一个前端登录页面"。
2. Planner 拆解出 Task："实现登录组件"。
3. Task 分配给 Coder Agent。
4. Model Router 接收 RoutingRequest：
   - task_type = coding
   - required_capabilities = [code, reasoning]
   - preferred_agent_id = Coder Agent
   - context_length_estimate = 8000
   - budget_preference = medium
   - speed_preference = quality
5. Model Router 排除额度 blocked 的模型。
6. Model Router 排除上下文不足的模型。
7. Model Router 计算各模型分数：
   - Claude 3 Opus: 92 分（角色匹配第1，能力匹配高）
   - DeepSeek Coder: 88 分（能力匹配最高，角色匹配第2）
   - GPT-4 Turbo: 85 分（能力匹配高，成本较高）
8. Model Router 选择 Claude 3 Opus 为 selected_model。
9. Model Router 选择 DeepSeek Coder 和 GPT-4 为 backup_models。
10. Workspace 的 Coder WorkerBadge 显示 "Claude 3 Opus"。
11. Agent Detail 展示路由理由：
    - "编码任务优先选择代码能力强的模型"
    - "Claude 3 Opus 在 Coder 角色中排名第1"
    - "上下文窗口充足"
12. 用户手动切换到 DeepSeek Coder。
13. WorkerBadge 更新为 "DeepSeek Coder"。
14. 系统记录用户覆盖行为。
15. Claude 3 Opus 额度达到 warning。
16. 下一个 Task 的路由中，Claude 分数降低，DeepSeek Coder 分数提升。
17. 如果 Claude 被 blocked，系统自动从 backup_models 中选择。
```

如果上述流程可稳定跑通，Model Router MVP 即视为完成。
