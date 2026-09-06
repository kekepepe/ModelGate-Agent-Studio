# Quota Manager 开发任务拆解

> 基于 `docs/stories/quota-manager-stories.md` 的 5 条 P0 + 1 条 P1 用户故事拆解
>
> 拆分模式：Operations (Pattern 2 — CRUD) + Simple/Complex (Pattern 7)
> ——先做数据模型和基础记录，再做状态计算，最后叠加预警和自动 Handoff。

---

## Epic: Quota Manager

**目标：** 自动记录模型调用次数和 token 消耗，计算额度使用率，在额度不足时预警用户并自动触发 Handoff，避免任务中断。

**Epic 验收标准：**
1. 每次模型 API 调用后自动记录 usage（成功或失败）
2. 用户在 Quota Overview 页面看到所有模型的使用统计和额度状态
3. 用户可为模型手动设置额度上限
4. 额度达到 WARNING（≥70%）时 Workspace 显示黄色预警条
5. 额度 LIMITED 时 Runtime 拒绝向该模型发送请求，并自动触发 Handoff
6. 额度状态变化触发事件，前端可实时更新

---

## Feature 1: Quota 数据模型与状态定义

> 对应 Story: US-QM-01 / US-QM-02 / US-QM-03 / US-QM-04 / US-QM-05
> 说明：所有 Story 共享 QuotaRecord 表和 QuotaStatus 状态机，合并为同一 Feature。

### Task 1.1: 创建 quota_records 数据库表

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T1.1 |
| **story_id** | US-QM-01 / US-QM-02 / US-QM-03 / US-QM-04 / US-QM-05 |
| **任务类型** | database |
| **文件** | `migrations/00x_create_quota_records.sql` |
| **任务说明** | 1. 创建 `quota_records` 表，字段：id, provider, model_id, model_name, request_count, input_tokens, output_tokens, total_tokens, limit_error_count, quota_mode (known/estimated/unknown), token_limit, request_limit, cost_limit, reset_period, reset_date, usage_percent, estimated_remaining, quota_status (normal/warning/near_limit/limited/cooldown/unknown), last_used_at, created_at, updated_at<br>2. 创建唯一索引 `idx_provider_model`（provider + model_id 唯一）<br>3. 创建索引 `idx_quota_status`、`idx_usage_percent` |
| **完成标准** | 1. 迁移脚本可正确执行<br>2. provider + model_id 组合唯一<br>3. 字段类型、NOT NULL 约束、默认值正确（request_count 默认 0，quota_mode 默认 unknown，quota_status 默认 unknown）<br>4. 索引覆盖高频查询场景 |
| **依赖任务** | 无 |
| **推荐顺序** | 1 |

---

### Task 1.2: 定义 QuotaStatus 状态机与额度计算逻辑

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T1.2 |
| **story_id** | US-QM-03 / US-QM-04 / US-QM-05 |
| **任务类型** | backend |
| **文件** | `src/domain/quota.ts`、`src/services/quota/quota-calculator.ts` |
| **任务说明** | 1. 定义 `QuotaStatus` 枚举：normal / warning / near_limit / limited / cooldown / unknown<br>2. 定义 `QuotaMode` 枚举：known / estimated / unknown<br>3. 实现额度计算函数：<br>   - `usage_percent`：known 模式 = total_tokens / token_limit；estimated 模式 = 基于历史趋势估算；unknown 模式 = null<br>   - `estimated_remaining`：known 模式 = token_limit - total_tokens<br>   - `quota_status`：usage_percent < 70% → normal；70-90% → warning；90-100% → near_limit；≥100% 或 limit_error_count > 0 → limited<br>4. 状态流转触发规则：usage_percent 跨越阈值时自动变更状态 |
| **完成标准** | 1. 6 个 QuotaStatus 枚举值完整<br>2. known 模式下 usage_percent 计算精确到小数点后 2 位<br>3. 状态阈值边界测试：69.99% = normal，70.00% = warning，89.99% = warning，90.00% = near_limit，100% = limited<br>4. limit_error_count > 0 时 quota_status 直接变为 limited<br>5. 单元测试覆盖全部计算逻辑和边界条件 |
| **依赖任务** | QM-T1.1 |
| **推荐顺序** | 2 |

