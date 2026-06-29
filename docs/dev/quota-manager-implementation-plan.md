# Quota Manager Implementation Plan

> 生成日期：2026-06-29
> 模块 slug：`quota-manager`
> 对应文档：PRD / Stories / Tasks / UI Spec

---

## 1. 已阅读的文档

1. `docs/prd/quota-manager-prd.md` — 产品需求（额度记录、估算、风险状态、联动规则）
2. `docs/stories/quota-manager-stories.md` — 5 条 P0 + 1 条 P1 用户故事
3. `docs/tasks/quota-manager-tasks.md` — 按 Phase 分组的 20 个任务
4. `docs/ui/quota-manager-ui-spec.md` — **不存在**，基于 PRD 第 9 节推断 UI 需求
5. `docs/architecture/API-Contract.md` — 通用 API 响应格式
6. `docs/architecture/数据结构与数据库Schema.md` — 状态枚举和数据对象定义
7. `docs/dev/module-development-sop.md` — 7 轮开发 SOP
8. `docs/dev/implementation-log.md` — 已有 Agent Registry + Model Router 日志

---

## 2. 当前项目结构判断

### 2.1 已完成模块

- **Agent Registry**（已完成）— agent_stations 表 + CRUD API（6 端点）+ 前端页面（/agents）
- **Model Router**（已完成）— models 表 + 6 维度评分 + 路由 API + 前端页面（/router）
- 共 103 个测试全部通过（49 后端 + 54 前端）

### 2.2 现有技术栈

**前端：** React 19 + TypeScript + Vite + Tailwind CSS v4 + React Router DOM 7 + TanStack Query 5 + Axios + Lucide React + Vitest 4

**后端：** Python 3 + FastAPI + SQLAlchemy 2.0 + SQLite + Pydantic v2 + pytest

### 2.3 Quota Manager 的目录位置

沿用现有项目风格：

```
backend/src/
  models/quota.py           # QuotaRecord SQLAlchemy ORM
  schemas/quota.py          # Pydantic schemas
  services/quota_service.py # 额度计算、状态判定、记录更新
  routes/quota.py           # FastAPI route handlers
  data/quota_thresholds.py  # 默认阈值配置

frontend/src/
  types/quota.ts            # TypeScript interfaces
  api/quota.ts              # Axios API client
  hooks/useQuota.ts         # TanStack Query hooks
  pages/
    QuotaOverviewPage.tsx   # 额度概览页面
  components/
    ModelUsageList.tsx      # 模型使用列表
    ModelUsageCard.tsx      # 展开详情卡片
    QuotaConfigForm.tsx     # 额度设置表单
    QuotaAlertBanner.tsx    # 预警条（独立展示用）
    RiskBadge.tsx           # 风险徽章
```

---

## 3. P0 Story / P0 Task

### P0 Stories（5 条）

| story_id | 摘要 | 验收标准 |
|----------|------|----------|
| US-QM-01 | 记录模型调用次数和 token | `POST /quota/record-usage` 接收 usage，累加统计，异步落库 |
| US-QM-02 | 查看模型额度概览 | `GET /quota/overview` 返回 summary + models[]，前端展示统计卡片 + 列表 |
| US-QM-03 | 手动填写额度上限 | `PATCH /quota/models/:modelId/quota` 更新 token_limit，重算 usage_percent |
| US-QM-04 | 额度状态预警和告警 | 状态达到 WARNING/NEAR_LIMIT/LIMITED 时，RiskBadge 颜色变化，预警条展示 |
| US-QM-05 | 额度不足时自动触发 Handoff | LIMITED/COOLDOWN 模型被拦截，触发事件（Handoff Manager 就绪后对接） |

### P0 Tasks

