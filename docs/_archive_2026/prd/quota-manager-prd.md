# Quota Manager 技术型 PRD

> 所属产品：ModelGate Agent Studio
>
> 所属阶段：MVP-A / MVP-B 核心能力
>
> 文档定位：Quota Manager 的产品与技术需求说明，作为额度记录、估算、风险判断和联动触发的实现依据。

---

## 1. 功能背景

ModelGate Agent Studio 面向拥有多个 AI Coding Plan 和多模型 API 的开发者。用户经常遇到模型额度突然用完、上下文中断、任务无法继续的问题。

Quota Manager 负责记录不同模型的使用状态，预估剩余额度，并在模型接近限制时触发 Handoff 或模型切换。

在多模型 Agent 协作平台中，额度管理不是可选的"成本监控"，而是任务连续性的基础设施：

- 任务执行到一半，模型额度耗尽，必须不中断地切换到备用模型。
- 多个 Agent Station 共享同一模型时，必须知道哪个 Worker 正在消耗哪个模型的额度。
- 用户需要看到实时额度状态，才能判断当前路由决策是否合理。
- 系统需要基于额度状态调整路由策略，避免把任务分配给即将耗尽的模型。

```text
Runtime 调用模型 API
↓
Quota Manager 记录调用次数 + token 使用量
↓
估算剩余额度 + 更新 quota_status
↓
风险判断：normal / warning / near_limit / limited / cooldown / unknown
↓
触发联动：
  → Model Router：降低该模型评分，推荐备用模型
  → Handoff Manager：生成交接摘要，切换到新 Worker
  → Workspace：更新 Risk Badge，提示用户
```

Quota Manager 的核心价值是：**额度不足时不中断任务**。

---

## 2. 用户问题

### 2.1 主要用户

- 多模型重度使用的开发者
- 使用多个 AI Coding Plan 或 API 的开发者
- 需要长时间推进复杂任务的独立开发者 / AI 产品经理 / 研究者

### 2.2 用户痛点

#### 痛点一：额度突然用完，任务中断

用户拥有 Claude、OpenAI、DeepSeek、Kimi 等多个模型的 API Key 或 Coding Plan，但无法实时知道每个模型的剩余额度。任务执行到关键步骤时，API 返回 429 / 403 / "insufficient_quota"，任务被迫中断。

- 已完成的工作无法自动保存到上下文。
- 用户需要手动复制粘贴到新模型重新执行。
- 丢失任务进度和中间决策。

#### 痛点二：不知道哪个模型快用完了

用户通常管理多个平台的额度：

- OpenAI：按 token 计费，有月度上限
- Anthropic：按 message 计费，有 rate limit
- DeepSeek：按 token 计费，有并发限制
- 其他平台：各有不同的计费单位和限制规则

用户无法在一个地方看到所有模型的使用情况和剩余额度。

#### 痛点三：额度不足时不知道切到哪个模型

当一个模型额度不足时，用户需要：

- 手动检查其他模型的额度是否充足。
- 手动判断哪个备用模型适合继续当前任务。
- 手动复制上下文并重新发起请求。

这个过程中，任务上下文丢失、时间浪费、用户焦虑。

#### 痛点四：无法读取真实额度时的焦虑

很多平台（尤其是 Coding Plan）不提供实时额度查询 API。用户只能凭感觉估算，或者等报错才知道额度用完了。

### 2.3 核心问题

Quota Manager 要回答的问题是：

> 当系统无法读取真实额度时，如何基于使用记录、错误码和频率估算剩余额度，并在接近限制时自动触发模型切换，保证任务不中断？

---

## 3. 产品目标

### 3.1 核心目标

1. 记录每个模型的 API 调用次数和 token 使用量。
2. 支持手动填写额度上限，或基于使用记录做近似估算。
3. 根据错误码、使用频率和阈值判断模型的风险状态。
4. 在模型接近限制时，自动触发 Handoff 或向用户发出提醒。
5. 向 Model Router 提供额度状态，影响路由评分和推荐。

### 3.2 体验目标

- 用户能在 Workspace 的 Quota Overview 中一眼看到所有模型的额度状态。
- 额度不足时，系统主动提示并给出切换建议，用户无需手动操作。
- 用户能手动修正额度状态，覆盖系统自动估算。
- 所有额度状态变化都有历史记录，可追溯、可审计。

### 3.3 技术目标

- 每次 API 调用后实时更新使用记录（异步，不阻塞主流程）。
- 额度估算支持"已知上限"和"未知上限"两种模式。
- 风险状态判断基于可配置阈值，支持不同模型的差异化策略。
- 与 Handoff Manager、Model Router 的联动通过事件机制解耦。

---

## 4. 额度记录范围

### 4.1 记录维度

Quota Manager 对每个模型的每次 API 调用记录以下维度：

| 维度 | 说明 | 来源 |
|------|------|------|
| request_count | API 调用总次数 | Runtime 每次调用后计数 +1 |
| input_tokens | 输入 token 总量 | API 响应中的 usage.prompt_tokens |
| output_tokens | 输出 token 总量 | API 响应中的 usage.completion_tokens |
| total_tokens | 总 token 量（input + output） | 计算得出 |
| last_used_at | 最近一次调用时间 | 每次调用后更新 |
| limit_error_count | 额度/限制相关错误次数 | 错误码匹配后计数 |
| handoff_triggered_count | 因额度触发的 Handoff 次数 | Handoff Manager 回调后计数 |