---

### Task 1.3: 创建 QuotaStatusHistory 表（P1）

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T1.3 |
| **story_id** | US-QM-06 |
| **任务类型** | database |
| **文件** | `migrations/00x_create_quota_status_history.sql` |
| **任务说明** | 1. 创建 `quota_status_history` 表：id, quota_record_id, from_status, to_status, reason, triggered_by (user/system/handoff), usage_percent_at_change, created_at<br>2. 外键关联 `quota_records.id` |
| **完成标准** | 1. 表结构符合 PRD 定义<br>2. 外键关系正确，级联删除<br>3. 索引：`idx_quota_record_id`、`idx_created_at` |
| **依赖任务** | QM-T1.1 |
| **推荐顺序** | 15（P1，最后） |

---

## Feature 2: Usage 记录与累加

> 对应 Story: US-QM-01

### Task 2.1: 实现 POST /quota/record-usage API

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T2.1 |
| **story_id** | US-QM-01 |
| **任务类型** | backend |
| **文件** | `src/routes/quota.ts`、`src/services/quota/quota-recorder.ts` |
| **任务说明** | 1. 实现 `POST /quota/record-usage` 接口，接收 `{ provider, model_id, request_tokens, response_tokens, error_code }`<br>2. 根据 provider + model_id 查找或创建 QuotaRecord（UPSERT 逻辑）<br>3. 累加逻辑：`request_count += 1`、`input_tokens += request_tokens`、`output_tokens += response_tokens`、`total_tokens = input_tokens + output_tokens`<br>4. 错误处理：error_code 为 429/403/402 时，`limit_error_count += 1`，且不累加 token（失败调用）<br>5. 更新 `last_used_at` 为当前时间<br>6. 写入操作异步执行，接口响应 < 100ms（先写入内存队列或消息队列，后台落库）<br>7. MVP 阶段可用 setImmediate / 内存队列实现异步，不引入 Kafka/RabbitMQ |
| **完成标准** | 1. 正常请求返回 200/201，响应时间 < 100ms<br>2. 调用后 request_count 累加 +1<br>3. input_tokens 累加 request_tokens，output_tokens 累加 response_tokens<br>4. 返回 429 时 limit_error_count +1，token 不累加<br>5. 新 provider+model_id 组合自动创建 QuotaRecord<br>6. 集成测试覆盖 |
| **依赖任务** | QM-T1.1 |
| **推荐顺序** | 3 |

---

### Task 2.2: Usage 记录后触发额度重算

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T2.2 |
| **story_id** | US-QM-01 / US-QM-04 |
| **任务类型** | backend |
| **文件** | `src/services/quota/quota-recorder.ts`、`src/services/quota/quota-calculator.ts` |
| **任务说明** | 1. 在 Usage 记录累加完成后，触发额度重算<br>2. 重新计算 usage_percent、estimated_remaining、quota_status<br>3. 如果 quota_status 发生变化（如 normal → warning），触发 `quota.status_changed` 事件<br>4. 状态变化时写入 QuotaStatusHistory（如果表已存在）<br>5. 事件通过简单的 EventEmitter / 回调机制传递，MVP 不引入复杂事件总线 |
| **完成标准** | 1. Usage 记录后 usage_percent 正确更新<br>2. 状态变化时触发事件，事件包含 quota_record_id、from_status、to_status、usage_percent<br>3. 状态未变化时不触发事件（避免噪音）<br>4. 单元测试覆盖状态变化检测逻辑 |
| **依赖任务** | QM-T1.2 / QM-T2.1 |
| **推荐顺序** | 4 |

---

## Feature 3: 额度概览与配置 API

> 对应 Story: US-QM-02 / US-QM-03