| task_id | 内容 | 类型 | 依赖 |
|---------|------|------|------|
| QM-T1.1 | quota_records 数据库表 | database | 无 |
| QM-T1.2 | QuotaStatus 状态机 + 额度计算逻辑 | backend | QM-T1.1 |
| QM-T2.1 | POST /quota/record-usage API | backend | QM-T1.1 |
| QM-T2.2 | Usage 记录后触发额度重算 | backend | QM-T1.2 / QM-T2.1 |
| QM-T3.1 | GET /quota/overview 概览 API | backend | QM-T1.2 |
| QM-T3.2 | PATCH /quota/models/:modelId/quota 设置额度 API | backend | QM-T1.2 |
| QM-T3.3 | GET /quota/models/:modelId/status 状态查询 API | backend | QM-T1.2 |
| QM-T4.1 | QuotaAlertBanner 组件 | frontend | 无（mock） |
| QM-T4.2 | RiskBadge 组件 | frontend | 无（mock） |
| QM-T4.3 | 对接真实 Quota 数据 | frontend | QM-T3.3 / QM-T4.1 / QM-T4.2 |
| QM-T5.1 | LIMITED 拦截 + 自动 Handoff 触发 | backend | QM-T1.2 / QM-T2.2 |
| QM-T6.1 | QuotaOverviewPage + ModelUsageList（mock） | frontend | 无 |
| QM-T6.2 | 对接真实概览 API + ModelUsageCard | frontend | QM-T3.1 / QM-T6.1 |
| QM-T6.3 | 额度设置表单（ModelUsageCard 内嵌） | frontend | QM-T3.2 / QM-T6.2 |
| QM-T8.1 | 额度计算与状态机单元测试 | test | QM-T1.2 |
| QM-T8.2 | API 集成测试 | test | QM-T2.1 / QM-T3.1 / QM-T3.2 / QM-T3.3 |
| QM-T8.3 | 前端组件测试 | test | QM-T4.1 / QM-T4.2 / QM-T6.1 / QM-T6.2 |

### P1 Tasks（延后）

| task_id | 内容 | 类型 |
|---------|------|------|
| QM-T1.3 | QuotaStatusHistory 表 | database |
| QM-T7.1 | GET /quota/models/:modelId/history API | backend |
| QM-T7.2 | QuotaStatusHistory 时间线组件 | frontend |

---

## 4. 计划新增文件

### 后端（7 个文件）

```
backend/migrations/003_create_quota_records.sql    # quota_records 表迁移
backend/src/models/quota.py                        # QuotaRecord SQLAlchemy ORM
backend/src/schemas/quota.py                       # QuotaRecord schemas
backend/src/services/quota_service.py              # 额度计算 + 状态判定 + 记录更新
backend/src/routes/quota.py                        # API endpoints
backend/src/data/quota_thresholds.py               # 默认阈值配置
backend/tests/test_quota_api.py                    # API 集成测试
backend/tests/test_quota_service.py                # 额度计算单元测试
```

### 前端（10 个文件）

```
frontend/src/types/quota.ts                        # TypeScript interfaces
frontend/src/api/quota.ts                          # Axios API client
frontend/src/hooks/useQuota.ts                     # TanStack Query hooks
frontend/src/pages/QuotaOverviewPage.tsx           # 额度概览页面
frontend/src/components/ModelUsageList.tsx         # 模型使用列表
frontend/src/components/ModelUsageCard.tsx         # 展开详情卡片
frontend/src/components/QuotaConfigForm.tsx        # 额度设置表单
frontend/src/components/QuotaAlertBanner.tsx       # 预警条组件
frontend/src/components/RiskBadge.tsx              # 风险徽章
frontend/src/components/__tests__/QuotaOverviewPage.test.tsx
frontend/src/components/__tests__/QuotaAlertBanner.test.tsx
frontend/src/components/__tests__/RiskBadge.test.tsx
```

### 文档（1 个文件）

```
docs/dev/quota-manager-implementation-plan.md      # 本文件
```

---

## 5. 计划修改文件

```
backend/src/main.py                # 注册 quota 路由 + seed 逻辑
frontend/src/App.tsx               # 添加 /quota 页面入口和导航链接
```

---

## 6. 后端实现顺序

### Phase 1 — 数据模型 + Usage 记录 + 状态计算（第 2 轮）

1. **迁移文件** `003_create_quota_records.sql`
   - 表结构对齐 PRD 11.1 QuotaRecord 接口
   - 索引：idx_provider_model（唯一）、idx_quota_status、idx_usage_percent

2. **ORM** `models/quota.py`
   - QuotaRecord SQLAlchemy model
   - 字段：id, provider, model_id, model_name, request_count, input_tokens, output_tokens, total_tokens, limit_error_count, quota_mode, token_limit, request_limit, cost_limit, reset_period, reset_date, usage_percent, estimated_remaining, quota_status, last_used_at, cooldown_until, handoff_triggered_count, created_at, updated_at

3. **默认阈值** `data/quota_thresholds.py`
   - warning_percent = 0.70
   - near_limit_percent = 0.90
   - cooldown_minutes = 1
   - max_errors_per_hour = 3
   - max_rate_limit_errors = 2

