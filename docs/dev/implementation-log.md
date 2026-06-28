# Implementation Log

---

## Agent Registry

**模块名称：** Agent Registry  
**模块 slug：** `agent-registry`  
**开发周期：** 2026-06-25 ~ 2026-06-27  
**对应 PRD：** `docs/prd/agent-registry-prd.md`  
**对应 Stories：** `docs/stories/agent-registry-stories.md`  
**对应 Tasks：** `docs/tasks/agent-registry-tasks.md`  
**对应 UI Spec：** `docs/ui/agent-registry-ui-spec.md`  

---

### 完成的 Story

| story_id | 故事摘要 | 状态 |
|----------|----------|------|
| US-AR-01 | 查看 Agent Station 列表 | ✅ 完成 |
| US-AR-02 | 创建自定义 Agent Station | ✅ 完成 |
| US-AR-03 | 编辑 Agent Station 配置 | ✅ 完成 |
| US-AR-04 | 启用/禁用 Agent Station | ✅ 完成 |
| US-AR-05 | 使用默认模板创建 Agent | ✅ 完成 |
| US-AR-06 | 查看 Agent 使用统计 | ⏸️ P1 延后 |

---

### 完成的 Task

| task_id | 任务内容 | 状态 |
|---------|----------|------|
| AG-T1.1 | 创建 agent_stations 数据库表 | ✅ |
| AG-T1.2 | 定义 AgentStatus / AgentRole 枚举与校验 | ✅ |
| AG-T2.1 | GET /agents 列表查询 API | ✅ |
| AG-T2.2 | POST /agents 创建 API | ✅ |
| AG-T2.3 | PATCH /agents/:id 编辑 API | ✅ |
| AG-T2.4 | PATCH /agents/:id/status 启用禁用 API | ✅ |
| AG-T3.1 | 6 个模板数据 + GET /agents/templates API | ✅ |
| AG-T3.2 | 模板创建集成到 POST /agents | ✅ |
| AG-T4.1 | AgentRegistryPage + AgentList（列表页） | ✅ |
| AG-T4.2 | 对接真实 API | ✅ |
| AG-T4.3 | AgentConfigForm 创建/编辑共用表单 | ✅ |
| AG-T4.4 | 启用/禁用开关 + 状态变更反馈 | ✅ |
| AG-T4.5 | 模板创建 UI（模板卡片 + 快速创建） | ✅ |
| AG-T6.1 | 后端 API 单元 + 集成测试 | ✅ |
| AG-T6.2 | 前端组件测试 | ✅ |
| AG-T5.1 | GET /agents/:id/stats API | ⏸️ P1 |
| AG-T5.2 | AgentStatsPanel 组件 | ⏸️ P1 |

---

### 新增文件列表

#### 后端

```
backend/migrations/001_create_agent_stations.sql
backend/src/models/agent.py
backend/src/schemas/agent.py
backend/src/services/agent_service.py
backend/src/routes/agents.py
backend/src/data/agent_templates.py
backend/tests/test_agents_api.py
```

#### 前端

```
frontend/src/types/agent.ts
frontend/src/api/agents.ts
frontend/src/hooks/useAgents.ts
frontend/src/pages/AgentRegistryPage.tsx
frontend/src/components/AgentList.tsx
frontend/src/components/AgentConfigForm.tsx
frontend/src/components/AgentTemplateCards.tsx
frontend/src/components/AgentStatusToggle.tsx
frontend/src/components/RoleTag.tsx
frontend/src/components/StatusIndicator.tsx
frontend/src/components/__tests__/AgentList.test.tsx
frontend/src/components/__tests__/AgentConfigForm.test.tsx
frontend/src/components/__tests__/AgentStatusToggle.test.tsx
frontend/src/components/__tests__/AgentTemplateCards.test.tsx
```

#### 文档

```
docs/dev/agent-registry-implementation-plan.md
docs/dev/agent-registry-audit-report.md
docs/dev/agent-registry-fix-report.md
docs/dev/agent-registry-round-progress.md
```

