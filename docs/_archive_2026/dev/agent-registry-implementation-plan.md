# Agent Registry Implementation Plan

> 生成日期：2026-06-25
> 模块：Agent Registry
> 模块 slug：agent-registry

---

## 1. 已阅读文档

1. `docs/prd/agent-registry-prd.md` — Agent Registry 产品需求
2. `docs/stories/agent-registry-stories.md` — 6 条用户故事（5 P0 + 1 P1）
3. `docs/tasks/agent-registry-tasks.md` — 17 条开发任务
4. `docs/ui/agent-registry-ui-spec.md` — UI 设计规范

---

## 2. 当前项目结构判断

项目处于从零初始化阶段，已完成基础框架搭建：

```text
ModelGate Agent Studio/
├── frontend/          # React 18 + TypeScript + Vite + Tailwind CSS v4
│   ├── src/
│   ├── package.json
│   └── vitest.config.ts
├── backend/           # Python 3.9 + FastAPI + SQLAlchemy + SQLite
│   ├── src/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── database.py
│   │   │   └── config.py
│   │   └── routes/
│   │       └── agents.py
│   ├── tests/
│   └── migrations/
└── docs/
    ├── prd/
    ├── stories/
    ├── tasks/
    ├── ui/
    └── dev/
```

---

## 3. 计划新增文件

### 后端（8 个文件）

| 文件路径 | 说明 |
|---------|------|
| `backend/migrations/001_create_agent_stations.sql` | 数据库表结构 |
| `backend/src/models/agent.py` | AgentStation SQLAlchemy Model |
| `backend/src/schemas/agent.py` | Pydantic Schema（Create/Update/Response） |
| `backend/src/services/agent_service.py` | CRUD + 校验逻辑 |
| `backend/src/data/agent_templates.py` | 6 个角色模板硬编码数据 |
| `backend/src/routes/agents.py` | 6 个 API 路由 |
| `backend/tests/test_agents_api.py` | API 集成测试 |
| `backend/tests/test_agent_service.py` | Service 单元测试 |

### 前端（11 个文件）

| 文件路径 | 说明 |
|---------|------|
| `frontend/src/types/agent.ts` | AgentStation / AgentTemplate 类型定义 |
| `frontend/src/api/agents.ts` | Axios 封装的 API 调用 |
| `frontend/src/hooks/useAgents.ts` | React Query hooks |
| `frontend/src/pages/AgentRegistryPage.tsx` | 主页面（路由 `/agents`） |
| `frontend/src/components/AgentList.tsx` | Agent 列表组件 |
| `frontend/src/components/AgentConfigForm.tsx` | 创建/编辑共用表单 |
| `frontend/src/components/AgentTemplateCards.tsx` | 模板选择卡片 |
| `frontend/src/components/AgentStatusToggle.tsx` | 启用/禁用开关 |
| `frontend/src/components/RoleTag.tsx` | 角色标签 |
| `frontend/src/components/StatusIndicator.tsx` | 状态指示灯 |
| `frontend/src/components/__tests__/*.test.tsx` | 组件测试 |

---

## 4. 计划修改文件

| 文件路径 | 修改内容 |
|---------|----------|
| `frontend/src/App.tsx` | 添加 `/agents` 路由 |
| `frontend/src/index.css` | 已完成 Tailwind v4 主题色配置 |
| `backend/src/main.py` | 确认 agents router 已 include |

---

## 5. 后端实现顺序

```text
1. migrations/001_create_agent_stations.sql  — 数据库表
2. src/models/agent.py                       — SQLAlchemy Model
3. src/schemas/agent.py                      — Pydantic Schema
4. src/data/agent_templates.py               — 6 个模板
5. src/services/agent_service.py             — Service 层
6. src/routes/agents.py                      — API 路由
7. tests/test_agents_api.py                  — 集成测试
8. tests/test_agent_service.py               — 单元测试
```

---

## 6. 前端实现顺序

```text
1. src/types/agent.ts                        — 类型定义
2. src/api/agents.ts                         — API 封装
3. src/hooks/useAgents.ts                    — 数据 hook
4. src/components/RoleTag.tsx                — 基础组件
5. src/components/StatusIndicator.tsx        — 基础组件
6. src/components/AgentList.tsx              — 列表组件
7. src/components/AgentConfigForm.tsx        — 表单组件
8. src/components/AgentTemplateCards.tsx     — 模板卡片
9. src/components/AgentStatusToggle.tsx      — 开关组件
10. src/pages/AgentRegistryPage.tsx          — 主页面
11. src/App.tsx                              — 添加路由
```