### Task 3.1: GET /quota/overview 概览 API

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T3.1 |
| **story_id** | US-QM-02 |
| **任务类型** | backend |
| **文件** | `src/routes/quota.ts`、`src/services/quota/quota-overview.service.ts` |
| **任务说明** | 1. 实现 `GET /quota/overview` 接口<br>2. 返回结构：`{ summary: { normal_count, warning_count, limited_count, unknown_count }, models: [...] }`<br>3. `models[]` 中每个对象包含：model_name、provider、request_count、total_tokens、usage_percent、estimated_remaining、quota_status、last_used_at、limit_error_count<br>4. 支持查询参数：`sort_by=usage_percent`、`order=desc`、`provider`、`quota_status`<br>5. 未设置 token_limit 的模型（quota_mode = unknown/estimated）usage_percent 显示为 null 或 "—" |
| **完成标准** | 1. 返回结构符合 PRD 定义<br>2. summary 中 4 个计数器正确（基于 quota_status 分组统计）<br>3. `sort_by=usage_percent&order=desc` 按使用率降序排列<br>4. provider 筛选只返回该 provider 的模型<br>5. 无记录时返回空数组，summary 全为 0<br>6. 集成测试覆盖 |
| **依赖任务** | QM-T1.1 / QM-T1.2 |
| **推荐顺序** | 5 |

---

### Task 3.2: PATCH /quota/models/:modelId/quota 手动设置额度 API

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T3.2 |
| **story_id** | US-QM-03 |
| **任务类型** | backend |
| **文件** | `src/routes/quota.ts`、`src/services/quota/quota-config.service.ts` |
| **任务说明** | 1. 实现 `PATCH /quota/models/:modelId/quota` 接口<br>2. 接收 `{ token_limit, request_limit, cost_limit, reset_period, reset_date }`<br>3. 更新 QuotaRecord：`quota_mode = "known"`，重新计算 usage_percent 和 estimated_remaining<br>4. 如果更新后 usage_percent ≥ 70%，quota_status 自动变为 WARNING<br>5. 状态变化时触发 `quota.status_changed` 事件，triggered_by = "user"<br>6. 返回更新后的完整 QuotaRecord |
| **完成标准** | 1. 正常请求返回 200 + 更新后的 QuotaRecord<br>2. 更新后 quota_mode = "known"<br>3. usage_percent = total_tokens / token_limit，精确到小数点后 2 位<br>4. token_limit ≤ 0 返回 400<br>5. 状态变化时触发事件，事件 payload 包含 triggered_by = "user"<br>6. 集成测试覆盖 |
| **依赖任务** | QM-T1.2 / QM-T3.1 |
| **推荐顺序** | 6 |

---

### Task 3.3: GET /quota/models/:modelId/status 单模型状态查询 API

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T3.3 |
| **story_id** | US-QM-04 |
| **任务类型** | backend |
| **文件** | `src/routes/quota.ts` |
| **任务说明** | 1. 实现 `GET /quota/models/:modelId/status` 接口<br>2. 返回：`{ quota_status, usage_percent, estimated_remaining, limit_error_count, last_used_at }`<br>3. 该接口供 Workspace 的 RiskBadge 和 TopStatusBar 使用，支持 SSE/轮询 |
| **完成标准** | 1. 正常请求返回 200 + 状态对象<br>2. modelId 不存在返回 404<br>3. 返回字段与 PRD 定义一致<br>4. 集成测试覆盖 |
| **依赖任务** | QM-T1.1 / QM-T1.2 |
| **推荐顺序** | 7 |

---

## Feature 4: Workspace 额度预警

> 对应 Story: US-QM-04

### Task 4.1: Workspace TopStatusBar 额度预警条（mock 数据）

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T4.1 |
| **story_id** | US-QM-04 |
| **任务类型** | frontend |
| **文件** | `src/components/TopStatusBar.tsx`、`src/components/QuotaAlertBanner.tsx` |
| **任务说明** | 1. 实现 QuotaAlertBanner 组件，嵌入 TopStatusBar<br>2. WARNING 状态：黄色预警条，显示 "⚠️ 模型 M 使用率 78% (WARNING)，建议关注或准备 Handoff"，含 [查看额度] 和 [立即 Handoff] 按钮<br>3. LIMITED 状态：红色告警条，显示 "模型 M 已受限，任务已自动 Handoff 至备用模型"，不可关闭<br>4. 先使用 mock 数据让 UI 可独立运行和视觉验收<br>5. 预警条支持多条叠加（多个模型同时 WARNING 时轮播或堆叠显示） |
| **完成标准** | 1. WARNING 时显示黄色条，LIMITED 时显示红色条<br>2. LIMITED 条不可关闭（无关闭按钮）<br>3. 按钮点击触发对应事件回调（预留）<br>4. 组件测试覆盖不同状态的渲染 |
| **依赖任务** | 无（与后端并行） |
| **推荐顺序** | 8 |