---

### 修改文件列表

```
frontend/src/App.tsx          # 添加 /agents 路由
frontend/src/main.tsx         # 添加 QueryClientProvider + BrowserRouter
```

---

### 新增 API 列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/agents` | 列表查询（支持 role/status/is_enabled/search 筛选 + 分页） |
| GET | `/api/v1/agents/:id` | 详情查询 |
| POST | `/api/v1/agents` | 创建 Agent（支持 template_id 预填充） |
| PATCH | `/api/v1/agents/:id` | 部分更新 |
| PATCH | `/api/v1/agents/:id/status` | 启用/禁用切换 |
| GET | `/api/v1/agents/templates` | 获取 6 个预设模板列表 |

**响应格式：** `{ success: boolean, data?: object, error?: { code, message } }`

---

### 数据对象 / 字段定义

#### AgentStation（后端 SQLAlchemy Model）

```python
id: str (UUID PK)
name: str (required, max 255)
role: str (required, max 50)
description: str (optional)
status: str (default "idle")
current_task_id: str (optional)
default_model_id: str (required)
backup_model_ids: List[str] (JSON 序列化到 Text)
allowed_tools: List[str] (JSON 序列化到 Text)
system_prompt: str (required, default "")
output_format: str (optional)
max_steps_per_task: int (required, default 10, range 1-50)
max_tool_calls_per_task: int (optional, default 20)
allow_handoff: bool (required, default False)
handoff_threshold_tokens: int (optional, range 1000-100000)
is_enabled: bool (required, default True)
total_tasks_completed: int (default 0)
total_tasks_failed: int (default 0)
total_handoffs_initiated: int (default 0)
average_tokens_per_task: int (optional)
created_at: datetime
updated_at: datetime
```

#### AgentStation（前端 TypeScript Interface）

与后端字段一一对应，`AgentListItem` 为列表精简版，`AgentCreateData` / `AgentUpdateData` 为写操作 DTO。

#### 6 个预设模板

| role | 名称 | 默认模型 | Handoff |
|------|------|----------|---------|
| planner | Planner Agent | claude-3-opus | 关闭 |
| coder | Coder Agent | deepseek-coder | 开启 (80k) |
| reviewer | Reviewer Agent | gpt-4-turbo | 开启 (60k) |
| research | Research Agent | kimi-long-context | 开启 (100k) |
| summarizer | Summarizer Agent | claude-3-haiku | 关闭 |
| supervisor | Supervisor Agent | claude-3-opus | 关闭 |

---

### Mock 数据说明

| Mock 数据 | 位置 | 原因 | 切换条件 |
|-----------|------|------|----------|
| MOCK_MODELS (6 个) | `frontend/src/types/agent.ts` | Model Router 模块未就绪 | Model Router 提供 `GET /models` 后切换 |
| MOCK_TOOLS (6 个) | `frontend/src/types/agent.ts` | MCP 模块未就绪 | MCP 提供工具列表 API 后切换 |
| 模板数据 | `backend/src/data/agent_templates.py` | MVP 无需持久化 | 若需用户自定义模板则建表 |

---

### 已知问题

| 问题 | 影响 | 计划修复时机 |
|------|------|-------------|
| default_model_id / backup_model_ids 无硬校验（模型是否存在且启用） | 可能绑定不存在的模型 | Model Router 就绪后 |
| 无 Toast 提示系统 | 操作成功/失败无轻量反馈 | MVP-B 引入 Toast 组件 |
| AgentStats 统计面板未实现 | 无法查看历史使用统计 | P1 功能，延后 |
| 筛选无结果时未提供"清除筛选"按钮 | 体验稍差 | 低优先级 |

---

### 已修复问题（Round 6）