---

## 7. 测试实现顺序

```text
1. backend/tests/test_agents_api.py          — 后端 API 测试（与后端开发并行）
2. backend/tests/test_agent_service.py       — 后端 Service 测试（与后端开发并行）
3. frontend/src/components/__tests__/AgentList.test.tsx
4. frontend/src/components/__tests__/AgentConfigForm.test.tsx
5. frontend/src/components/__tests__/AgentStatusToggle.test.tsx
```

---

## 8. Mock 数据说明

| 位置 | 用途 | 切换方式 |
|------|------|----------|
| `frontend/src/api/agents.ts` | Agent 列表 mock | 通过 `USE_MOCK` 常量切换 |
| `frontend/src/api/models.ts` | 模型下拉 mock（Model Router 未就绪） | hard-code 6 个常用模型 |

MVP 阶段允许 mock 的位置：
- 前端模型下拉列表（`GET /models` 未实现）
- 前端工具列表（`GET /tools` 未实现）
- AgentStats 面板数据（P1，依赖其他模块）

---

## 9. 真实接口依赖

| 接口 | 依赖模块 | 当前状态 | 应对策略 |
|------|---------|---------|----------|
| `GET /models` | Model Router | 未实现 | 前端 hard-code 6 个模型 |
| `GET /tools` | MCP 工具层 | 未实现 | 前端 hard-code 常用工具 |
| `GET /agents/:id/stats` | WorkerSession / ExecutionLog | 未实现 | P1 延后，API 返回 0 |

---

## 10. 风险点

| 风险 | 等级 | 应对措施 |
|------|------|----------|
| Model Router 未就绪，模型校验无法做硬校验 | 中 | model_id 校验暂时软处理，允许任意字符串 |
| 前端 model 下拉无真实数据源 | 低 | hard-code 6 个模型，标记为 mock |
| AgentStats 依赖其他模块数据 | 低 | P1 功能延后，stats API 做防御性编程 |
| Python 3.9 与 Pydantic v2 兼容性 | 低 | 已验证 pydantic 2.13.4 安装成功 |
| 项目从零搭建，环境配置问题 | 中 | 第 1 轮已验证前后端可独立运行 |

---

## 11. 本模块与其他模块的依赖关系

```text
Agent Registry
├── 被 Runtime 调用：读取 AgentStation 配置执行任务
├── 被 Model Router 调用：读取 default_model_id / backup_model_ids
├── 被 Handoff Manager 调用：读取 allow_handoff / handoff_threshold_tokens
├── 被 Workspace 调用：读取 AgentStation 列表和状态
└── 依赖 Model Router：模型列表（软依赖，mock 兜底）
```

---

## 12. P0 Story / P0 Task

### P0 Stories（必须完成）

| Story | 编号 | 核心验收点 |
|-------|------|-----------|
| 查看 Agent Station 列表 | US-AR-01 | `GET /agents` + AgentList 组件 |
| 创建自定义 Agent Station | US-AR-02 | `POST /agents` + 创建表单 |
| 编辑 Agent Station 配置 | US-AR-03 | `PATCH /agents/:id` + 编辑表单 |
| 启用/禁用 Agent Station | US-AR-04 | `PATCH /agents/:id/status` + Switch |
| 使用默认模板创建 Agent | US-AR-05 | `GET /agents/templates` + 模板卡片 |

### P0 Tasks（必须完成）

| Task | 编号 | 类型 |
|------|------|------|
| 创建 agent_stations 表 | AG-T1.1 | database |
| 定义状态枚举与校验 | AG-T1.2 | backend |
| GET /agents 列表查询 | AG-T2.1 | backend |
| POST /agents 创建 | AG-T2.2 | backend |
| PATCH /agents/:id 编辑 | AG-T2.3 | backend |
| PATCH /agents/:id/status | AG-T2.4 | backend |
| 模板数据 + templates API | AG-T3.1 | backend |
| 模板创建集成 | AG-T3.2 | backend |
| AgentRegistryPage + AgentList | AG-T4.1 | frontend |
| 对接真实 API | AG-T4.2 | frontend |
| AgentConfigForm | AG-T4.3 | frontend |
| 启用/禁用开关 | AG-T4.4 | frontend |
| 模板创建 UI | AG-T4.5 | frontend |

---

## 13. Implementation Plan 文件路径

`docs/dev/agent-registry-implementation-plan.md`（本文档）