---

### Task 4.2: WorkerBadge RiskBadge 组件（mock 数据）

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T4.2 |
| **story_id** | US-QM-04 |
| **任务类型** | frontend |
| **文件** | `src/components/RiskBadge.tsx`、`src/components/WorkerBadge.tsx` |
| **任务说明** | 1. 实现 RiskBadge 组件，显示在 WorkerBadge 右上角<br>2. 颜色映射：normal=绿色✓、warning=黄色⚠、near_limit=橙色🔴、limited=红色✗、cooldown=蓝色⏱、unknown=灰色?<br>3. 鼠标悬停显示 Tooltip：使用率、剩余额度、最近错误<br>4. 先使用 mock 数据 |
| **完成标准** | 1. 6 种状态颜色与图标正确对应<br>2. Tooltip 显示 usage_percent 和 estimated_remaining<br>3. limited 状态显示红色 ✗<br>4. 组件测试覆盖 6 种状态渲染 |
| **依赖任务** | 无（与后端并行） |
| **推荐顺序** | 9 |

---

### Task 4.3: 对接真实 Quota 状态数据（轮询/SSE）

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T4.3 |
| **story_id** | US-QM-04 |
| **任务类型** | frontend |
| **文件** | `src/hooks/useQuotaStatus.ts`、`src/api/quota.ts` |
| **任务说明** | 1. 实现 `api.getQuotaStatus(modelId)` 封装 `GET /quota/models/:modelId/status`<br>2. useQuotaStatus hook：轮询获取模型额度状态（每 10 秒），或接入 SSE 推送<br>3. 状态变化时更新 RiskBadge 颜色和 TopStatusBar 预警条<br>4. 监听 `quota.status_changed` 事件（SSE 或轮询触发），立即刷新对应模型状态 |
| **完成标准** | 1. RiskBadge 颜色与后端 quota_status 严格同步<br>2. WARNING 状态时 TopStatusBar 自动弹出黄色预警条<br>3. LIMITED 状态时预警条变红，RiskBadge 变红<br>4. 状态变化有平滑过渡动画（300ms）<br>5. API 错误时有降级显示（unknown 灰色状态） |
| **依赖任务** | QM-T3.3 / QM-T4.1 / QM-T4.2 |
| **推荐顺序** | 10 |

---

## Feature 5: 自动 Handoff 触发

> 对应 Story: US-QM-05

### Task 5.1: LIMITED 模型拦截 + 自动 Handoff 触发

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T5.1 |
| **story_id** | US-QM-05 |
| **任务类型** | backend |
| **文件** | `src/services/runtime/quota-guard.ts`、`src/services/quota/auto-handoff.service.ts` |
| **任务说明** | 1. 在 Runtime 调用模型 API 前，检查该模型的 quota_status<br>2. 如果 quota_status 为 LIMITED 或 COOLDOWN，直接返回错误（不发送 API 请求），错误信息："模型额度已耗尽，已触发自动 Handoff"<br>3. 触发 `quota.exhausted` 事件，Handoff Manager 监听并自动创建 HandoffRecord<br>4. Handoff 原因标记为 `quota_exceeded`<br>5. to_model 由 Model Router 从非 LIMITED 模型中选择（调用已有的 select-model 逻辑）<br>6. Task 状态保持连续性，不标记为 failed |
| **完成标准** | 1. LIMITED 模型的 API 调用被拦截，返回特定错误码<br>2. 拦截时触发 `quota.exhausted` 事件<br>3. HandoffRecord 的 handoff_reason = "quota_exceeded"<br>4. to_model 的 quota_status 不是 LIMITED<br>5. Task 状态从 running → handoff → running，不显示 failed<br>6. 单元测试覆盖拦截逻辑和事件触发 |
| **依赖任务** | QM-T1.2 / QM-T2.2（状态计算）/ MR-T3.1（Model Router 选择备用模型） |
| **推荐顺序** | 11 |

---

