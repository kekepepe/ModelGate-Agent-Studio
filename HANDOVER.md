# ModelGate Agent Studio — 交接文档

> 本文件是接手者唯一的入口文档：读完能知道项目是什么、现在在哪、代码在哪、坑在哪、下一步是什么。
> 阶段性执行计划不写在这里（各阶段有自己的计划文档，见路线图）；本文只在阶段收尾时更新快照。
> 最后更新：2026-09-15（V1.2.1 P0 重构，取代此前被计划内容污染的版本）。

## 1. 项目一句话

本地可跑的多模型 Agent 协作平台：把多个 LLM 组织成角色化 Station，通过任务拆解、模型路由、
额度感知调度和结构化 Handoff 推进复杂目标，并用本地 Memory / RAG / Skill 把每次执行沉淀为
可复用知识——模型可以换，经验不能丢。

## 2. 当前状态快照

| 项 | 值 |
|---|---|
| 当前版本 | V1.5 ✅ 完成（Evolution Quality Loop）；下一版本 V2.0（Developer Agent OS，按 ROADMAP） |
| 已完成 | V1.0 核心闭环 / V1.1 Handoff+Quota / V1.2 Memory+RAG+Skill |
| 后端 pytest | **509 passed, 1 skipped** |
| 前端 vitest | **183 passed / 38 文件**（typecheck / build / lint 全绿） |
| e2e 验收 | e2e-demo / e2e-handoff / e2e-product-acceptance / **e2e-mcp** / **e2e-parallel** 全 PASS |
| CI | workflow 已就位但**默认静音**（push 不触发；Actions 页手动 `workflow_dispatch` 或 PR 触发） |
| 远程 | `https://github.com/kekepepe/ModelGate-Agent-Studio.git`（main，Keychain 免密） |
| 本地路径 | `/Users/kepeng/codex_project/ModelGate Agent Studio`（**路径含空格，命令行记得加引号**） |

## 3. 代码地图

### 文档权威关系

| 文档 | 角色 |
|---|---|
| `ROADMAP.md` | **版本路线 SSOT**（V1.2.1 → V2.0 阶段定义与边界） |
| `docs/design/2026-09-06-platform-redesign.md` | 架构 SSOT（§8 编号已对齐 ROADMAP） |
| `CHANGELOG.md` | 发布记录 |
| `V1.2.1-plan.md` | 当前阶段执行计划（checkbox 进度） |
| `docs/README.md` | 文档目录与变更规则 |
| `docs/_archive_2026/` | 历史规划 + 已完成阶段计划（只读） |

### 后端（`backend/src/`）

| 路径 | 说明 |
|---|---|
| `main.py` | FastAPI 入口；`verify_provider_config()` 启动期校验 |
| `services/providers/` | **现役 Provider 层**：mock / openai_compatible（provider_factory） |
| `providers/` | **预留层**（litellm）：V1.3 P2 Real Multi-Provider 时启用 |
| `services/runtime_service.py` | Runtime 主实现（调度、执行、验证、handoff 触发点） |
| `services/orchestrator_service.py` | 编排入口 `execute_goal_pipeline` |
| `services/handoff_service.py` | Handoff 状态机 + LLM 摘要（模板兜底） |
| `services/context_service.py` | 上下文包构建：混合排序 + 偏好注入 + 渐进披露 |
| `services/memory_vector_service.py` | 记忆/技能嵌入 + 混合检索 |
| `services/curator_service.py` | Memory/Skill/经验沉淀 + 偏好创建 |
| `services/tool_service.py` | Local Tool Runtime（V1.3 MCP 的基座） |
| `services/state_machine_service.py` | Goal/Task 状态机（flush guard） |
| `alembic/versions/` | 迁移链，head = `0011_memory_skill_embeddings` |

### 前端（`frontend/src/`）

| 路径 | 说明 |
|---|---|
| `App.tsx` | react-router-dom v7 声明式路由（**不是 TanStack Router**） |
| `pages/WorkspacePage.tsx` | 主工作区（3 视图 + Handoff 状态条 + SSE） |
| `pages/EvolutionReviewPage.tsx` | 记忆/技能审批 + 偏好创建 + 知识源管理 |
| `components/ui/` | shadcn 基础件 + `agent-status-badge`（30+ 状态映射） |
| `utils/workspaceViewModel.ts` | 工作区视图模型（ACTIVE_HANDOFF_STATUSES 与后端枚举对齐） |
| `hooks/useRuntimeEvents.ts` | SSE 流（unmount 已修 listener 泄漏） |