| 问题 | 修复文件 |
|------|----------|
| AgentTemplateCards 缺少单元测试 | 新增 `AgentTemplateCards.test.tsx` |
| running Agent 编辑时无警告横幅 | `AgentConfigForm.tsx` |
| 提交按钮未在表单无效时禁用 | `AgentConfigForm.tsx` |
| 表单提交失败后无 API 错误展示 | `AgentConfigForm.tsx` + `AgentRegistryPage.tsx` |
| AgentStatusToggle mutation 失败无回弹 | `AgentStatusToggle.tsx` |
| Backend 未校验 role 合法性 | `agent_service.py` |

---

### 测试命令和结果

**后端测试：**

```bash
cd backend
./.venv/bin/python -m pytest tests/test_agents_api.py -v
```

结果：**22 passed** (新增 1 个 role 非法校验测试)

**前端测试：**

```bash
cd frontend
npx vitest run src/components/__tests__
```

结果：**28 passed** (新增 AgentTemplateCards 5 个 + AgentConfigForm 更新后 15 个 + AgentList 6 个 + AgentStatusToggle 4 个)

**前端构建：**

```bash
cd frontend
npm run build
```

结果：**构建通过**

---

### 下一步建议

1. **进入 Model Router 模块开发** — Agent Registry 的 model_id 硬校验依赖 Model Router 的模型列表 API。
2. **进入 Handoff Manager 模块开发** — Agent Registry 已提供 `allow_handoff` 和 `handoff_threshold_tokens` 配置，Handoff Manager 可直接读取。
3. **MVP-B 阶段补全** — Toast 系统、AgentStats 统计面板、批量操作。

---

> 日志生成日期：2026-06-27  
> 对应实现计划：`docs/dev/agent-registry-implementation-plan.md`

---

## Model Router

**模块名称：** Model Router  
**模块 slug：** `model-router`  
**开发周期：** 2026-06-27 ~ 2026-06-29  
**对应 PRD：** `docs/prd/model-router-prd.md`  
**对应 Stories：** `docs/stories/model-router-stories.md`  
**对应 Tasks：** `docs/tasks/model-router-tasks.md`  
**对应 UI Spec：** `docs/ui/model-router-ui-spec.md`（缺失，基于 PRD 第 12 节推断）  

---

### 完成的 Story

| story_id | 故事摘要 | 状态 |
|----------|----------|------|
| US-MR-01 | 自动路由选择模型 | 完成 |
| US-MR-02 | 查看路由决策详情 | 完成 |
| US-MR-03 | 手动覆盖路由决策 | 完成 |
| US-MR-04 | 额度不足模型自动排除 | 完成 |
| US-MR-05 | 查看评分拆解矩阵 | 完成 |
| US-MR-06 | 查看路由规则配置 | API 完成，前端页面 P1 延后 |

---

### 完成的 Task

| task_id | 任务内容 | 状态 |
|---------|----------|------|
| MR-T1.1 | 定义模型能力标签 + Routing 数据结构 | 完成 |
| MR-T1.2 | 定义路由规则配置（权重 + 硬约束） | 完成 |
| MR-T2.1 | 候选池筛选（排除 LIMITED/disabled） | 完成 |
| MR-T2.2 | 简单评分实现（规则匹配，让 API 先跑通） | 被 MR-T2.3 直接覆盖 |
| MR-T2.3 | 完整 6 维度评分算法 | 完成 |
| MR-T3.1 | POST /router/select-model（接入评分） | 完成 |
| MR-T3.2 | 升级 select-model 为完整评分 | 完成 |
| MR-T3.3 | POST /router/override-model | 完成 |
| MR-T4.1 | RoutingResultCard 组件（mock 数据） | 完成 |
| MR-T4.2 | 对接真实 API + 卡片交互 | 完成 |
| MR-T4.3 | 评分拆解矩阵 UI | 完成 |
| MR-T4.4 | 手动覆盖模型 UI | 完成 |
| MR-T5.1 | GET /router/rules API | 完成 |
| MR-T5.2 | RouterRulesPage 前端 | P1 延后 |
| MR-T6.1 | 评分引擎单元测试 | 完成 |
| MR-T6.2 | API 集成测试 | 完成 |
| MR-T6.3 | 前端组件测试 | 完成 |

