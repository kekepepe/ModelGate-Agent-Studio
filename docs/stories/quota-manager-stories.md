# Quota Manager 用户故事

> 所属产品：ModelGate Agent Studio
>
> 来源文档：`docs/prd/quota-manager-prd.md`
>
> 文档定位：将 Quota Manager PRD 转化为可开发、可测试的用户故事与验收标准。

---

## 故事清单

| 编号 | 优先级 | 故事摘要 | 涉及页面 | 涉及接口 | 数据对象 |
|------|--------|----------|----------|----------|----------|
| US-QM-01 | P0 | 记录模型调用次数和 token | QuotaManager | `POST /quota/record-usage` | QuotaRecord |
| US-QM-02 | P0 | 查看模型额度概览 | QuotaOverviewPage | `GET /quota/overview` | QuotaRecord |
| US-QM-03 | P0 | 手动填写额度上限 | QuotaOverviewPage | `PATCH /quota/models/:id/quota` | QuotaRecord |
| US-QM-04 | P0 | 额度状态预警和告警 | Workspace, TopStatusBar | `GET /quota/models/:id/status` | QuotaRecord |
| US-QM-05 | P0 | 额度不足时自动触发 Handoff | Workspace | `POST /tasks/:taskId/handoff` | QuotaRecord, HandoffRecord |
| US-QM-06 | P1 | 查看额度状态变化历史 | QuotaOverviewPage | `GET /quota/models/:id/history` | QuotaStatusHistory |

---

## P0 用户故事

### US-QM-01：记录模型调用次数和 token

- **Summary:** 每次模型 API 调用后，系统自动记录调用次数、输入/输出 token 量，并更新额度估算。

#### Use Case:
- **As a** 多模型协作平台用户
- **I want to** 系统自动记录每个模型的调用次数和 token 使用量
- **so that** 我可以实时了解每个模型的消耗情况，避免额度突然用完

#### Acceptance Criteria:

- **Scenario:** API 调用后自动记录 usage
- **Given:** Runtime 调用了一次模型 API
- **When:** 收到 API 响应后（成功或失败）
- **Then：** 系统异步记录 usage，QuotaRecord 的 `request_count`、`input_tokens`、`output_tokens`、`total_tokens`、`last_used_at` 正确更新
- **and Then：** 如果 API 返回 429/403/402 等额度错误，`limit_error_count` +1
- **and Then：** 记录操作不阻塞 Runtime 主流程（延迟 < 100ms）

**涉及页面：** 后台服务（无前端页面）
**涉及接口：** `POST /quota/record-usage`
**数据对象：** QuotaRecord

**可转测试的验收点：**
1. 后端：`POST /quota/record-usage` 接收 `{ provider, model_id, request_tokens, response_tokens, error_code }`
2. 后端：调用后 `request_count` 累加 +1
3. 后端：`input_tokens` 累加 `request_tokens`，`output_tokens` 累加 `response_tokens`
4. 后端：返回 429 时 `limit_error_count` +1，且不累加 token（失败调用）
5. 后端：记录写入为异步操作，接口响应 < 100ms
6. 后端：根据 provider + model_id 自动查找或创建 QuotaRecord

---

### US-QM-02：查看模型额度概览

- **Summary:** 用户在 Quota Overview 页面看到所有模型的使用统计、额度状态和剩余估算。

#### Use Case:
- **As a** 拥有多个 AI Coding Plan 的开发者
- **I want to** 在一个页面看到所有模型的额度使用情况
- **so that** 我可以一眼判断哪些模型快用完了，哪些模型还充足

#### Acceptance Criteria:

- **Scenario:** 查看额度概览
- **Given:** 系统中已有多条 QuotaRecord
- **When:** 我进入 Quota Overview 页面
- **Then：** 页面展示模型列表，每行包含：模型名、Provider、调用次数、总 token、使用率、额度状态
- **and Then：** 顶部总览卡片显示：正常模型数、警告模型数、受限模型数、未知模型数
- **and Then：** 列表支持按 provider、quota_status 筛选，按使用率排序