### 技术栈（V1.2.1 P0 落锤）

- 后端：Python 3.12（Docker/.python-version）· FastAPI · **SQLAlchemy 2 sync**（无 async，
  V1.4 并行若成瓶颈再评估）· Alembic · SQLite（compose 可切 PG）
- 前端：React 19 · Vite · **React Router v7** · TanStack Query · shadcn/ui · Tailwind v4
- 依赖纪律：**arq/Redis 未安装**（V1.4 才引入）；litellm 保留但运行时未用（V1.3 P2 启用）

## 4. 已知坑（接手者必读）

1. **路径含空格**：`cd "/Users/kepeng/codex_project/ModelGate Agent Studio"` 必须加引号。
2. **shadcn CLI alias bug**：`npx shadcn add` 会写到字面 `./@/` 目录，需手动 `mv`（绕法见 V1.0
   交接历史）。select.tsx 事件已解决（已提交且被引用），但 CLI bug 本身仍在。
3. **httpx 宽 pin**：`httpx>=0.27,<0.29` 与 litellm 1.55.0 的 `httpx<0.28` 约束共存；**动 httpx
   版本前先查 litellm 约束**，别简单 bump。
4. **SQLite naive datetime**：DateTime 列回读是 naive，与 `now(timezone.utc)` 比较会 TypeError。
   quota 的 cooldown 已修（V1.1），recovery_service 有归一化范例——写新的时间比较时照做。
5. **`GET /api/v1/tasks` 必须注册在 `/tasks/{task_id}` 之前**（FastAPI 路径遮蔽）。
6. **`paused` 不是合法 TaskStatus**：前端筛选已排除；新增筛选时记得。
7. **AgentStatusBadge 的 label prop**：传 null 用 `?? undefined`，不能用 `||`。
8. **Task.set_json 只对真实列生效**：曾用 `_get_json("_flag")` 当一次性标记导致静默失败；现在
   用执行日志当标记（见 runtime `_task_has_runtime_log`）。
9. **alembic head 被 `tests/test_alembic_migrations.py` 钉死**：新增迁移必须同步更新该测试。
10. **5 个组件故意不 shadcn 化**（TopStatusBar / WorkspaceModeSwitch / CardFlowRenderer /
    ThreeZoneCardFlow / PixelOfficeRenderer）——自定义布局，不是技术债。
11. **30+ 组件仍是旧 P0-P7 classNames**：计划内欠账，随所在版本顺带收口，不单独立项。
12. **本地 venv 是 Python 3.9**（系统限制），Docker/CI 用 3.12.8：写代码别用 3.10+ 语法
    （match、`X | Y` 类型注解在运行时等）。

## 5. 路线图

见 [`ROADMAP.md`](./ROADMAP.md)。当前：V1.2.1（P0 架构收口 → P1 CI + 产品验收）；
下一主版本 V1.3 = Real Multi-Provider + MCP。各版本边界（做什么/不做什么）在 ROADMAP §各版本边界。

## 6. 工作约定（必须遵守）

- **每个子任务 = 1 commit + 1 push**，绝不攒批；commit 带阶段标签（`docs(v1.2.1):` 等）
- 提交门禁：后端 `pytest -q` 全绿 + 前端 `typecheck / test` 全绿（V1.2.1 P1 起加 ruff）
- 删除原则：仅当"不确定 AND 可简单再生"才删；每次删除/保留记入
  `docs/_archive_2026/v1.0_deletions_log.md`
- 架构/接口/状态机变更：**先改设计文档**再写代码
- 文档分工：本文件只做交接快照；阶段进度在阶段计划文档；发布记录在 CHANGELOG——
  **不再把执行计划内容写进本文件**（faf963e 事故的教训）
- 用户偏好"我定你执行 + 你推荐我拍板"，默认推进，只在必须决策时一次性问完

## 7. 联系方式

solo developer（用户：kekeppe），macOS，主语言中文。