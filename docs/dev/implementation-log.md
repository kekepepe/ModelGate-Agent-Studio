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
