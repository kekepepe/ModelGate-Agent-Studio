# Model Router Implementation Plan

> 生成日期：2026-06-27
> 模块 slug：`model-router`
> 对应文档：PRD / Stories / Tasks（UI Spec 缺失，基于 PRD 第 12 节推断）

---

## 1. 已阅读的文档

1. `docs/prd/model-router-prd.md` — 产品需求（完整，包含评分算法、API Contract、数据对象）
2. `docs/stories/model-router-stories.md` — 5 条 P0 + 1 条 P1 用户故事
3. `docs/tasks/model-router-tasks.md` — 按 Phase 分组的任务拆解
4. `docs/ui/model-router-ui-spec.md` — **不存在**，基于 PRD 第 12 节和 `docs/ui/UI状态与交互动效规则.md` 推断 UI 需求
5. `docs/architecture/API-Contract.md` — 通用 API 响应格式和分页约定
6. `docs/architecture/数据结构与数据库Schema.md` — 状态枚举和数据对象定义
7. `docs/dev/module-development-sop.md` — 7 轮开发 SOP
8. `docs/dev/implementation-log.md` — 已有 Agent Registry 日志（判断项目当前状态）

---

## 2. 当前项目结构判断

### 2.1 已完成模块

Agent Registry 已完成 7 轮开发（2026-06-25 ~ 2026-06-27），包含：
- `agent_stations` 表 + CRUD API（6 个端点）
- Agent Registry 前端页面（`/agents`）
- 28 个前端测试 + 22 个后端测试全部通过

### 2.2 现有技术栈

**前端：**
- React 19 + TypeScript + Vite 8
- Tailwind CSS v4（`@theme` 自定义颜色：stone, lavender, brick）
- React Router DOM 7
- TanStack Query 5（default: retry 1, refetchOnWindowFocus false）
- Axios + Lucide React
- Vitest 4 + Testing Library + jsdom
- Lint: oxlint

**后端：**
- Python 3 + FastAPI + SQLAlchemy 2.0 + SQLite
- Pydantic v2
- pytest + httpx（TestClient）
- 测试数据库：`sqlite:///./test.db`，每次测试 `drop_all` + `create_all`
- API prefix: `/api/v1`
- 统一响应格式：`{ success, data?, error? }`

### 2.3 Model Router 的目录位置

沿用现有项目风格：

```
backend/src/
  models/model.py          # Model ORM（新增表，非覆盖 Agent Registry 的 model.py）
  schemas/router.py        # Pydantic schemas
  services/router_service.py   # 路由评分引擎 + 业务逻辑
  routes/router.py         # FastAPI route handlers
  data/models.py           # 模型 seed 数据（hard-code 能力标签）

frontend/src/
  types/router.ts          # TypeScript interfaces
  api/router.ts            # Axios API client
  hooks/useModelRouter.ts  # TanStack Query hooks
  components/
    RoutingResultCard.tsx      # 路由决策结果卡片
    ScoreBreakdownPanel.tsx    # 6 维度评分拆解
    ModelOverrideModal.tsx     # 手动覆盖模型选择
  pages/
    ModelRouterPage.tsx        # P1 路由规则查看页（延后）
```

---

## 3. P0 Story / P0 Task

### P0 Stories（5 条）

| story_id | 摘要 | 验收标准 |
|----------|------|----------|
| US-MR-01 | 自动路由选择模型 | `POST /router/select-model` 返回 selected_model_id、confidence、backup_model_ids |
| US-MR-02 | 查看路由决策详情 | RoutingResultCard 展示模型名、置信度条、路由理由、risk flags |
| US-MR-03 | 手动覆盖路由决策 | `POST /router/override-model` 支持从 backup 中选择新模型 |
| US-MR-04 | 额度不足模型自动排除 | LIMITED/COOLDOWN 模型被排除，无可用模型时返回 503 + risk_flags |
| US-MR-05 | 查看评分拆解矩阵 | ScoreBreakdownPanel 展示 6 维度评分条和加权得分 |

### P0 Tasks（对应 Tasks 文档 Phase 1~3）