### 4.2 错误码分类

额度/限制相关错误码（触发 limit_error_count +1）：

| 错误码 | 含义 | 状态影响 |
|--------|------|----------|
| 429 | Rate limit exceeded | cooldown |
| 429 (insufficient_quota) | 额度不足 | limited |
| 403 | Permission denied / quota exceeded | limited |
| 402 | Payment required | limited |
| 503 | Service unavailable (临时) | cooldown |
| 529 | Overloaded | cooldown |

非额度相关错误（不触发 limit_error_count）：400, 401, 422, 500 等。

### 4.3 记录粒度

- **MVP-A**：按 `provider + model_id` 粒度记录，同一模型所有 Agent Station 共享一条 QuotaRecord。
- **MVP-B**：支持按 `provider + model_id + api_key_id` 粒度记录，区分不同 API Key 的额度。
- **V1**：支持按 `provider + model_id + user_id` 粒度记录，支持多用户场景。

---

## 5. 额度估算规则

### 5.1 估算模式

Quota Manager 支持两种额度上限模式：

#### 模式 A：已知上限（User-Defined Quota）

用户手动填写或导入模型的额度上限：

```typescript
interface UserDefinedQuota {
  quota_type: 'token_limit' | 'request_limit' | 'cost_limit' | 'hybrid';
  token_limit?: number;        // 月度 token 上限
  request_limit?: number;      // 月度请求数上限
  cost_limit?: number;         // 月度费用上限（USD）
  reset_period: 'daily' | 'weekly' | 'monthly' | 'never';
  reset_date?: number;         // 每月几号重置（1-31）
}
```

- 适用于：OpenAI、Anthropic 等提供明确额度上限的平台。
- 优点：估算准确。
- 缺点：需要用户手动维护。

#### 模式 B：近似估算（System-Estimated Quota）

当用户无法提供真实额度上限时，系统基于历史使用记录做近似估算：

```typescript
interface EstimatedQuota {
  estimated_limit: number;     // 系统估算的上限
  confidence: number;          // 置信度（0-1）
  estimation_method: 'usage_trend' | 'error_frequency' | 'default_assumption';
}
```

估算方法：

1. **使用趋势法（usage_trend）**：
   - 统计最近 7 天的日均使用量。
   - 假设月度上限 = 日均使用量 × 30 × 波动系数（默认 1.5）。
   - 置信度 = min(1, 记录天数 / 14)。

2. **错误频率法（error_frequency）**：
   - 统计最近 limit_error_count 的增长频率。
   - 如果最近 24h 内出现 2 次以上额度错误，estimated_remaining 直接置为 0。
   - 置信度较低（0.3-0.5）。

3. **默认假设法（default_assumption）**：
   - 新模型无任何历史数据时，使用平台默认值。
   - 例如：OpenAI GPT-4 默认 1M tokens/月，Claude 默认 100K tokens/月。
   - 置信度最低（0.1），需要用户尽快手动修正。

### 5.2 剩余额度计算

```typescript
function calculateRemaining(record: QuotaRecord, mode: QuotaMode): number {
  if (mode === 'known') {
    return userDefinedQuota.token_limit - record.total_tokens;
  }
  if (mode === 'estimated') {
    return estimatedQuota.estimated_limit - record.total_tokens;
  }
  return -1; // unknown
}
```

### 5.3 使用速率计算

```typescript
function calculateUsageRate(record: QuotaRecord): UsageRate {
  const hoursSinceLastUse = (now - record.last_used_at) / 3600000;
  const tokensPerHour = record.total_tokens / max(hoursSinceLastUse, 1);
  const requestsPerHour = record.request_count / max(hoursSinceLastUse, 1);
  return { tokensPerHour, requestsPerHour };
}
```

---

## 6. 风险状态定义

### 6.1 QuotaStatus 枚举

```typescript
enum QuotaStatus {
  NORMAL = 'normal',           // 正常，无风险
  WARNING = 'warning',         // 注意，接近阈值
  NEAR_LIMIT = 'near_limit',   // 接近限制，建议准备切换
  LIMITED = 'limited',         // 已受限，当前不可用
  COOLDOWN = 'cooldown',       // 冷却中（rate limit），暂不可用
  UNKNOWN = 'unknown',         // 无数据，无法判断
}
```

### 6.2 状态判定规则

状态判定基于多个维度的阈值：

```typescript
interface QuotaThresholds {
  warning_percent: number;      // 默认 70%
  near_limit_percent: number;   // 默认 90%
  cooldown_minutes: number;     // 默认 1 分钟
  max_errors_per_hour: number;  // 默认 3
  max_rate_limit_errors: number; // 默认 2
}
```

判定优先级（从高到低）：

1. **LIMITED**：
   - 最近 1 小时内出现 `insufficient_quota` 或 `payment_required` 错误。
   - 或 remaining ≤ 0（已知上限模式）。
   - 或 estimated_remaining ≤ 0（估算模式，且置信度 > 0.5）。

2. **COOLDOWN**：
   - 最近 `cooldown_minutes` 内出现过 rate limit 错误（429）。
   - 或 cooldown_until > now。