### Task 5.2: Workspace 自动 Handoff 状态展示

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T5.2 |
| **story_id** | US-QM-05 |
| **任务类型** | frontend |
| **文件** | `src/components/ErrorBanner.tsx`、`src/components/TaskCard.tsx` |
| **任务说明** | 1. 自动 Handoff 发生时，Workspace 显示提示而非错误<br>2. ErrorBanner 显示 "模型 M 已受限，已自动切换至模型 N 继续执行"（非红色错误样式）<br>3. TaskCard 状态从 running → handoff → running，不显示 failed<br>4. WorkerBadge 模型名称平滑过渡到新模型（300ms） |
| **完成标准** | 1. 自动 Handoff 时 ErrorBanner 为信息样式（蓝色/黄色），非红色错误<br>2. TaskCard 不显示 failed 红色边框<br>3. WorkerBadge 模型名切换有 300ms CSS transition<br>4. 前端测试覆盖 |
| **依赖任务** | QM-T5.1 / HM-T4.x（Handoff 可视化组件） |
| **推荐顺序** | 12 |

---

## Feature 6: Quota Overview 管理页面

> 对应 Story: US-QM-02 / US-QM-03

### Task 6.1: QuotaOverviewPage 页面框架 + 模型列表（mock 数据）

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T6.1 |
| **story_id** | US-QM-02 |
| **任务类型** | frontend |
| **文件** | `src/pages/QuotaOverviewPage.tsx`、`src/components/ModelUsageList.tsx` |
| **任务说明** | 1. 创建 QuotaOverviewPage 页面，路由 `/quota`<br>2. 顶部统计卡片：normal_count、warning_count、limited_count、unknown_count（4 个彩色卡片）<br>3. 模型列表：每行显示 model_name、provider、request_count、total_tokens、usage_percent（进度条）、quota_status（彩色标签）<br>4. 支持按 provider、quota_status 筛选，按 usage_percent 排序<br>5. 先使用 mock 数据 |
| **完成标准** | 1. 页面可访问 `/quota`<br>2. 4 个统计卡片数字正确，颜色与状态对应（normal=绿、warning=黄、limited=红、unknown=灰）<br>3. 列表每行有 usage_percent 进度条<br>4. quota_status 标签颜色正确<br>5. 筛选和排序功能正常（前端先 mock 实现） |
| **依赖任务** | 无（与后端并行） |
| **推荐顺序** | 13 |

---

### Task 6.2: 对接真实概览 API + ModelUsageCard 展开

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T6.2 |
| **story_id** | US-QM-02 |
| **任务类型** | frontend |
| **文件** | `src/hooks/useQuotaOverview.ts`、`src/components/ModelUsageCard.tsx` |
| **任务说明** | 1. useQuotaOverview hook 对接 `GET /quota/overview`<br>2. 点击模型行展开 ModelUsageCard，显示：input/output token、最近调用时间、limit_error_count、额度模式（known/estimated/unknown）<br>3. 支持按 provider、quota_status 筛选，按 usage_percent 排序（调用后端 API）<br>4. 列表支持分页 |
| **完成标准** | 1. 页面展示真实数据库中的额度数据<br>2. 点击行展开 ModelUsageCard，字段完整<br>3. 筛选排序调用真实 API<br>4. 空列表时显示引导 "暂无额度记录，开始调用模型后自动统计" |
| **依赖任务** | QM-T3.1 / QM-T6.1 |
| **推荐顺序** | 14 |

---

### Task 6.3: 额度设置表单（ModelUsageCard 内嵌）

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T6.3 |
| **story_id** | US-QM-03 |
| **任务类型** | frontend |
| **文件** | `src/components/QuotaConfigForm.tsx`、`src/components/ModelUsageCard.tsx` |
| **任务说明** | 1. ModelUsageCard 中 [设置额度] 按钮：在 quota_mode 为 unknown/estimated 时可见<br>2. 点击后弹出表单：token_limit（数字输入）、request_limit（数字输入）、cost_limit（数字输入）、reset_period（下拉：daily/weekly/monthly/yearly）、reset_date（日期选择器）<br>3. 保存后调用 `PATCH /quota/models/:modelId/quota`<br>4. 成功后 usage_percent 进度条立即更新，quota_status 标签变色 |
| **完成标准** | 1. [设置额度] 按钮只在 unknown/estimated 状态可见<br>2. 表单字段完整，token_limit 为空时提交禁用<br>3. 保存后进度条和标签立即更新（乐观更新或刷新 API）<br>4. 成功后显示 toast "额度设置已保存"<br>5. 组件测试覆盖 |
| **依赖任务** | QM-T3.2 / QM-T6.2 |
| **推荐顺序** | 15 |