| task_id | 内容 | 类型 | 依赖 |
|---------|------|------|------|
| MR-T1.1 | 定义模型能力标签 + Routing 数据结构 | backend | 无 |
| MR-T1.2 | 定义路由规则配置（权重 + 硬约束） | backend | MR-T1.1 |
| MR-T2.1 | 候选池筛选（排除 LIMITED/disabled） | backend | MR-T1.2 |
| MR-T2.2 | 简单评分实现（规则匹配，让 API 先跑通） | backend | MR-T2.1 |
| MR-T3.1 | `POST /router/select-model`（接入简单评分） | backend | MR-T2.2 |
| MR-T4.1 | RoutingResultCard 组件（mock 数据） | frontend | 无 |
| MR-T4.2 | 对接真实 API + 卡片交互 | frontend | MR-T3.1 / MR-T4.1 |
| MR-T2.3 | 完整 6 维度评分算法 | backend | MR-T2.2 |
| MR-T3.2 | 升级 select-model 为完整评分 | backend | MR-T2.3 |
| MR-T3.3 | `POST /router/override-model` | backend | MR-T3.1 |
| MR-T4.3 | 评分拆解矩阵 UI | frontend | MR-T3.2 |
| MR-T4.4 | 手动覆盖模型 UI | frontend | MR-T3.3 |

### P1 Tasks（延后）

| task_id | 内容 | 类型 |
|---------|------|------|
| MR-T5.1 | `GET /router/rules` API | backend |
| MR-T5.2 | RouterRulesPage | frontend |

---

## 4. 计划新增文件

### 后端（8 个文件）

```
backend/migrations/002_create_models.sql          # models 表迁移
backend/src/models/model.py                        # Model SQLAlchemy ORM
backend/src/schemas/router.py                      # RoutingRequest, RoutingResult, ScoreBreakdown schemas
backend/src/services/router_service.py             # 路由核心服务（筛选 + 评分 + 选择）
backend/src/routes/router.py                       # POST /select-model, POST /override-model, GET /rules
backend/src/data/models.py                         # 6-8 个常用模型的 hard-code seed 数据
backend/tests/test_router_api.py                   # API 集成测试
backend/tests/test_router_service.py               # 评分引擎单元测试
```

### 前端（9 个文件）

```
frontend/src/types/router.ts                       # RoutingRequest, RoutingResult, ScoreBreakdown 类型
frontend/src/api/router.ts                         # selectModel(), overrideModel(), getRules()
frontend/src/hooks/useModelRouter.ts               # useSelectModel, useOverrideModel TanStack Query hooks
frontend/src/components/RoutingResultCard.tsx      # 路由决策结果卡片
frontend/src/components/ScoreBreakdownPanel.tsx    # 6 维度评分拆解展开面板
frontend/src/components/ModelOverrideModal.tsx     # 手动覆盖模型选择弹窗
frontend/src/components/__tests__/RoutingResultCard.test.tsx
frontend/src/components/__tests__/ScoreBreakdownPanel.test.tsx
frontend/src/components/__tests__/ModelOverrideModal.test.tsx
```

### 文档（1 个文件）

```
docs/dev/model-router-implementation-plan.md       # 本文件
```

---

## 5. 计划修改文件

```
backend/src/main.py                # 注册 router 路由：app.include_router(router, prefix="/api/v1")
frontend/src/App.tsx               # 添加 /router 页面入口（P1 延后，Phase 2/3 先以组件形式集成）
```

---

## 6. 后端实现顺序

### Phase 1 — 数据结构 + 简单路由 API（第 2 轮）

1. **迁移文件** `002_create_models.sql`
   - 表结构对齐 PRD 8.3 / Schema 文档 Model 表
   - 字段：id, provider, model_name, display_name, capability_tags(JSON), max_context_tokens, cost_level, speed_level, is_enabled, is_default
   - 索引：idx_provider, idx_is_enabled

2. **ORM** `models/model.py`
   - Model SQLAlchemy model
   - capability_tags 用 JSON 序列化到 Text（同 Agent Registry 的 backup_model_ids 模式）

3. **Seed 数据** `data/models.py`
   - Hard-code 6-8 个模型：claude-3-opus, gpt-4-turbo, deepseek-coder, kimi-long-context, claude-3-haiku, glm-4
   - 每个模型包含能力标签、context_window、cost_level、speed_level