3. **NEAR_LIMIT**：
   - 使用率 ≥ `near_limit_percent`（默认 90%）。
   - 或最近 1 小时内 limit_error_count ≥ `max_errors_per_hour`。

4. **WARNING**：
   - 使用率 ≥ `warning_percent`（默认 70%）。
   - 或最近 24 小时内出现过 1 次额度相关错误。

5. **NORMAL**：
   - 使用率 < `warning_percent`。
   - 且最近 24 小时无额度相关错误。

6. **UNKNOWN**：
   - 无历史使用记录。
   - 且用户未填写额度上限。
   - 且系统无法做默认假设。

### 6.3 使用率计算

```typescript
function calculateUsagePercent(record: QuotaRecord): number {
  if (record.quota_mode === 'known' && record.token_limit > 0) {
    return record.total_tokens / record.token_limit;
  }
  if (record.quota_mode === 'estimated' && record.estimated_limit > 0) {
    return record.total_tokens / record.estimated_limit;
  }
  return -1;
}
```

### 6.4 状态历史记录

每次 quota_status 变化时，系统写入一条状态历史记录：

```typescript
interface QuotaStatusHistory {
  history_id: string;
  quota_record_id: string;
  from_status: QuotaStatus;
  to_status: QuotaStatus;
  reason: string;               // 变化原因
  triggered_by: 'system' | 'user' | 'handoff' | 'router';
  usage_percent_at_change: number;
  total_tokens_at_change: number;
  request_count_at_change: number;
  limit_error_count_at_change: number;
  created_at: string;
}
```

---

## 7. Handoff 触发规则

### 7.1 自动触发条件

Quota Manager 在以下条件下自动触发 Handoff：

| 触发条件 | 状态 | Handoff 类型 | 说明 |
|----------|------|-------------|------|
| 使用率 ≥ 95% | NEAR_LIMIT | auto_quota_warning | 系统提示用户，建议切换 |
| 使用率 ≥ 100% 或 额度错误 | LIMITED | auto_quota_handoff | 自动触发 Handoff，切换到备用模型 |
| 最近 1h 内 429 ≥ 2 次 | COOLDOWN | auto_cooldown_handoff | 自动切换到非冷却模型 |
| 用户手动触发 | 任意 | manual_quota_handoff | 用户主动决定切换 |

### 7.2 触发流程

```text
Runtime API 调用返回错误
  ↓
Quota Manager 更新 limit_error_count + 1
  ↓
状态判定：是否达到 LIMITED / COOLDOWN / NEAR_LIMIT？
  ↓
是 → 写入 QuotaStatusHistory
  ↓
触发事件：quota.status_changed
  ↓
  ├─→ Handoff Manager：检查是否需要自动 Handoff
  │    ↓
  │    是 → 创建 HandoffRecord，生成 HandoffSummary
  │    ↓
  │    Model Router 选择新模型
  │    ↓
  │    Runtime 启动新 Worker 继续任务
  │
  └─→ Model Router：更新模型评分，降低受限模型权重
  │
  └─→ Workspace：更新 Risk Badge，向用户展示警告
```

### 7.3 Handoff 摘要中的额度信息

Handoff Manager 生成的 HandoffSummary 中，Quota Manager 提供以下字段：

```typescript
interface HandoffQuotaInfo {
  from_model_id: string;
  from_model_name: string;
  quota_status: QuotaStatus;
  usage_percent: number;
  total_tokens_consumed: number;
  limit_error_count: number;
  handoff_reason: 'quota_exceeded' | 'rate_limited' | 'cooldown' | 'manual';
  suggested_backup_models: string[];  // Model Router 提供的备用模型列表
}
```

---

## 8. Model Router 联动规则

### 8.1 额度状态对路由评分的影响

Model Router 的评分维度中，`quota_health` 直接与 Quota Manager 的状态关联：

```typescript
function calculateQuotaHealthScore(quotaStatus: QuotaStatus): number {
  switch (quotaStatus) {
    case QuotaStatus.NORMAL:   return 1.0;
    case QuotaStatus.WARNING:  return 0.7;
    case QuotaStatus.NEAR_LIMIT: return 0.3;
    case QuotaStatus.LIMITED:  return 0.0;
    case QuotaStatus.COOLDOWN: return 0.0;
    case QuotaStatus.UNKNOWN:  return 0.5; // 中性，不加分不扣分
  }
}
```

在 Model Router 的加权评分中：

- `quota_health` 权重默认 0.10。
- 如果模型状态为 LIMITED 或 COOLDOWN，直接排除（hard constraint）。
- 如果状态为 NEAR_LIMIT，在 RoutingResult 的 `risk_flags` 中标记 `"near_quota_limit"`。

### 8.2 风险标记传递

Model Router 返回的 `RoutingResult` 中，与额度相关的 risk_flags：

| risk_flag | 触发条件 | 含义 |
|-----------|----------|------|
| near_quota_limit | quota_status === NEAR_LIMIT | 推荐模型接近额度上限 |
| quota_unknown | quota_status === UNKNOWN | 无法判断推荐模型的额度状态 |
| backup_model_quota_low | 备用模型中有 NEAR_LIMIT | 备用模型也不安全 |
| all_models_limited | 所有候选模型 LIMITED/COOLDOWN | 无可用的模型 |