**涉及页面：** QuotaOverviewPage / ModelUsageCard
**涉及接口：** `GET /quota/overview`
**数据对象：** QuotaRecord

**可转测试的验收点：**
1. 前端：列表每行显示 `model_name`、`request_count`、`total_tokens`、`usage_percent`（百分比进度条）、`quota_status` 彩色标签
2. 前端：顶部 4 个统计卡片（normal / warning / limited / unknown）数字正确
3. 前端：点击模型行展开 ModelUsageCard，显示 input/output token、最近调用时间、limit_error_count
4. 后端：`GET /quota/overview` 返回 `{ summary: { normal_count, warning_count, ... }, models: [...] }`
5. 后端：`models[]` 中每个对象包含 `usage_percent`、`estimated_remaining`、`quota_status`
6. 后端：支持 `sort_by=usage_percent` 和 `order=desc` 参数

---

### US-QM-03：手动填写额度上限

- **Summary:** 用户为某个模型手动填写 token 上限、请求数上限和重置周期，系统据此计算使用率和剩余额度。

#### Use Case:
- **As a** 需要精确管理模型额度的开发者
- **I want to** 手动填写每个模型的额度上限
- **so that** 系统可以准确计算使用率和剩余额度，而不是依赖不准确的估算

#### Acceptance Criteria:

- **Scenario:** 手动设置额度上限
- **Given:** 我正在 Quota Overview 页面，某个模型当前 quota_mode 为 unknown/estimated
- **When：** 我点击 [设置额度]，填写 token_limit = 1000000，reset_period = monthly，确认
- **Then：** 系统更新 QuotaRecord，`quota_mode` 变为 `known`，重新计算 `usage_percent` 和 `estimated_remaining`
- **and Then：** 如果填写后 usage_percent ≥ 70%，quota_status 自动变为 WARNING

**涉及页面：** QuotaOverviewPage / ModelUsageCard
**涉及接口：** `PATCH /quota/models/:modelId/quota`
**数据对象：** QuotaRecord

**可转测试的验收点：**
1. 前端：ModelUsageCard 中 [设置额度] 按钮在 unknown/estimated 状态下可见
2. 前端：表单包含 token_limit、request_limit、cost_limit、reset_period、reset_date 字段
3. 前端：保存后 usage_percent 进度条立即更新
4. 后端：`PATCH /quota/models/:modelId/quota` 接收 `{ token_limit, reset_period, ... }`
5. 后端：更新后 `quota_mode = "known"`，`usage_percent = total_tokens / token_limit`
6. 后端：状态变化时写入 QuotaStatusHistory，triggered_by = "user"

---

### US-QM-04：额度状态预警和告警

- **Summary:** 当模型额度达到 WARNING（≥70%）或 LIMITED（100% 或额度错误）时，系统在 Workspace 显示预警条，并在 RiskBadge 上更新状态。

#### Use Case:
- **As a** 不希望任务因额度中断的开发者
- **I want to** 在额度接近上限时收到系统预警
- **so that** 我可以提前决定切换模型或触发 Handoff，避免任务突然中断

#### Acceptance Criteria:

- **Scenario：** 额度预警展示
- **Given：** 模型 M 的使用率达到 78%，quota_status 变为 WARNING
- **When：** 状态变化事件推送到 Workspace
- **Then：** Workspace 顶部显示黄色预警条："⚠️ 模型 M 使用率 78% (WARNING)，建议关注或准备 Handoff"
- **and Then：** 所有使用该模型的 WorkerBadge 上 RiskBadge 变为黄色 ⚠
- **and Then：** 当 quota_status 变为 LIMITED 时，预警条变红色，且显示 "任务已自动 Handoff 至备用模型"

**涉及页面：** Workspace / TopStatusBar / WorkerBadge / RiskBadge
**涉及接口：** `GET /quota/models/:modelId/status`（推送）
**数据对象：** QuotaRecord