4. **Schemas** `schemas/router.py`
   - RoutingRequest: task_id, task_type, task_complexity, required_capabilities, preferred_agent_id, preferred_model_id, context_length_estimate, budget_preference, speed_preference
   - RoutingResult: selected_model_id, selected_agent_id, backup_model_ids, routing_reason, confidence, risk_flags, score_breakdown
   - ScoreBreakdown: model_id, model_name, total_score, dimension_scores
   - DimensionScore: dimension, score, weight, weighted_score, reason
   - RoutingReason: summary, primary_factors, secondary_factors, tradeoffs
   - RiskFlag: type, severity, message, suggestion

5. **Service 层** `services/router_service.py`
   - `filter_candidates()` — 硬约束筛选：排除 is_enabled=false, 排除 quota_status=LIMITED/COOLDOWN（先用 mock）, 排除 context_window 不足, 排除能力缺失
   - `simple_score()` — 简单评分（Phase 1）：按 task_type 匹配 capability_tags，匹配一个 +0.3 分，其余维度固定 0.5
   - `select_model()` — 调用筛选 + 评分，返回 RoutingResult
   - `override_model()` — 校验 selected_model_id 在 backup_model_ids 中，返回 override 结果

6. **API 路由** `routes/router.py`
   - `POST /router/select-model` — 200 / 503(all_models_limited) / 400
   - `POST /router/override-model` — 200 / 400

### Phase 3 — 完整评分算法（第 6 轮或单独迭代）

7. **完整评分** 升级 `services/router_service.py`
   - 6 维度独立评分函数：capability_match, role_match, context_fit, cost_fit, speed_fit, quota_health
   - 加权求和：confidence = Σ(dimension_score × weight)
   - 权重动态调整：budget/speed/complexity 偏好
   - 置信度修正：risk_flags 和 score_gap 影响
   - 路由理由生成：基于最高评分维度的自然语言描述

---

## 7. 前端实现顺序

### Phase 2 — Workspace 可视化（第 3 轮）

1. **类型定义** `types/router.ts`
   - 与后端 schemas 一一对应

2. **API 封装** `api/router.ts`
   - `selectModel(request)` → POST /router/select-model
   - `overrideModel(request)` → POST /router/override-model

3. **Hooks** `hooks/useModelRouter.ts`
   - `useSelectModel()` — mutation
   - `useOverrideModel()` — mutation

4. **RoutingResultCard 组件**
   - Props: result, onAccept, onOverride
   - 展示：推荐模型名、置信度进度条（0-100%）、路由理由文本、备用模型列表
   - RiskFlagBanner：条件渲染 amber 警告条
   - 按钮：[接受] [切换模型]
   - 5 秒自动收起（hover 重置计时器）

### Phase 3 — 完整功能（第 3 轮后半或第 6 轮）

5. **ScoreBreakdownPanel 组件**
   - 默认收起，点击展开（300ms 过渡）
   - 6 个维度水平进度条，显示原始分数 × 权重 = 加权得分
   - 底部显示加权总和 ≈ confidence

6. **ModelOverrideModal 组件**
   - 从 backup_model_ids 获取备用模型列表
   - 每行展示：模型名、Provider、额度状态
   - LIMITED 模型禁用不可选
   - 确认后调用 overrideModel API

---

## 8. 测试实现顺序

### 后端测试（第 4 轮）

1. `test_router_service.py`
   - 候选池筛选：正常过滤 / 全部 LIMITED / disabled 排除 / 能力缺失排除
   - 简单评分：代码任务优先代码模型 / 规划任务优先长上下文模型
   - 完整 6 维度评分：每个维度独立测试 / 加权求和误差 < 0.001
   - 边界：空候选池 / 单个候选

2. `test_router_api.py`
   - `POST /router/select-model`：正常路由 / 代码任务 / 规划任务 / 全部 LIMITED(503) / 缺少参数(400)
   - `POST /router/override-model`：正常覆盖 / 不在 backup 中(400) / LIMITED 模型(400)

### 前端测试（第 4 轮）

3. `RoutingResultCard.test.tsx`
   - 渲染、置信度条、risk flag 展示、接受/切换按钮点击

4. `ScoreBreakdownPanel.test.tsx`
   - 6 维度渲染、展开/收起、数值计算

5. `ModelOverrideModal.test.tsx`
   - 备用列表渲染、LIMITED 禁用、选择确认

---

## 9. Mock 数据说明