### 8.3 实时状态查询

Model Router 在每次路由决策前，调用 Quota Manager 的查询接口：

```typescript
GET /quota/models/:model_id/status
```

返回当前模型的 quota_status、usage_percent、estimated_remaining，供路由决策使用。

---

## 9. 前端页面设计

### 9.1 Quota Overview（额度总览页面）

**布局**：

```
┌─────────────────────────────────────────────────────────────┐
│  Quota Manager                              [刷新] [设置]   │
├─────────────────────────────────────────────────────────────┤
│  总览卡片行                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 正常模型 │ │ 警告模型 │ │ 受限模型 │ │ 未知模型 │       │
│  │    5     │ │    2     │ │    1     │ │    2     │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├─────────────────────────────────────────────────────────────┤
│  模型使用列表                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ [筛选: 全部 ▼] [排序: 使用率 ▼] [搜索...]            │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │ ● gpt-4o        ████████████░░  78%  WARNING         │  │
│  │ ● claude-3-5    ██████████████  95%  NEAR_LIMIT      │  │
│  │ ● deepseek-chat ██████░░░░░░░░  45%  NORMAL          │  │
│  │ ● kimi-k2       ░░░░░░░░░░░░░░   --   UNKNOWN        │  │
│  │ ● gpt-4         ██████████████ 100%  LIMITED         │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**交互**：

- 点击模型卡片 → 展开 Model Usage Card 详情。
- 点击 [设置] → 打开 Quota Settings Modal，可手动填写额度上限。
- 点击 [刷新] → 重新拉取最新额度状态。
- 筛选器：按 provider、quota_status 筛选。
- 排序：按使用率、最近使用、请求数排序。

### 9.2 Model Usage Card（模型使用卡片）

**展开状态**：

```
┌────────────────────────────────────────────┐
│ ● claude-3-5-sonnet                        │
│ Provider: Anthropic                        │
│ Status: NEAR_LIMIT 🔴                      │
├────────────────────────────────────────────┤
│ 使用率                                     │
│ ████████████████████░░░░  95%              │
│ 已用 950K / 上限 1M tokens                 │
├────────────────────────────────────────────┤
│ 使用统计                                   │
│ 调用次数：    1,234 次                     │
│ Input tokens：  600K                       │
│ Output tokens： 350K                       │
│ 总 tokens：     950K                       │
│ 最近使用：    2 分钟前                     │
├────────────────────────────────────────────┤
│ 风险记录                                   │
│ ⚠️ 3 小时前：429 rate limit (冷却 1 分钟) │
│ 🔴 1 小时前：insufficient_quota            │
│ 🔴 30 分钟前：insufficient_quota           │
├────────────────────────────────────────────┤
│ 操作                                       │
│ [手动修正额度] [标记为正常] [查看历史]     │
│ 因额度触发 Handoff：3 次                   │
└────────────────────────────────────────────┘
```

**交互**：

- [手动修正额度] → 打开 Edit Quota Modal，修改 token_limit、request_limit、cost_limit。
- [标记为正常] → 用户确认后，强制将状态设为 NORMAL（写入历史记录）。
- [查看历史] → 跳转到 Usage Trend 页面。

### 9.3 Usage Trend（使用趋势图）

**布局**：

```
┌────────────────────────────────────────────┐
│ gpt-4o 使用趋势                            │
│ 周期：[24小时] [7天] [30天]                │
├────────────────────────────────────────────┤
│                                            │
│  tokens                                    │
│  1M ┤    ╱╲                                │
│ 800K┤   ╱  ╲    ╱╲                         │
│ 600K┤  ╱    ╲  ╱  ╲                        │
│ 400K┤ ╱      ╲╱    ╲                      │
│ 200K┤╱              ╲                     │
│   0 ┼──────────────────────                │
│      00:00 06:00 12:00 18:00 24:00        │
│                                            │
├────────────────────────────────────────────┤
│ 状态变化历史                               │
│ 2026-06-25 14:32  NORMAL → WARNING        │
│ 2026-06-25 18:15  WARNING → NEAR_LIMIT     │
│ 2026-06-25 19:00  NEAR_LIMIT → LIMITED     │
│ 2026-06-25 19:05  LIMITED → COOLDOWN       │
│ 2026-06-25 19:10  COOLDOWN → NORMAL        │
└────────────────────────────────────────────┘
```

**图表类型**：

- 折线图：total_tokens 随时间变化。
- 柱状图：每小时 request_count。
- 状态变化时间轴：用颜色标记状态变化点。

### 9.4 Risk Badge（风险徽章）

Risk Badge 出现在以下位置：

- **Agent Station Board 的 Worker Badge**：显示当前 Worker 所用模型的 quota_status。
- **Model Router 的 RoutingResultCard**：显示推荐模型的风险标记。
- **Task Detail Panel**：显示当前 Task 所用模型的额度状态。

**样式**：

| 状态 | 颜色 | 图标 | 文本 |
|------|------|------|------|
| NORMAL | 绿色 | ✓ | 正常 |
| WARNING | 黄色 | ⚠ | 注意 |
| NEAR_LIMIT | 橙色 | 🔴 | 接近上限 |
| LIMITED | 红色 | ✕ | 已受限 |
| COOLDOWN | 蓝色 | ⏱ | 冷却中 |
| UNKNOWN | 灰色 | ? | 未知 |

**交互**：

- 鼠标悬停 → 显示 tooltip：使用率、剩余额度、最近错误。
- 点击 → 跳转到该模型的 Quota Overview 详情。

### 9.5 Handoff Trigger History（Handoff 触发历史）

**布局**：

```
┌─────────────────────────────────────────────────────────────┐
│ 额度触发的 Handoff 历史                                     │
├─────────────────────────────────────────────────────────────┤
│ 时间              从模型          到模型          原因      │
├─────────────────────────────────────────────────────────────┤
│ 2026-06-25 19:00  claude-3-5     gpt-4o         额度耗尽   │
│ 2026-06-25 15:30  deepseek-chat  kimi-k2        rate limit │
│ 2026-06-25 10:15  gpt-4          claude-3-5     手动切换   │
├─────────────────────────────────────────────────────────────┤
│ 点击行可查看完整 HandoffRecord                               │
└─────────────────────────────────────────────────────────────┘
```

**数据**：

- 从 Handoff Manager 的 HandoffRecord 中筛选 `trigger_reason` 包含 quota 的记录。
- 展示：时间、源模型、目标模型、触发原因、任务名。

---

## 10. 后端接口设计

### 10.1 Quota Record API

#### 10.1.1 记录 API 调用

```
POST /quota/record-usage
```

**请求体**：

```json
{
  "provider": "anthropic",
  "model_id": "claude-3-5-sonnet-20241022",
  "model_name": "Claude 3.5 Sonnet",
  "agent_station_id": "agent-123",
  "task_id": "task-456",
  "request_tokens": 1500,
  "response_tokens": 800,
  "total_tokens": 2300,
  "request_count": 1,
  "error_code": null,
  "error_type": null,
  "timestamp": "2026-06-25T10:00:00Z"
}
```

**响应**：

```json
{
  "quota_record_id": "quota-789",
  "updated_status": "warning",
  "usage_percent": 0.78,
  "estimated_remaining": 220000,
  "risk_flags": ["near_quota_limit"]
}
```

**业务逻辑**：

1. 根据 provider + model_id 查找或创建 QuotaRecord。
2. 累加 request_count、input_tokens、output_tokens、total_tokens。
3. 更新 last_used_at。
4. 如果 error_code 是额度相关错误，limit_error_count +1。
5. 重新计算 quota_status。
6. 如果状态变化，写入 QuotaStatusHistory。
7. 如果达到 NEAR_LIMIT / LIMITED / COOLDOWN，触发事件通知。

#### 10.1.2 获取单个模型额度状态

```
GET /quota/models/:model_id/status
```

**响应**：

```json
{
  "quota_record_id": "quota-789",
  "provider": "anthropic",
  "model_id": "claude-3-5-sonnet-20241022",
  "model_name": "Claude 3.5 Sonnet",
  "request_count": 1234,
  "input_tokens": 600000,
  "output_tokens": 350000,
  "total_tokens": 950000,
  "last_used_at": "2026-06-25T18:58:00Z",
  "estimated_remaining": 50000,
  "quota_status": "near_limit",
  "limit_error_count": 3,
  "cooldown_until": null,
  "handoff_triggered_count": 2,
  "updated_at": "2026-06-25T19:00:00Z",
  "usage_percent": 0.95,
  "quota_mode": "known",
  "token_limit": 1000000,
  "risk_flags": ["near_quota_limit"]
}
```

#### 10.1.3 获取所有模型额度概览

```
GET /quota/overview
```

**查询参数**：

- `provider`：按平台筛选（可选）
- `status`：按状态筛选（可选）
- `sort_by`：排序字段（usage_percent, last_used_at, request_count）
- `order`：asc / desc

**响应**：

```json
{
  "summary": {
    "total_models": 10,
    "normal_count": 5,
    "warning_count": 2,
    "near_limit_count": 1,
    "limited_count": 1,
    "cooldown_count": 0,
    "unknown_count": 1
  },
  "models": [
    {
      "quota_record_id": "quota-789",
      "provider": "anthropic",
      "model_id": "claude-3-5-sonnet-20241022",
      "model_name": "Claude 3.5 Sonnet",
      "quota_status": "near_limit",
      "usage_percent": 0.95,
      "estimated_remaining": 50000,
      "last_used_at": "2026-06-25T18:58:00Z",
      "limit_error_count": 3,
      "handoff_triggered_count": 2
    }
  ]
}
```

#### 10.1.4 手动修正额度

```
PATCH /quota/models/:model_id/quota
```

**请求体**：

```json
{
  "token_limit": 2000000,
  "request_limit": 5000,
  "cost_limit": 50.0,
  "reset_period": "monthly",
  "reset_date": 1,
  "quota_mode": "known"
}
```

**业务逻辑**：

1. 更新 QuotaRecord 的额度配置。
2. 重新计算 usage_percent 和 quota_status。
3. 写入 QuotaStatusHistory，triggered_by = "user"。
4. 返回更新后的状态。

#### 10.1.5 手动标记状态

```
PATCH /quota/models/:model_id/status
```

**请求体**：

```json
{
  "quota_status": "normal",
  "reason": "用户确认已充值",
  "cooldown_until": null
}
```

**约束**：

- 不能直接标记为 LIMITED 或 COOLDOWN（必须由系统根据错误码判定）。
- 用户标记为 NORMAL 后，limit_error_count 不清零，但状态覆盖为 NORMAL。
- 写入 QuotaStatusHistory，triggered_by = "user"。

### 10.2 Quota History API

#### 10.2.1 获取状态变化历史

```
GET /quota/models/:model_id/history
```

**响应**：

```json
{
  "history": [
    {
      "history_id": "hist-001",
      "from_status": "normal",
      "to_status": "warning",
      "reason": "使用率超过 70% 阈值",
      "triggered_by": "system",
      "usage_percent_at_change": 0.72,
      "total_tokens_at_change": 720000,
      "request_count_at_change": 900,
      "limit_error_count_at_change": 0,
      "created_at": "2026-06-25T14:32:00Z"
    }
  ]
}
```

#### 10.2.2 获取使用趋势

```
GET /quota/models/:model_id/trend
```

**查询参数**：

- `period`：24h / 7d / 30d
- `granularity`：hour / day

**响应**：

```json
{
  "period": "24h",
  "granularity": "hour",
  "data_points": [
    {
      "timestamp": "2026-06-25T00:00:00Z",
      "request_count": 10,
      "input_tokens": 5000,
      "output_tokens": 3000,
      "total_tokens": 8000,
      "limit_error_count": 0
    }
  ]
}
```

### 10.3 Handoff 联动 API

#### 10.3.1 获取额度触发的 Handoff 历史

```
GET /quota/handoff-history
```

**查询参数**：

- `model_id`：按模型筛选
- `period`：时间范围

**响应**：

```json
{
  "handoffs": [
    {
      "handoff_id": "handoff-001",
      "task_id": "task-456",
      "task_name": "实现用户登录功能",
      "from_model_id": "claude-3-5-sonnet-20241022",
      "to_model_id": "gpt-4o",
      "trigger_reason": "quota_exceeded",
      "quota_status_at_trigger": "limited",
      "usage_percent_at_trigger": 1.0,
      "created_at": "2026-06-25T19:00:00Z"
    }
  ]
}
```

---

## 11. 数据对象设计

### 11.1 QuotaRecord（额度记录）

```typescript
interface QuotaRecord {
  // 主键
  quota_record_id: string;           // UUID，唯一标识