---

## Feature 7: 额度状态历史（P1）

> 对应 Story: US-QM-06

### Task 7.1: GET /quota/models/:modelId/history API

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T7.1 |
| **story_id** | US-QM-06 |
| **任务类型** | backend |
| **文件** | `src/routes/quota.ts` |
| **任务说明** | 1. 实现 `GET /quota/models/:modelId/history` 接口<br>2. 返回 `history[]`，包含 from_status、to_status、reason、triggered_by、usage_percent_at_change、created_at<br>3. 按 created_at 倒序排列 |
| **完成标准** | 1. 返回 200 + history 数组<br>2. 按时间倒序排列<br>3. triggered_by 正确：用户手动修改 = "user"、系统自动 = "system"、Handoff 触发 = "handoff"<br>4. 集成测试覆盖 |
| **依赖任务** | QM-T1.3 / QM-T2.2 |
| **推荐顺序** | 16（P1，延后） |

---

### Task 7.2: QuotaStatusHistory 时间线组件

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T7.2 |
| **story_id** | US-QM-06 |
| **任务类型** | frontend |
| **文件** | `src/components/QuotaStatusHistory.tsx` |
| **任务说明** | 1. 在 ModelUsageCard 或独立页面中展示状态变化时间线<br>2. 每条记录显示：from_status → to_status、变化时间、原因、触发者、当时使用率<br>3. 颜色变化条：绿色→黄色→红色<br>4. 按时间倒序排列 |
| **完成标准** | 1. 时间线正确展示状态变化<br>2. 颜色条反映状态变化趋势<br>3. 空历史时显示 "暂无状态变化记录"<br>4. 组件测试覆盖 |
| **依赖任务** | QM-T7.1 |
| **推荐顺序** | 17（P1，延后） |

---

## Feature 8: 测试与质量保障

### Task 8.1: 额度计算与状态机单元测试

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T8.1 |
| **story_id** | US-QM-01 / US-QM-03 / US-QM-04 |
| **任务类型** | test |
| **文件** | `tests/quota/quota-calculator.test.ts` |
| **任务说明** | 1. usage_percent 计算：known 模式 / estimated 模式 / unknown 模式<br>2. 状态阈值边界：69.99%→normal、70%→warning、89.99%→warning、90%→near_limit、100%→limited<br>3. limit_error_count > 0 → limited<br>4. 状态流转：normal→warning→near_limit→limited 和反向（设置更高额度后降级）<br>5. estimated_remaining 计算 |
| **完成标准** | 1. 全部边界条件有测试用例<br>2. 状态升降级逻辑正确<br>3. 测试覆盖率 ≥ 90% |
| **依赖任务** | QM-T1.2 |
| **推荐顺序** | 18（与开发并行） |

---

### Task 8.2: API 集成测试

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T8.2 |
| **story_id** | US-QM-01 / US-QM-02 / US-QM-03 / US-QM-04 |
| **任务类型** | test |
| **文件** | `tests/quota.api.test.ts` |
| **任务说明** | 1. `POST /quota/record-usage` — 正常/429错误/新模型自动创建/响应时间<br>2. `GET /quota/overview` — 正常/筛选/排序/空列表<br>3. `PATCH /quota/models/:modelId/quota` — 正常/负额度/状态自动变化<br>4. `GET /quota/models/:modelId/status` — 正常/不存在<br>5. LIMITED 拦截 — 拦截成功/非 LIMITED 放行 |
| **完成标准** | 1. 全部 5 个 API 场景有测试<br>2. 每个 API 至少 3 个测试用例<br>3. 数据库状态在每次测试后正确清理 |
| **依赖任务** | QM-T2.1 / QM-T3.1 / QM-T3.2 / QM-T3.3 / QM-T5.1 |
| **推荐顺序** | 19（与开发并行） |

---

### Task 8.3: 前端组件测试