---

### 新增文件列表

#### 后端

```
backend/migrations/002_create_models.sql
backend/src/models/model.py
backend/src/schemas/router.py
backend/src/services/router_service.py
backend/src/routes/router.py
backend/src/data/models.py
backend/tests/test_router_api.py
backend/tests/test_router_service.py
```

#### 前端

```
frontend/src/types/router.ts
frontend/src/api/router.ts
frontend/src/hooks/useModelRouter.ts
frontend/src/pages/ModelRouterPage.tsx
frontend/src/components/RoutingResultCard.tsx
frontend/src/components/ScoreBreakdownPanel.tsx
frontend/src/components/ModelOverrideModal.tsx
frontend/src/components/__tests__/RoutingResultCard.test.tsx
frontend/src/components/__tests__/ScoreBreakdownPanel.test.tsx
frontend/src/components/__tests__/ModelOverrideModal.test.tsx
```

#### 文档

```
docs/dev/model-router-implementation-plan.md
docs/dev/model-router-audit-report.md
```

---

### 修改文件列表

```
backend/src/main.py                # 注册 router 路由 + 模型 seed 逻辑
frontend/src/App.tsx               # 添加 /router 路由和导航链接
```

---

### 新增 API 列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/router/select-model` | 根据任务特征自动选择模型 |
| POST | `/api/v1/router/override-model` | 用户手动覆盖路由决策 |
| GET | `/api/v1/router/rules` | 获取当前路由规则配置 |

**响应格式：** `{ success: boolean, data?: object, error?: { code, message } }`

---

### 数据对象 / 字段定义

#### Model（后端 SQLAlchemy Model）

```python
id: str (UUID PK)
provider: str (required)
model_name: str (required)
display_name: str (required)
capability_tags: List[str] (JSON 序列化到 Text)
max_context_tokens: int (default 8192)
cost_level: int (1-5)
speed_level: int (1-5)
is_enabled: bool (default True)
is_default: bool (default False)
created_at: datetime
updated_at: datetime
```

#### RoutingRequest（前后端共用）

```typescript
task_id: string
goal_id?: string
task_type: string
task_complexity?: string
task_description?: string
required_capabilities?: string[]
preferred_agent_id?: string
preferred_model_id?: string
context_length_estimate?: number
has_vision_input?: boolean
requires_tool_calling?: boolean
budget_preference?: string
speed_preference?: string
```

#### RoutingResult（前后端共用）

```typescript
selected_model_id: string
selected_agent_id?: string
backup_model_ids: string[]
routing_reason: RoutingReason
confidence: number (0-1)
risk_flags: RiskFlag[]
score_breakdown: ScoreBreakdown[]
is_user_override: boolean
override_note?: string
```

#### 6 维度评分

| 维度 | 权重 | 说明 |
|------|------|------|
| capability_match | 0.25 | 任务所需能力与模型能力标签交集比例 |
| role_match | 0.20 | Agent 角色偏好列表中的排名 |
| context_fit | 0.15 | 上下文窗口余量比例 |
| cost_fit | 0.15 | 成本等级反比，受 budget_preference 调整 |
| speed_fit | 0.10 | 速度等级反比，受 speed_preference 调整 |
| quota_health | 0.10 | 额度健康度（mock，等 Quota Manager） |
| historical_performance | 0.05 | 历史表现（mock 0.5，MVP-B 接入） |

**权重动态调整：**
- `budget_preference=low`：cost_fit +0.10，capability_match -0.05
- `speed_preference=fast`：speed_fit +0.10，capability_match -0.05
- `task_complexity=very_complex`：capability_match +0.10，cost_fit -0.05

#### 6 个 Seed 模型