4. **Schemas** `schemas/quota.py`
   - QuotaRecordCreate, QuotaRecordUpdate, QuotaRecordResponse
   - QuotaOverviewResponse, QuotaStatusResponse
   - RecordUsageRequest, UpdateQuotaRequest

5. **Service 层** `services/quota_service.py`
   - `record_usage()` — 查找/创建 QuotaRecord，累加统计，异步落库
   - `calculate_quota_status()` — 基于阈值判定状态
   - `calculate_usage_percent()` — known/estimated/unknown 模式计算
   - `get_overview()` — 概览查询 + summary 统计
   - `update_quota_config()` — 手动设置额度上限
   - `get_model_status()` — 单模型状态查询
   - `check_and_intercept()` — LIMITED/COOLDOWN 拦截检查

6. **API 路由** `routes/quota.py`
   - `POST /quota/record-usage` — 200 + 更新后状态
   - `GET /quota/overview` — 200 + summary + models[]
   - `PATCH /quota/models/:modelId/quota` — 200 + 更新后记录
   - `GET /quota/models/:modelId/status` — 200 + 状态对象

### Phase 2 — 额度拦截 + 事件触发（第 2 轮后半）

7. **LIMITED 拦截逻辑**
   - `check_and_intercept()`：检查 quota_status，LIMITED/COOLDOWN 时返回错误
   - 触发 `quota.exhausted` 事件（内存 EventEmitter，MVP 不引入消息队列）
   - Handoff Manager 就绪后替换为真实调用

---

## 7. 前端实现顺序

### Phase 3 — 额度概览页面（第 3 轮）

1. **类型定义** `types/quota.ts`
   - QuotaRecord, QuotaStatus, QuotaMode, QuotaOverview, QuotaSummary
   - STATUS_COLORS, STATUS_LABELS, STATUS_ICONS

2. **API 封装** `api/quota.ts`
   - recordUsage(), getOverview(), updateQuota(), getModelStatus()

3. **Hooks** `hooks/useQuota.ts`
   - useRecordUsage(), useOverview(), useUpdateQuota(), useModelStatus()

4. **QuotaOverviewPage** 页面
   - 路由 `/quota`
   - 顶部 4 个统计卡片（normal/warning/limited/unknown）
   - ModelUsageList：每行显示 model_name、provider、usage_percent 进度条、quota_status 标签
   - 筛选：provider、quota_status
   - 排序：usage_percent

5. **ModelUsageCard** 展开详情
   - input/output token、request_count、last_used_at
   - limit_error_count、quota_mode
   - [设置额度] 按钮（unknown/estimated 状态可见）

6. **QuotaConfigForm** 额度设置
   - token_limit、request_limit、cost_limit
   - reset_period（daily/weekly/monthly/never）
   - reset_date

### Phase 3 后半 — 预警组件（第 3 轮）

7. **RiskBadge** 组件
   - 6 种状态颜色映射（normal=绿、warning=黄、near_limit=橙、limited=红、cooldown=蓝、unknown=灰）
   - Tooltip 显示 usage_percent 和 estimated_remaining

8. **QuotaAlertBanner** 组件
   - WARNING：黄色预警条，可关闭
   - LIMITED：红色告警条，不可关闭
   - 支持多条叠加（取最高优先级展示）

---

## 8. 测试实现顺序

### 后端测试（第 4 轮）

1. `test_quota_service.py`
   - usage_percent 计算：known/estimated/unknown 模式
   - 状态阈值边界：69.99%=normal、70%=warning、89.99%=warning、90%=near_limit、100%=limited
   - limit_error_count > 0 → limited
   - 状态升降级逻辑
   - 周期重置逻辑

2. `test_quota_api.py`
   - POST /quota/record-usage — 正常/429错误/新模型自动创建
   - GET /quota/overview — 正常/筛选/排序/空列表
   - PATCH /quota/models/:modelId/quota — 正常/负额度/状态自动变化
   - GET /quota/models/:modelId/status — 正常/不存在
   - LIMITED 拦截 — 拦截成功/非 LIMITED 放行

### 前端测试（第 4 轮）

3. `QuotaOverviewPage.test.tsx` — 列表渲染、统计卡片、筛选排序、空状态
4. `QuotaAlertBanner.test.tsx` — WARNING 黄色条 / LIMITED 红色条 / 按钮点击
5. `RiskBadge.test.tsx` — 6 种状态颜色 / Tooltip