  // 模型标识
  provider: string;                  // 平台：openai, anthropic, deepseek, kimi, etc.
  model_id: string;                  // 模型 ID：gpt-4o, claude-3-5-sonnet-20241022
  model_name: string;                // 显示名称：Claude 3.5 Sonnet

  // 使用统计
  request_count: number;             // API 调用总次数
  input_tokens: number;              // 输入 token 总量
  output_tokens: number;             // 输出 token 总量
  total_tokens: number;              // 总 token 量

  // 时间
  last_used_at: string;              // ISO 8601，最近一次调用时间
  updated_at: string;                // ISO 8601，记录更新时间
  created_at: string;                // ISO 8601，记录创建时间

  // 额度估算
  estimated_remaining: number;       // 估算剩余额度（tokens 或请求数）
  quota_mode: 'known' | 'estimated' | 'unknown';

  // 用户配置的额度上限
  token_limit?: number;              // token 上限
  request_limit?: number;            // 请求数上限
  cost_limit?: number;               // 费用上限（USD）
  reset_period?: 'daily' | 'weekly' | 'monthly' | 'never';
  reset_date?: number;               // 每月几号重置

  // 状态
  quota_status: QuotaStatus;         // normal / warning / near_limit / limited / cooldown / unknown

  // 错误统计
  limit_error_count: number;         // 额度/限制相关错误次数
  cooldown_until?: string;           // ISO 8601，冷却结束时间