| id | 名称 | 能力标签 | 上下文 | 成本 | 速度 |
|----|------|----------|--------|------|------|
| model-claude-3-opus | Claude 3 Opus | code, planning, reasoning, long_context, tool_calling | 200K | 5 | 3 |
| model-gpt-4-turbo | GPT-4 Turbo | code, planning, reasoning, tool_calling, vision | 128K | 4 | 3 |
| model-deepseek-coder | DeepSeek Coder | code, reasoning, low_cost | 64K | 2 | 3 |
| model-kimi-long-context | Kimi Long Context | long_context, reasoning, summarization | 200K | 3 | 4 |
| model-claude-3-haiku | Claude 3 Haiku | fast, low_cost, summarization | 200K | 1 | 1 |
| model-glm-4 | GLM-4 | vision, tool_calling, multilingual, low_cost | 128K | 2 | 2 |

---

### Mock 数据说明

| Mock 数据 | 位置 | 原因 | 切换条件 |
|-----------|------|------|----------|
| quota_status 查询 | `router_service.py` `_get_mock_quota_status()` | Quota Manager 未就绪 | Quota Manager 提供查询 API 后接入 |
| quota_health 评分 | `QUOTA_HEALTH_SCORES` | 同上 | 同上 |
| historical_performance | `_score_model()` 固定 0.5 | MVP-B 功能 | Model Performance Service 就绪后接入 |
| 前端模型列表 | `frontend/src/types/agent.ts` `MOCK_MODELS` | Model Router 未提供 GET /models | 提供模型列表 API 后切换 |
| WorkerSession 创建 | `override_model()` 仅记录决策 | Worker 模块未就绪 | Worker 模块就绪后补全 |

---

### 已知问题

| 问题 | 影响 | 计划修复时机 |
|------|------|-------------|
| quota_status 为 mock 数据（全 normal） | 额度排除逻辑无法真实验证 | Quota Manager 就绪后 |
| ScoreBreakdownPanel 仅展示 top 模型评分 | PRD 设计图为多模型对比矩阵 | P1 改进，不影响 P0 |
| RouterRulesPage 未实现 | P1 功能缺失 | P1 阶段或 MVP-B |
| 无 `docs/ui/model-router-ui-spec.md` | UI 决策基于 PRD 推断 | 后续补全文档 |

---

### 已修复问题（Round 6）

| 问题 | 修复文件 |
|------|----------|
| Agent `default_model_id` 评分加成缺失 | `router_service.py` `_score_model()` + `select_model()` |
| 默认模型被排除时未添加 `default_model_unavailable` risk_flag | `router_service.py` `_build_risk_flags()` |
| RiskFlag 类型覆盖不全（缺 context_limit / cost_high / speed_slow） | `router_service.py` `_build_risk_flags()` |

---

### 测试命令和结果

**后端测试：**

```bash
cd backend
./.venv/bin/python -m pytest tests/test_router_service.py tests/test_router_api.py -v
```

结果：**27 passed**

**前端测试：**

```bash
cd frontend
npx vitest run src/components/__tests__/RoutingResultCard.test.tsx src/components/__tests__/ScoreBreakdownPanel.test.tsx src/components/__tests__/ModelOverrideModal.test.tsx
```

结果：**26 passed**

**全量测试：**

```bash
# 后端 49 passed（Agent Registry 22 + Model Router 27）
# 前端 54 passed（Agent Registry 28 + Model Router 26）
# 总计 103 passed，零回归
```

**前端构建：**

```bash
cd frontend
npm run build
```

结果：**构建通过**

---

### 下一步建议

1. **进入 Quota Manager 模块开发** — Model Router 的额度感知（quota_health 评分、LIMITED/COOLDOWN 排除）依赖 Quota Manager 提供真实数据。
2. **进入 Handoff Manager 模块开发** — Model Router 已预留 Handoff 路由接口（排除原模型、重新评分），Handoff Manager 可直接调用 `select_model()`。
3. **P1 补全** — RouterRulesPage 前端页面、多模型评分对比矩阵、Toast 提示系统。

---

> 日志生成日期：2026-06-29  
> 对应实现计划：`docs/dev/model-router-implementation-plan.md`  
> 对应自查报告：`docs/dev/model-router-audit-report.md`