| 属性 | 值 |
|------|-----|
| **task_id** | QM-T8.3 |
| **story_id** | US-QM-02 / US-QM-04 |
| **任务类型** | test |
| **文件** | `tests/components/QuotaAlertBanner.test.tsx`、`tests/components/RiskBadge.test.tsx`、`tests/components/QuotaOverviewPage.test.tsx` |
| **任务说明** | 1. QuotaAlertBanner：WARNING 黄色条 / LIMITED 红色条 / 按钮点击 / 不可关闭<br>2. RiskBadge：6 种状态颜色 / Tooltip / 图标<br>3. QuotaOverviewPage：列表渲染 / 统计卡片 / 筛选排序 / 空状态<br>4. ModelUsageCard：展开/折叠 / 额度设置按钮显隐 |
| **完成标准** | 1. 全部 4 个组件/页面有测试文件<br>2. 每个覆盖主要渲染状态<br>3. 快照测试覆盖关键 UI |
| **依赖任务** | QM-T4.1 / QM-T4.2 / QM-T6.1 / QM-T6.2 |
| **推荐顺序** | 20（与开发并行） |

---

## 推荐开发顺序

```
Phase 1 — 数据模型 + Usage 记录 + 状态计算（1 周）
  QM-T1.1  创建 quota_records 表
  QM-T1.2  QuotaStatus 状态机 + 额度计算逻辑
  QM-T2.1  POST /quota/record-usage API
  QM-T2.2  Usage 记录后触发额度重算
  QM-T8.1  额度计算单元测试（与开发并行）

Phase 2 — 概览与配置 API（3-4 天）
  QM-T3.1  GET /quota/overview 概览 API
  QM-T3.2  PATCH /quota/models/:modelId/quota 设置额度 API
  QM-T3.3  GET /quota/models/:modelId/status 状态查询 API
  QM-T8.2  API 集成测试（与开发并行）

Phase 3 — Workspace 预警 + 管理页面（1 周）
  QM-T4.1  TopStatusBar 预警条（mock）
  QM-T4.2  RiskBadge 组件（mock）
  QM-T4.3  对接真实 Quota 数据
  QM-T6.1  QuotaOverviewPage + 列表（mock）
  QM-T6.2  对接真实概览 API
  QM-T6.3  额度设置表单
  QM-T8.3  前端组件测试（与开发并行）

Phase 4 — 自动 Handoff（3-4 天）
  QM-T5.1  LIMITED 拦截 + 自动 Handoff 触发
  QM-T5.2  Workspace 自动 Handoff 状态展示

Phase 5 — P1 状态历史（2 天，可选）
  QM-T1.3  创建 QuotaStatusHistory 表
  QM-T7.1  GET /quota/models/:modelId/history API
  QM-T7.2  QuotaStatusHistory 时间线组件
```

---

## 按 Phase 排期的任务看板

### Phase 1 — 数据模型 + Usage 记录（1 周）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| QM-T1.1 | quota_records 表结构 | database | 无 | QM-01~05 |
| QM-T1.2 | QuotaStatus 状态机 + 计算逻辑 | backend | QM-T1.1 | QM-03~05 |
| QM-T2.1 | POST /quota/record-usage | backend | QM-T1.1 | QM-01 |
| QM-T2.2 | Usage 记录后触发重算 | backend | QM-T1.2/2.1 | QM-01/04 |
| QM-T8.1 | 额度计算单元测试 | test | QM-T1.2 | QM-01/03/04 |

**Phase 1 交付物：** Usage 记录 API 可运行，额度自动计算和状态流转正确。可通过 HTTP 工具记录 usage 并观察状态变化。

### Phase 2 — 概览与配置 API（3-4 天）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| QM-T3.1 | GET /quota/overview | backend | QM-T1.2 | QM-02 |
| QM-T3.2 | PATCH /quota/models/:modelId/quota | backend | QM-T1.2 | QM-03 |
| QM-T3.3 | GET /quota/models/:modelId/status | backend | QM-T1.2 | QM-04 |
| QM-T8.2 | API 集成测试 | test | QM-T2/3.x | QM-01~04 |

**Phase 2 交付物：** 完整的 Quota 查询和配置 API，支持概览、单模型状态查询、手动设置额度。