  // Handoff 统计
  handoff_triggered_count: number;   // 因额度触发的 Handoff 次数

  // 估算元数据
  estimation_confidence?: number;    // 估算置信度（0-1）
  estimation_method?: 'usage_trend' | 'error_frequency' | 'default_assumption';
}
```

### 11.2 QuotaStatusHistory（状态变化历史）

```typescript
interface QuotaStatusHistory {
  history_id: string;
  quota_record_id: string;
  from_status: QuotaStatus;
  to_status: QuotaStatus;
  reason: string;
  triggered_by: 'system' | 'user' | 'handoff' | 'router';
  usage_percent_at_change: number;
  total_tokens_at_change: number;
  request_count_at_change: number;
  limit_error_count_at_change: number;
  created_at: string;
}
```

### 11.3 QuotaUsageLog（使用日志，可选，MVP-B）

```typescript
interface QuotaUsageLog {
  log_id: string;
  quota_record_id: string;
  task_id: string;
  agent_station_id: string;
  request_tokens: number;
  response_tokens: number;
  total_tokens: number;
  error_code?: string;
  error_type?: string;
  timestamp: string;
}
```

### 11.4 QuotaThresholds（阈值配置）

```typescript
interface QuotaThresholds {
  // 全局默认阈值
  warning_percent: number;           // 默认 0.70
  near_limit_percent: number;        // 默认 0.90
  cooldown_minutes: number;          // 默认 1
  max_errors_per_hour: number;       // 默认 3
  max_rate_limit_errors: number;     // 默认 2