---

## 9. Mock 数据说明

| Mock 数据 | 位置 | 原因 | 切换条件 |
|-----------|------|------|----------|
| Handoff 触发 stub | `quota_service.py` | Handoff Manager 未开发 | Handoff Manager 就绪后替换为真实调用 |
| Workspace 预警展示 | `QuotaAlertBanner.tsx` | Workspace 模块未开发 | 先做独立 Quota Overview 页面展示 |
| 实时推送（SSE） | `useQuota.ts` | 轮询替代 | 10 秒轮询间隔，SSE 作为后续优化 |
| 使用趋势图 | 未实现 | MVP-B 功能 | 延后到 Usage Trend 图表开发 |

---

## 10. 真实接口依赖

| 依赖模块 | 当前状态 | 影响 | 应对 |
|----------|----------|------|------|
| Model Router | 已完成 | quota_status 查询供路由评分使用 | Quota Manager 提供 GET /quota/models/:modelId/status |
| Handoff Manager | 未开发 | LIMITED 触发 Handoff 无法完整实现 | Phase 4 用 stub，等 Handoff Manager 就绪后替换 |
| Workspace | 未开发 | 预警条无法在 Workspace 展示 | Phase 3 先做独立 Quota Overview 页面 |
| Agent Registry | 已完成 | agent_station_id 关联 | 直接使用已有 agent_stations 表 |

---

## 11. 风险点

| 风险 | 影响 | 应对 |
|------|------|------|
| Usage 高频写入导致数据库压力 | Phase 1 性能问题 | 直接同步写入（SQLite 足够），MVP 不引入队列；如后期有压力再优化 |
| 额度估算（estimated 模式）算法复杂 | Phase 1 延迟 | MVP 只做 known 和 unknown 模式；estimated 模式后续迭代 |
| 自动 Handoff 依赖 Handoff Manager | Phase 4 无法完整集成 | 先实现 LIMITED 拦截 + 事件触发，Handoff 创建用最小 stub |
| 前端需要实时推送额度状态 | SSE 实现复杂 | 先用轮询（10 秒间隔） |
| QuotaRecord 与 Model 表的 model_id 对齐 | 可能出现不一致 | 使用 models 表已有的 model_id，quota_record 的 model_id 引用 models.id |

---

## 12. 与其他模块的依赖关系

```text
Quota Manager
├── 依赖 Model Router（已完成）
│   └── model_id 来自 models 表
│   └── 提供 quota_status 供 Model Router 评分使用
├── 被 Model Router 依赖（已完成）
│   └── GET /quota/models/:modelId/status → quota_health_score
├── 依赖 Handoff Manager（未开发）
│   └── quota.exhausted 事件 → Handoff Manager 创建 HandoffRecord
├── 被 Workspace 依赖（未开发）
│   └── RiskBadge / QuotaAlertBanner 展示额度状态
├── 依赖 Agent Registry（已完成）
│   └── agent_station_id 关联
└── 被 Runtime 依赖（未开发）
    └── 每次 API 调用后 POST /quota/record-usage
```

---

## 13. 实现计划检查清单

- [x] 已阅读 PRD / Stories / Tasks
- [x] 已分析当前项目结构
- [x] 已明确前端目录（沿用 Agent Registry / Model Router 风格）
- [x] 已明确后端目录（沿用现有风格）
- [x] 已列出新增文件（后端 8 + 前端 11 + 文档 1）
- [x] 已列出修改文件（backend/src/main.py, frontend/src/App.tsx）
- [x] 已区分 mock 数据和真实接口依赖
- [x] 已列出开发顺序（Phase 1 后端 → Phase 2 拦截 → Phase 3 前端）
- [x] 已识别 P0 story（5 条）和 P0 task（17 条）
- [x] 已识别风险点（5 项）
- [x] 已说明与其他模块的依赖关系
- [x] 本轮未修改任何代码

---

## 14. 下一步（第 2 轮）

进入 **第 2 轮：实现数据结构和后端接口**，覆盖 Phase 1~2 任务：

1. `003_create_quota_records.sql` 迁移
2. `models/quota.py` ORM
3. `data/quota_thresholds.py` 默认阈值
4. `schemas/quota.py`
5. `services/quota_service.py`（记录 + 计算 + 状态判定）
6. `routes/quota.py`（4 个 API 端点）
7. `main.py` 注册路由

完成后输出：新增接口列表、请求/响应结构、手动测试方式。