| Mock 数据 | 位置 | 原因 | 切换条件 |
|-----------|------|------|----------|
| 模型能力标签和定价 | `backend/src/data/models.py` | MVP 阶段不建独立配置表 | 用户需要自定义时迁移到 DB |
| quota_status 查询 | `router_service.py` 内部 | Quota Manager 模块未就绪 | Quota Manager 提供查询 API 后接入 |
| quota_health 评分 | `score_engine.py` | 同上 | 接入真实额度数据后替换 |
| WorkerSession 创建 | `override_model()` | Worker 模块未就绪 | Worker 模块就绪后补全创建逻辑 |
| 前端模型列表详情 | `RoutingResultCard` / `ModelOverrideModal` | 仅需要 model_id 和 display_name | Model Registry 提供 GET /models 后切换 |

---

## 10. 真实接口依赖

| 依赖模块 | 当前状态 | 影响 | 应对 |
|----------|----------|------|------|
| Quota Manager | 未开发 | quota_health 无数据来源 | 先用 mock：normal=1.0, warning=0.7, near_limit=0.4 |
| WorkerSession | 未开发 | override-model 无法创建 Worker | 只记录 override 决策，不创建 Worker 实体 |
| Agent Registry | 已完成 | preferred_agent_id 对应的 Agent 存在 | 可直接引用 agent_stations 表 |
| Model 列表 | 本模块新建 | 需要 models 表和 seed 数据 | 本模块自己创建和填充 |

---

## 11. 风险点

| 风险 | 影响 | 应对 |
|------|------|------|
| models 表是新表，与 Agent Registry 的 default_model_id 无硬外键 | 可能引用不存在的模型 | 路由时通过硬约束排除不存在/未启用的模型，形成软性一致性 |
| 6 维度评分算法开发周期长 | Phase 3 延迟 | Task 2.2 先提供简单评分让 API 跑通；Task 2.3 可延后到 Phase 3 |
| UI Spec 缺失 | 前端 UI 决策需要推断 | 基于 PRD 第 12 节和现有 Agent Registry UI 风格推断 |
| RoutingResultCard 需要 Workspace 上下文才能触发 | 独立测试困难 | 先做独立组件（Storybook/mock props），后对接 Workspace |
| 前端 oxlint 可能对新文件报错 | 构建失败 | 沿用现有代码风格，避免复杂类型体操 |

---

## 12. 与其他模块的依赖关系

```text
Model Router
├── 依赖 Agent Registry（已完成）
│   └── preferred_agent_id → agent_stations 表查询
│   └── Agent 的 default_model_id / backup_model_ids 作为评分输入
├── 依赖 Quota Manager（未开发）
│   └── quota_status 查询 → 当前用 mock
├── 被 Handoff Manager 依赖（未开发）
│   └── Handoff 时调用 Model Router 重新选择接手模型
├── 被 Runtime 依赖（未开发）
│   └── Task 执行前调用 Model Router 获取模型
└── 被 Workspace 依赖（未开发）
    └── 展示 RoutingResultCard 和 WorkerBadge
```

---

## 13. 实现计划检查清单

- [x] 已阅读 PRD / Stories / Tasks
- [x] 已分析当前项目结构
- [x] 已明确前端目录（沿用 Agent Registry 风格）
- [x] 已明确后端目录（沿用 Agent Registry 风格）
- [x] 已列出新增文件（后端 8 + 前端 9 + 文档 1）
- [x] 已列出修改文件（backend/src/main.py, frontend/src/App.tsx）
- [x] 已区分 mock 数据和真实接口依赖
- [x] 已列出开发顺序（Phase 1 后端 → Phase 2 前端 → Phase 3 完整功能）
- [x] 已识别 P0 story（5 条）和 P0 task（12 条）
- [x] 已识别风险点（5 项）
- [x] 已说明与其他模块的依赖关系
- [x] 本轮未修改任何代码

---

## 14. 下一步（第 2 轮）

进入 **第 2 轮：实现数据结构和后端接口**，覆盖 Phase 1 任务：

1. `002_create_models.sql` 迁移
2. `models/model.py` ORM
3. `data/models.py` seed 数据
4. `schemas/router.py`
5. `services/router_service.py`（简单评分版）
6. `routes/router.py`（POST /select-model + POST /override-model）
7. `main.py` 注册路由

完成后输出：新增接口列表、请求/响应结构、手动测试方式。