### Phase 3 — Workspace 预警 + 管理页面（1 周）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| QM-T4.1 | TopStatusBar 预警条 | frontend | 无 | QM-04 |
| QM-T4.2 | RiskBadge 组件 | frontend | 无 | QM-04 |
| QM-T4.3 | 对接真实 Quota 数据 | frontend | QM-T3.3/4.1/4.2 | QM-04 |
| QM-T6.1 | QuotaOverviewPage（mock） | frontend | 无 | QM-02 |
| QM-T6.2 | 对接真实概览 API | frontend | QM-T3.1/6.1 | QM-02 |
| QM-T6.3 | 额度设置表单 | frontend | QM-T3.2/6.2 | QM-03 |
| QM-T8.3 | 前端组件测试 | test | QM-T4/6.x | QM-02/04 |

**Phase 3 交付物：** Workspace 实时显示额度预警，RiskBadge 颜色同步，Quota Overview 页面可查看和配置额度。

### Phase 4 — 自动 Handoff（3-4 天）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| QM-T5.1 | LIMITED 拦截 + 自动 Handoff | backend | QM-T1.2/2.2/MR-T3.1 | QM-05 |
| QM-T5.2 | Workspace 自动 Handoff 展示 | frontend | QM-T5.1 | QM-05 |

**Phase 4 交付物：** LIMITED 模型自动被排除，系统自动触发 Handoff 到备用模型，用户看到平滑切换提示。

### Phase 5 — P1 状态历史（2 天，可选）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| QM-T1.3 | QuotaStatusHistory 表 | database | QM-T1.1 | QM-06 |
| QM-T7.1 | GET /quota/models/:modelId/history | backend | QM-T1.3 | QM-06 |
| QM-T7.2 | 状态历史时间线组件 | frontend | QM-T7.1 | QM-06 |

**Phase 5 交付物：** 可查看模型额度状态变化历史。

---

## 风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| Usage 记录高频写入导致数据库压力 | Phase 1 性能问题 | Task 2.1 使用内存队列 + 批量写入，MVP 不引入 Kafka；每 5 秒批量 flush 一次 |
| 额度估算（estimated 模式）算法复杂 | Phase 1 延迟 | MVP 先只做 known 模式（用户手动设置）和 unknown 模式（无估算）；estimated 模式后续迭代 |
| 自动 Handoff 依赖 Handoff Manager 和 Model Router | Phase 4 无法集成 | Task 5.1 先实现 LIMITED 拦截和事件触发，Handoff 创建逻辑用最小 stub 实现；等 Handoff Manager 就绪后替换为真实调用 |
| 前端需要实时推送额度状态 | SSE 实现复杂 | Task 4.3 先用轮询（10 秒间隔），SSE 作为后续优化 |
| 多个模型同时 WARNING 时预警条过多 | UI 混乱 | Task 4.1 支持多条预警轮播或合并显示 "3 个模型额度预警" |

---

## Story → Task 映射表

| Story | 涉及 Task | 是否完整覆盖 |
|-------|-----------|--------------|
| US-QM-01 记录模型调用次数和 token | QM-T1.1 / QM-T2.1 / QM-T2.2 | 是 |
| US-QM-02 查看模型额度概览 | QM-T1.1 / QM-T1.2 / QM-T3.1 / QM-T6.1 / QM-T6.2 | 是 |
| US-QM-03 手动填写额度上限 | QM-T1.1 / QM-T1.2 / QM-T3.2 / QM-T6.3 | 是 |
| US-QM-04 额度状态预警和告警 | QM-T1.2 / QM-T2.2 / QM-T3.3 / QM-T4.1 / QM-T4.2 / QM-T4.3 | 是 |
| US-QM-05 额度不足时自动触发 Handoff | QM-T1.2 / QM-T2.2 / QM-T5.1 / QM-T5.2 | 是 |
| US-QM-06 查看额度状态变化历史 | QM-T1.3 / QM-T7.1 / QM-T7.2 | 是 |

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
>
> 相关文档：
> - `docs/stories/quota-manager-stories.md` — 用户故事来源
> - `docs/prd/quota-manager-prd.md` — 产品需求
> - `docs/architecture/数据结构与数据库Schema.md` — Schema 定义