**可转测试的验收点：**
1. 前端：`WARNING` 时顶部显示黄色预警条，含 [查看额度] 和 [立即 Handoff] 按钮
2. 前端：`LIMITED` 时顶部显示红色告警条，不可关闭
3. 前端：RiskBadge 颜色与 QuotaStatus 严格对应（normal=绿、warning=黄、limited=红）
4. 后端：`GET /quota/models/:modelId/status` 返回 `quota_status`、`usage_percent`、`estimated_remaining`
5. 后端：状态达到 WARNING/NEAR_LIMIT/LIMITED 时触发 `quota.status_changed` 事件
6. 后端：LIMITED 状态的模型在 Model Router 评分中 `quota_health = 0`

---

### US-QM-05：额度不足时自动触发 Handoff

- **Summary:** 当模型额度 LIMITED 或 COOLDOWN 时，系统自动触发 Handoff 或阻止向该模型发送请求，确保任务不中断。

#### Use Case:
- **As a** 需要任务连续性的开发者
- **I want to** 当模型额度不足时，系统自动切换到备用模型继续任务
- **so that** 我的任务不会因为某个模型额度耗尽而被迫中断

#### Acceptance Criteria:

- **Scenario：** 额度不足自动 Handoff
- **Given：** Task 正在由模型 M 执行，模型 M 的 quota_status 变为 LIMITED
- **When：** Runtime 尝试再次调用模型 M 或系统检测到 LIMITED 状态
- **Then：** Runtime 拒绝向 LIMITED/COOLDOWN 模型发送 API 请求
- **and Then：** 系统自动触发 Handoff 流程（如果配置了备用模型）
- **and Then：** Workspace 显示告警："模型 M 已受限，已自动切换至模型 N 继续执行"
- **and Then：** Task 状态保持连续性，不标记为 failed

**涉及页面：** Workspace / TaskCard / ErrorBanner
**涉及接口：** `POST /tasks/:taskId/handoff`（内部自动触发）
**数据对象：** QuotaRecord, HandoffRecord, Task

**可转测试的验收点：**
1. 后端：Runtime 调用前检查 `quota_status`，LIMITED/COOLDOWN 时直接返回错误，不发 API 请求
2. 后端：LIMITED 触发 `quota.exhausted` 事件，Handoff Manager 自动创建 HandoffRecord
3. 后端：Handoff 原因标记为 `quota_exceeded`
4. 后端：自动 Handoff 的 to_model 由 Model Router 从非 LIMITED 模型中选择
5. 前端：TaskCard 状态从 running → handoff → running，不显示 failed
6. 前端：ErrorBanner 显示切换提示而非错误提示

---

## P1 用户故事

### US-QM-06：查看额度状态变化历史

- **Summary:** 用户在 Quota Overview 中查看某个模型的额度状态变化历史，包括何时从 normal → warning → limited，以及变化原因。

#### Use Case:
- **As a** 需要排查额度问题的开发者
- **I want to** 查看模型额度状态的变化历史
- **so that** 我可以追溯额度是在哪个时间点、因为什么原因（系统判定/用户手动/Handoff）发生变化的

#### Acceptance Criteria:

- **Scenario：** 查看状态变化历史
- **Given：** 我正在 Quota Overview 页面，某个模型有多次状态变化
- **When：** 我点击 [查看历史] 按钮
- **Then：** 展示状态变化时间线：from_status → to_status、变化时间、原因、触发者、当时的使用率

**涉及页面：** QuotaOverviewPage / ModelUsageCard
**涉及接口：** `GET /quota/models/:modelId/history`
**数据对象：** QuotaStatusHistory

**可转测试的验收点：**
1. 前端：历史列表按时间倒序排列
2. 前端：每条记录显示颜色变化条（如 绿色→黄色→红色）
3. 后端：`GET /quota/models/:modelId/history` 返回 `history[]`，包含 `from_status`、`to_status`、`reason`、`triggered_by`、`created_at`
4. 后端：用户手动修改的状态记录 `triggered_by = "user"`

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