  // 模型特定阈值（覆盖全局）
  model_overrides?: Record<string, Partial<QuotaThresholds>>;
}
```

---

## 12. 状态流转

### 12.1 状态流转图

```text
                    ┌──────────┐
                    │  UNKNOWN │
                    └────┬─────┘
                         │ 首次使用记录
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                      ┌──────────┐                            │
│         ┌───────────▶│  NORMAL  │◀──────────┐               │
│         │  使用率    └────┬─────┘   重置周期 │               │
│         │  < 70%          │          到期     │               │
│         │                 │ 使用率           │               │
│         │                 │ ≥ 70%            │               │
│         │                 ▼                  │               │
│         │            ┌──────────┐            │               │
│         │  使用率    │ WARNING  │            │               │
│         │  < 70%     └────┬─────┘            │               │
│         │                 │ 使用率           │               │
│         │                 │ ≥ 90%            │               │
│         │                 ▼                  │               │
│         │            ┌──────────┐            │               │
│         │            │NEAR_LIMIT│            │               │
│         │            └────┬─────┘            │               │
│         │                 │                  │               │
│         │                 │ 额度耗尽/错误    │               │
│         │                 ▼                  │               │
│         │            ┌──────────┐            │               │
│         │            │ LIMITED  │            │               │
│         │            └────┬─────┘            │               │
│         │                 │                  │               │
│         │                 │ 429 rate limit   │               │
│         │                 ▼                  │               │
│         │            ┌──────────┐            │               │
│         └────────────│ COOLDOWN │────────────┘               │
│   冷却结束/手动恢复   └──────────┘   冷却结束                 │
└──────────────────────────────────────────────────────────────┘
```

### 12.2 状态流转规则表

| 当前状态 | 触发条件 | 目标状态 | 说明 |
|----------|----------|----------|------|
| UNKNOWN | 首次使用记录 | NORMAL | 有使用数据后进入正常跟踪 |
| NORMAL | usage_percent ≥ 70% | WARNING | 接近阈值，提示注意 |
| NORMAL | 额度错误 | LIMITED | 直接受限 |
| NORMAL | 429 错误 | COOLDOWN | 进入冷却 |
| WARNING | usage_percent < 70% | NORMAL | 使用率回落 |
| WARNING | usage_percent ≥ 90% | NEAR_LIMIT | 接近上限 |
| WARNING | 额度错误 | LIMITED | 直接受限 |
| NEAR_LIMIT | usage_percent < 90% | WARNING | 使用率回落 |
| NEAR_LIMIT | 额度错误 | LIMITED | 直接受限 |
| NEAR_LIMIT | 429 错误 | COOLDOWN | 进入冷却 |
| LIMITED | 用户手动恢复 | NORMAL | 用户确认已解决 |
| LIMITED | 重置周期到期 | NORMAL | 月度/周期重置 |
| COOLDOWN | cooldown_until 过期 | NORMAL | 冷却结束 |
| COOLDOWN | 用户手动恢复 | NORMAL | 用户确认已解决 |

### 12.3 周期重置逻辑

当 `reset_period` 到期时：

1. request_count、input_tokens、output_tokens、total_tokens 清零。
2. limit_error_count 清零。
3. cooldown_until 置空。
4. quota_status 重置为 NORMAL。
5. 写入 QuotaStatusHistory：from_status = 原状态，to_status = NORMAL，reason = "周期重置"。

---

## 13. 异常状态

### 13.1 额度耗尽时任务正在执行

**场景**：任务执行过程中，API 返回 insufficient_quota。

**处理流程**：

1. Runtime 捕获错误，返回给 Quota Manager。
2. Quota Manager 更新 limit_error_count +1，状态设为 LIMITED。
3. Quota Manager 触发 `quota.exhausted` 事件。
4. Handoff Manager 收到事件，自动创建 HandoffRecord。
5. Model Router 选择备用模型（排除 LIMITED/COOLDOWN 模型）。
6. Runtime 用新模型继续执行任务。
7. Workspace 显示 Handoff 提示："Claude 额度耗尽，已自动切换至 GPT-4o 继续执行。"

**异常处理**：

- 如果所有备用模型都 LIMITED：暂停任务，向用户展示警告，等待用户手动处理。
- 如果 Handoff 失败：记录错误，任务状态设为 failed，用户可手动重试。

### 13.2 无法估算额度（UNKNOWN 状态）

**场景**：新添加的模型，无历史数据，用户未填写上限。

**处理策略**：

1. 状态设为 UNKNOWN。
2. Model Router 的 quota_health 评分为 0.5（中性）。
3. 首次使用时开始记录，逐步积累数据。
4. 使用默认假设法估算上限。
5. 在 Workspace 中显示 "? 未知" 提示，建议用户手动填写额度。

### 13.3 冷却期间的请求

**场景**：模型处于 COOLDOWN 状态，但任务仍尝试调用。

**处理策略**：

1. Runtime 调用前检查 quota_status。
2. 如果 COOLDOWN，直接返回错误，不发送 API 请求。
3. 触发 Handoff 流程，切换到非冷却模型。
4. 如果用户强制指定使用该模型，提示警告并允许执行（用户自担风险）。

### 13.4 用户手动修正与系统判定的冲突

**场景**：用户手动将 LIMITED 标记为 NORMAL，但系统很快又检测到额度错误。

**处理策略**：

1. 尊重用户手动标记，但继续监控。
2. 如果再次检测到额度错误，覆盖用户标记，恢复为 LIMITED。
3. 写入 QuotaStatusHistory，reason 标注 "系统检测到额度错误，覆盖用户标记"。
4. 向用户发送通知："您标记为正常的模型再次出现额度错误，已自动恢复受限状态。"

---

## 14. MVP 范围

### MVP-A（核心闭环）

1. **记录 API 调用次数和 token**：
   - Runtime 每次调用后异步记录 usage。
   - 支持 provider + model_id 粒度。

2. **支持手动填写或系统估算额度**：
   - 用户可在 Quota Settings 中填写 token_limit、request_limit。
   - 未填写时，使用默认假设法估算。

3. **根据错误码和使用频率判断风险**：
   - 支持 429、403、402 等额度相关错误码。
   - 基于使用率和错误次数判断 NORMAL / WARNING / NEAR_LIMIT / LIMITED / COOLDOWN / UNKNOWN。

4. **基础 Quota 页面**：
   - Quota Overview：所有模型的额度列表和总览卡片。
   - Model Usage Card：展开查看详情。
   - Risk Badge：在 Workspace 各位置显示状态。

5. **接近限制时提醒用户或触发 Handoff**：
   - NEAR_LIMIT 时，Workspace 显示警告提示。
   - LIMITED / COOLDOWN 时，自动触发 Handoff（如果已配置备用模型）。

### MVP-B（增强体验）

1. **Usage Trend 图表**：24h / 7d / 30d 趋势。
2. **QuotaStatusHistory 完整记录**：状态变化历史查询。
3. **按 API Key 粒度记录**：区分不同 Key 的额度。
4. **使用趋势法和错误频率法估算**：更智能的估算。
5. **Handoff Trigger History 页面**：展示额度触发的 Handoff 记录。

---

## 15. 暂缓范围

1. **不做所有平台真实 coding plan 额度读取**：
   - 理由：多数平台不提供实时额度 API，且接口差异大。
   - 替代：手动填写 + 系统估算。

2. **不做复杂计费预测**：
   - 理由：MVP 阶段不需要预测未来费用，只需要实时状态。
   - 替代：简单的使用率百分比。

3. **不做企业级成本管理**：
   - 理由：超出 MVP 范围，属于 V1+ 的平台化能力。
   - 替代：基础的 token/request 计数。

4. **不做自动购买额度**：
   - 理由：涉及支付集成和安全性，MVP 阶段不考虑。
   - 替代：提醒用户手动处理。

5. **不做跨账号额度池**：
   - 理由：多用户/多账号场景属于 V1+。
   - 替代：单用户本地额度记录。

---

## 16. 验收标准

### 16.1 功能验收

- [ ] 每次 API 调用后，QuotaRecord 的 request_count、total_tokens、last_used_at 正确更新。
- [ ] 收到 429/403/402 错误后，limit_error_count 正确增加，quota_status 变为 LIMITED 或 COOLDOWN。
- [ ] 用户使用率达到 70% 时，quota_status 变为 WARNING。
- [ ] 用户使用率达到 90% 时，quota_status 变为 NEAR_LIMIT。
- [ ] 用户手动填写 token_limit 后，usage_percent 和 estimated_remaining 正确计算。
- [ ] 用户手动修改 quota_status 后，QuotaStatusHistory 正确记录。
- [ ] LIMITED 状态下，Model Router 的评分将该模型降为 0。
- [ ] LIMITED 状态下，自动触发 Handoff（如果配置了备用模型）。
- [ ] COOLDOWN 状态下，Runtime 拒绝发送 API 请求，直接触发 Handoff。
- [ ] Quota Overview 页面正确显示所有模型的状态和统计。
- [ ] Risk Badge 在 Workspace 各位置正确显示颜色和图标。

### 16.2 体验验收

- [ ] 用户能在 3 秒内看到所有模型的额度状态。
- [ ] 额度不足时，用户能在 Workspace 看到清晰的警告提示和切换建议。
- [ ] Handoff 切换后，用户能在 ExecutionLog 中看到 "因额度不足自动切换模型" 的记录。
- [ ] 用户手动修正额度后，状态立即更新，无需等待下一次 API 调用。

### 16.3 性能验收

- [ ] 额度记录为异步操作，不阻塞 Runtime 主流程（延迟 < 100ms）。
- [ ] Quota Overview 页面加载时间 < 500ms（10 个模型以内）。
- [ ] 状态判定逻辑执行时间 < 50ms。

### 16.4 安全验收

- [ ] 额度数据仅存储在本地，不上传云端。
- [ ] 用户手动修正额度时，需要确认弹窗，防止误操作。
- [ ] 所有状态变化都有历史记录，可追溯、可审计。

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
>
> 相关文档：
> - `docs/prd/model-router-prd.md` — Model Router 联动规则
> - `docs/prd/handoff-manager-prd.md` — Handoff Manager 触发规则
> - `docs/prd/agent-workspace-prd.md` — Risk Badge 在 Workspace 中的展示
> - `docs/prd/agent-registry-prd.md` — Agent Station 的模型绑定
