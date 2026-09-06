# ModelGate Agent Studio · 平台重设计（2026-09-06）

> 文档性质：本设计的"出生日"是 2026-09-06。从这天起，**所有架构决策、PRD、任务拆分都以此文档为唯一权威**。旧的 `docs/roadmap/2026-07-*.md` 与 `docs/prd/*-prd.md` 仅作历史参考。
>
> 设计者：Mavis（MiniMax Code 内的 agent）
> 适用版本：V1.0 → V1.4
> 项目代号：MG-AS（ModelGate Agent Studio）
> 仓库：`github.com/kekepepe/ModelGate-Agent-Studio`

---

## 0. TL;DR

| 维度 | 决策 |
|---|---|
| 产品定位 | **面向独立开发者的多模型 Agent 协作控制台**。不是 SaaS，不是企业平台。 |
| 核心差异化 | **多角色 Station + 结构化 Handoff + 真实 LLM 全链路**。 |
| 技术栈（前端） | Vite · React 19 · TypeScript · **TanStack Router** · **shadcn/ui** · Tailwind v4 · **Zustand** · RHF + Zod |
| 技术栈（后端） | Python 3.12 · **FastAPI** · **SQLAlchemy 2 异步** · Alembic · Pydantic v2 · **LiteLLM** · **arq**（Redis 队列） |
| 数据库 | 本地 SQLite / 生产 PostgreSQL（同一套 ORM） |
| Agent 编排 | **保留多角色 Station**（Planner / Coder / Reviewer / Researcher / Summarizer / Supervisor），但每个 Station 都是「可编辑数据」，不是写死代码；用户可克隆/编辑/新建 |
| 实时通信 | **SSE**（run 状态流） + 2s 轮询兜底 |
| 状态机 | Goal / Task / Worker / Handoff 显式状态机，非法跳转直接拒绝 |
| 部署 | Docker Compose（dev + prod 同源） |
| 旧文档 | 归档到 `docs/_archive_2026/`，仅供考古 |
| 旧代码 | 全部重写，不再兼容 |

---

## 1. 产品愿景

### 1.1 一句话

**让独立开发者用一个桌面应用级别的体验，编排多个真实 LLM 协作完成一个 Goal，并完整看到"为什么是这个模型、这个 Agent 做了什么、花了多少 token"的全过程。**

### 1.2 用户

- 一个人开发，但同时拥有 3-5 个 AI Coding Plan（Claude / GPT / DeepSeek / Kimi / GLM / 自建）
- 需要长期处理复杂任务（代码项目、bug 修复、文档生成、跨工具工作流）
- 不想要 ChatGPT 那种聊天界面，想要**任务流控制台**
- 不需要"团队空间 / 权限 / 多用户"

### 1.3 显式不做（V1.x 全周期）

- ❌ 多人协作 / 团队空间 / 权限
- ❌ 移动端适配
- ❌ Agent / Skill / Plugin Marketplace
- ❌ 自动读取第三方 Coding Plan 真实额度（用本地估算）
- ❌ 复杂像素办公室动画（只保留轻量可视化）
- ❌ 自由拖拽 Workflow Builder
- ❌ 自动 commit / 自动 push / 自动合并
- ❌ 通知中心

### 1.4 核心体验闭环

```text
Studio（创建 Team / 选 Goal 模板）
  └─ Workspace（Goal 运行中的唯一主入口）
       ├─ Goal 描述 + 约束 + 完成标准
       ├─ Planner 拆分 → 任务树
       ├─ Router 选模型 → 显示理由
       ├─ Worker 串行/有限并行执行
       ├─ 异常时：Retry / Override Model / Handoff
       ├─ Handoff 在 Task Card 上结构化展示（不离 Workspace）
       ├─ 底部 Console：实时事件 + token + 错误
       └─ 完成后 Supervisor 给 Final Summary
  Logs（按 Goal/Task 全局筛选，纯审计视图）
  Settings（模型 / Provider / Station 模板 / 额度配置）
```

---

## 2. 架构总览

### 2.1 系统图

```text
┌──────────────────────────────────────────────────────────┐
│                     Frontend (Vite SPA)                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │
│  │   Studio   │  │ Workspace  │  │  Logs / Settings   │  │
│  └────────────┘  └────────────┘  └────────────────────┘  │
│         │              │                  │              │
│         └──────────────┴──────────────────┘              │
│                  TanStack Query + SSE                    │
└────────────────────────┬─────────────────────────────────┘
                         │  HTTPS  +  Server-Sent Events
┌────────────────────────┴─────────────────────────────────┐
│                   Backend (FastAPI)                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │  API Layer (Routers)                               │  │
│  │  /api/v1/{goals,tasks,runs,agents,models,logs}    │  │
│  └────────────────────┬───────────────────────────────┘  │
│  ┌────────────────────┴───────────────────────────────┐  │
│  │  Service Layer                                     │  │
│  │  GoalService · TaskService · AgentService ·        │  │
│  │  RouterService · QuotaService · HandoffService ·   │  │
│  │  LogService · RunOrchestrator                      │  │
│  └────────────────────┬───────────────────────────────┘  │
│  ┌────────────────────┴───────────────────────────────┐  │
│  │  Runtime (异步执行)                                 │  │
│  │  StateMachine · Worker · ToolRegistry · Retry      │  │
│  └─────┬──────────┬─────────────┬─────────────────────┘  │
│        │          │             │                         │
│   ┌────┴───┐ ┌────┴────┐  ┌─────┴──────┐                  │
│   │ LiteLLM│ │  arq    │  │ MCP Tools  │                  │
│   └────┬───┘ └────┬────┘  └─────┬──────┘                  │
└────────┼──────────┼─────────────┼──────────────────────────┘
         │          │             │
   ┌─────┴────┐ ┌───┴────┐  ┌────┴─────┐
   │ LLM APIs │ │ Redis  │  │   FS /   │
   │ (统一)   │ │ 队列   │  │  Git /   │
   └──────────┘ └────────┘  │  Shell   │
                            └──────────┘
         ┌──────────────────────────────┐
         │   Database (SQLite / PG)     │
         └──────────────────────────────┘
```

### 2.2 关键技术决策

| 决策 | 为什么 |
|---|---|
| **保留 FastAPI** | 异步生态成熟、Pydantic v2 强类型、独立 dev 最高 ROI |
| **改用 SQLAlchemy 2 异步** | 旧版 sync 在 SSE 并发下会卡 IO；新版 async 是 2026 默认 |
| **LiteLLM 作为 Provider 抽象** | 100+ 模型一个接口，token 计费/重试/streaming 统一；避免自己写 N 个 provider |
| **TanStack Router 替代 React Router** | 完全类型安全的路由 + 搜索参数 + loader，比手写 boilerplate 安全 10 倍 |
| **shadcn/ui 替代自写组件库** | Copy-paste 进项目，零额外依赖，完全可控可改；不锁定在某个 npm 包 |
| **Zustand 替代 Redux/Context** | 50 行解决 80% 场景，比 Redux Toolkit 少 5 倍样板 |
| **SSE 而非 WebSocket** | 单向推状态、HTTP 友好、自动重连、原生浏览器支持足够用 |
| **状态机显式校验** | 老项目状态错乱是头号 bug 源；现在用纯函数 transition 矩阵，任何非法跳转直接 400 |

---

## 3. 领域模型

### 3.1 核心实体

```text
Goal           用户输入的顶层目标
  └─ Task      Planner 拆解的子任务（1..N，有 parent_id 树形）
       └─ WorkerSession  实际执行 Task 的实例（每次执行 / 每次 Handoff 重建）
            ├─ Agent (Station)  角色 + system_prompt + 允许工具
            └─ Model            LLM 标识 + provider

Handoff        WorkerSession 之间交接的结构化记录
  ├─ from_worker / to_worker
  ├─ summary（结构化 JSON，9 字段）
  └─ reason

Model          注册的 LLM（provider/model_name/api_base 等）
Agent          Station（角色 Agent 的可编辑定义）
Tool           MCP 注册的工具 + 权限
QuotaRecord    按 (provider, model_name) 聚合的用量 + 限额
ExecutionLog   不可变事件流（10 种事件类型）
```

### 3.2 状态机（关键）

```text
Goal:        draft → planning → ready → running → {completed, failed, stopped}
Task:        pending → assigned → running → {completed_verified, completed_unverified,
                                              revision_required, failed, cancelled}
Worker:      created → running → {completed, failed, handoff_required}
Handoff:     requested → summary_ready → accepted → {completed, failed, rejected}
```

**所有状态转换走纯函数矩阵**：`can_transition(from, to, ctx) -> bool | TransitionError`。
任何非法转换直接拒绝并记录 ExecutionLog，**不允许数据库层修改绕过**。

### 3.3 关键不变式

- 一个 Goal 同一时刻只能有 1 个 active Task（V1.0）；V1.2 才引入有限并行
- WorkerSession 创建后绑定 Model，**不可热切换 Model**（要切必须新建 Worker + Handoff）
- Handoff 必须**先生成结构化 Summary，再创建 to_worker**（不写空白交接）
- 所有 Quota 计算在**同一事务**里写 `quota_records` + `execution_logs`

---

## 4. Agent 设计（核心）

### 4.1 Station 模型

> Station = "一个角色化 Agent 的可编辑定义"。是**数据**，不是代码。

```typescript
interface Station {
  id: string;                    // UUID
  name: string;                  // "首席 Coder"
  slug: string;                  // 唯一标识 'coder', 'planner', ...
  role: 'planner' | 'coder' | 'reviewer' | 'researcher' | 'summarizer' | 'supervisor' | 'custom';
  description: string;
  system_prompt: string;         // YAML / Markdown，可含变量 {{goal}}, {{task}}
  default_model_id: string;      // FK → Model
  backup_model_ids: string[];
  allowed_tools: string[];       // 白名单 tool slugs
  max_steps_per_task: number;    // 单 Task 内部最大推理步
  handoff_policy: {
    can_initiate: boolean;       // 这个 Station 能否主动交接
    on_quota_exhausted: 'handoff' | 'fail' | 'fallback_backup';
    on_provider_error: 'retry_once' | 'handoff' | 'fail';
  };
  is_builtin: boolean;           // 6 个预制=true，用户新建=false
  is_enabled: boolean;
  created_at, updated_at;
}
```

### 4.2 预制 6 个 Station（出厂）

| Slug | 角色 | 默认模型建议 | Handoff 策略 |
|---|---|---|---|
| `planner` | 任务拆解 + 完成标准制定 | 长上下文强（如 kimi / claude-opus） | on_quota_exhausted=handoff |
| `coder` | 写代码 / 改代码 | 代码强（deepseek-coder / gpt-4 / claude-sonnet） | on_quota_exhausted=handoff, on_provider_error=retry_once |
| `reviewer` | 审查 diff / 给建议 | 推理强（claude-opus / gpt-4） | on_quota_exhausted=fallback_backup |
| `researcher` | 读文档 / 搜资料 | 长上下文 + 工具调用 | on_quota_exhausted=handoff |
| `summarizer` | 把执行结果压成摘要 | 速度快成本低（claude-haiku / gpt-4o-mini） | on_quota_exhausted=fallback_backup |
| `supervisor` | 终审 + 风险标注 | 推理强 | on_quota_exhausted=fallback_backup |

> **关键**：预制只是 seed 数据。代码里**不写死 if role == 'coder'** 这种逻辑。所有行为来自 Station 配置 + 通用 Runtime。

### 4.3 用户扩展方式

- 克隆预制 → 改名 → 改 prompt → 改默认模型 → 改 allowed_tools → 保存
- 全新建：`role=custom`，完全手写
- 启禁用：软删除（`is_enabled=false`），不让 Router 选中
- 删预制：禁止（`is_builtin=true` 时 API 返回 400）

### 4.4 Router

> Router 的输入 = Task 的特征 + 当前所有可用 Station + 所有非 LIMITED 的 Model。输出 = 1 个 Station + 1 个 Model + 评分拆解。

**6 维评分（沿用旧版，权重可调）**：

| 维度 | 权重 | 说明 |
|---|---|---|
| capability_match | 0.25 | Task 所需能力 vs Station 的 allowed_tools + 默认模型能力 |
| role_match | 0.20 | 显式指定 role vs Station.role |
| context_fit | 0.15 | Model 上下文窗口余量 |
| cost_fit | 0.15 | Model 成本等级 + 用户预算偏好 |
| speed_fit | 0.10 | Model 速度等级 + 用户速度偏好 |
| quota_health | 0.10 | 该 Model 剩余额度 |
| historical | 0.05 | 该 (Station, Model) 历史成功率（V1.1 启用） |

返回结构：

```typescript
interface RouteDecision {
  station_id: string;
  model_id: string;
  confidence: number;            // 0..1
  score_breakdown: Record<Dim, number>;
  reasoning: string;             // 人类可读解释
  backup_plan: Array<{ station_id, model_id, score }>;
  risk_flags: string[];
}
```

### 4.5 Handoff（结构化交接）

```typescript
interface HandoffSummary {
  original_goal: string;
  current_task: string;
  completed_work: string[];      // 已经做了
  unfinished_work: string[];    // 还没做
  important_constraints: string[];
  key_decisions: string[];       // 关键判断 + 原因
  errors_and_risks: string[];
  next_suggested_steps: string[];
  context_needed: string[];      // 接手 Agent 必须读的文件 / 资料
  generated_by: 'llm' | 'fallback';  // 是否 LLM 生成（失败时 fallback）
  generated_at: string;
}
```

**流程**：

```text
Worker 触发 Handoff
  → 锁定当前 Task
  → 生成 HandoffSummary（LLM 优先；失败用 fallback 模板）
  → Handoff.status = summary_ready
  → 创建 to_WorkerSession（Station + Model 来自 Router 重新选）
  → 旧 WorkerSession.status = handoff_required（不动 output）
  → 用户在 Workspace 里看到"由 A 交给 B"提示 + [接受] 按钮
  → Handoff.status = accepted
  → Task 继续，to_Worker 继承 inherited_from_handoff_id
  → 完成时 Handoff.status = completed，写入 result_after_handoff
```

> V1.0：Handoff 在 Task Card 上半透明卡片展示，不开新页。V1.1 才加 Handoff 历史列表。

---

## 5. 前端设计

### 5.1 路由（TanStack Router）

```text
/                              → /studio 重定向
/studio                        Team 模板 + 创建 Run
/studio/teams/:teamId          Team 详情（编辑 Station 链）
/studio/teams/:teamId/new-run  Goal 输入弹层

/workspace                     Run 列表（active / recent / failed / completed）
/workspace/$runId              Run 详情（核心页面）
  ├─ /workspace/$runId         默认 Goal 概览
  ├─ /workspace/$runId/task/$taskId   跳到指定 Task 详情侧栏
  └─ /workspace/$runId/logs    Run 范围内 Logs

/logs                          全局日志筛选（按 Goal / Task / Station / Level）
/agents                        Station 列表 + 编辑 + 启禁用
/agents/$stationId             Station 详情 + 试运行
/models                        Model 注册 + 测试连接
/tools                         MCP Tool 列表 + 权限
/settings                      Provider / 额度 / 主题
```

### 5.2 信息架构

**顶层导航**（永远在）：
- Studio · Workspace · Logs · Agents · Models · Tools · Settings

**Workspace 内部**（run 详情页）：
```text
┌─────────────────────────────────────────────────┐
│ TopBar: ← Studio  ·  Goal 标题  ·  Run 状态  ⓘ │ ← 全局
├─────────────────────────────────────────────────┤
│ RunHeader:  Team · Station 链 · Pause/Stop/Export│ ← run 级
├──────────┬──────────────────────┬───────────────┤
│ Task     │ Card Flow / Pixel    │ Task Detail   │
│ Tree     │ (主视图)             │ (侧栏 380px)  │
│ (280px)  │                      │               │
│          │                      │               │
├──────────┴──────────────────────┴───────────────┤
│ Bottom Console (可展开):  Events · Tokens · Errs │ ← run 级
└─────────────────────────────────────────────────┘
```

### 5.3 设计系统

**基调**：**Claude 风**，浅色为主，少量强调色，无深色。

| Token | 值 | 用途 |
|---|---|---|
| `--bg` | `#fafaf9` (stone-50) | 全局背景 |
| `--bg-elevated` | `#ffffff` | 卡片 |
| `--text` | `#1c1917` (stone-900) | 主文字 |
| `--text-muted` | `#78716c` (stone-500) | 次文字 |
| `--border` | `#e7e5e4` (stone-200) | 边线 |
| `--accent` | `#7c3aed` (violet-600) | 强调（不滥用） |
| 状态色 | 沿用旧的：running=blue, handoff=purple, completed=green, failed=red, pending=amber | |

**字体**：系统 sans 为主；代码用 `ui-monospace, SFMono-Regular`。

**组件库**：**shadcn/ui**（基于 Radix UI），需要的就 `npx shadcn add xxx` 拉进 `src/components/ui/`。

**图标**：lucide-react。

**动效**：CSS transform / opacity only，200ms transition。**禁止**复杂 keyframe 动画。

### 5.4 状态管理

```text
服务端状态     → TanStack Query（缓存 + refetch + 失效）
全局 UI 状态   → Zustand stores（theme / sidebar / selected run）
表单状态       → React Hook Form + Zod
URL 状态       → TanStack Router 的 search params（selected task, view mode）
实时事件       → SSE EventSource → 写 TanStack Query cache
```

### 5.5 核心页面

#### Studio
- 顶部 6 个 Team 模板卡片（每个模板固定 Station 链 + 建议 Model）
- 下方"我的 Team"列表
- 进入 Team：编辑 Station 顺序、替换 Model、配额
- "Create Run" 按钮 → Goal 弹层 → 创建 → 跳到 `/workspace/$runId`

#### Workspace（核心）
- 首次进入：显示 Goal + Run Config + "Start" 按钮
- 启动后：任务树实时长出，每完成一个 Task 折叠收缩
- Task Card：状态色 + Station 头像 + Model 名 + 耗时 + 摘要 + 操作（retry / handoff / view）
- 视图切换：Card Flow（默认）/ Pixel Office（极简静态版，1 张图，无动画）
- Task Detail 侧栏：Router 决策、Token、上下文、Logs、Handoff 摘要

#### Logs
- 全局事件流
- 多维筛选：Goal / Task / Station / Model / Level / 类型
- 时间范围
- 单条点击 → 详情 Drawer

#### Agents
- Station 列表（grid）
- 点开：编辑 prompt、默认 Model、允许工具、Handoff 策略
- 顶部"克隆预制"快捷入口
- 禁用 toggle

---

## 6. 后端设计

### 6.1 API（REST + SSE）

```text
/api/v1/stations         GET / POST
/api/v1/stations/:id     GET / PATCH / DELETE (is_enabled only)
/api/v1/stations/:id/test  POST { goal, model_id? } → 同步小执行

/api/v1/models           GET / POST
/api/v1/models/:id       GET / PATCH / DELETE
/api/v1/models/:id/test  POST { prompt } → 连接测试

/api/v1/goals            POST { title, description, station_chain, run_config }
/api/v1/goals/:id        GET
/api/v1/goals/:id/start  POST
/api/v1/goals/:id/stop   POST

/api/v1/tasks/:id        GET
/api/v1/tasks/:id/retry  POST
/api/v1/tasks/:id/handoff POST { to_station_id, to_model_id?, reason }

/api/v1/runs             GET (workspace 列表)
/api/v1/runs/:id         GET (Run 聚合状态)
/api/v1/runs/:id/events  GET (SSE stream)

/api/v1/logs             GET (筛选 + 分页)
/api/v1/logs/:id         GET

/api/v1/quota            GET (概览)
/api/v1/quota/:model_id  PATCH { token_limit, ... }
```

### 6.2 服务层

```text
src/services/
  agents/
    station_service.py        CRUD + 试运行
  runs/
    goal_service.py           Goal 生命周期
    task_service.py           Task 生命周期
    run_orchestrator.py       串联 Goal → Task → Worker
  router/
    router_service.py         评分 + 选择 + 解释
  handoff/
    handoff_service.py        Handoff 状态机 + Summary 生成
  quota/
    quota_service.py          用量记录 + 状态机
  logs/
    log_service.py            不可变事件写入
  models/
    model_service.py          Model 注册 + 测试
  runtime/
    state_machine.py          纯函数 transition
    worker.py                 单 Worker 执行循环
    tool_registry.py          MCP tool 调度
    retry.py                  退避重试
src/providers/
  base.py                     LLMProvider Protocol
  litellm_provider.py         LiteLLM 实现
  mock_provider.py            Mock 实现（dev/test）
```

### 6.3 Runtime 核心

```text
RunOrchestrator.execute(goal_id)
  │
  ├─ 加载 Goal + Station 链
  ├─ for each task in plan:
  │   ├─ RouterService.select(station, model_pool) → RouteDecision
  │   ├─ 创建 WorkerSession(model_id=...)
  │   ├─ Worker.run(task)             ← 内部循环
  │   │   ├─ Observe (读 context / tool results)
  │   │   ├─ Decide (LLM call)
  │   │   ├─ Tool call? → ToolRegistry.execute
  │   │   ├─ Check 完成标准 / max_steps / quota
  │   │   └─ 返回 TaskResult
  │   ├─ 写 ExecutionLog
  │   ├─ 写 QuotaRecord
  │   ├─ 触发 SSE 推送
  │   └─ 若 Handoff: 走 handoff_service
  ├─ Supervisor Station 跑一遍 → Final Summary
  └─ Goal → completed
```

**关键约束**：
- Worker 内部循环有**硬上限**：max_steps / max_tokens / max_wall_time
- Quota 校验在**每次 LLM 调用前**做（不是事后）
- 任何错误 → 写 ExecutionLog + 抛 TransitionError，**不静默吞**

### 6.4 异步与队列

- **V1.0**：直接 `asyncio.create_task` 跑 Worker，不用外部队列（单机够用）
- **V1.3+**：引入 arq + Redis，多 Worker 并行 + 跨进程恢复

### 6.5 Provider 抽象（LiteLLM）

```python
class LLMProvider(Protocol):
    async def chat(
        self,
        messages: list[dict],
        model: str,
        tools: list[dict] | None = None,
        stream: bool = False,
        **kwargs,
    ) -> ChatResponse: ...
    async def stream_chat(self, ...) -> AsyncIterator[Chunk]: ...
    def token_count(self, messages) -> int: ...
```

`litellm_provider.py` 调 LiteLLM；`mock_provider.py` 离线 dev 用。
**禁止**业务代码直接 import litellm。

### 6.6 错误分类

```python
class ProviderError(Exception): ...
class ProviderAuthError(ProviderError): ...
class ProviderRateLimit(ProviderError): ...
class ProviderTimeout(ProviderError): ...
class ProviderContextOverflow(ProviderError): ...
class ProviderInvalidResponse(ProviderError): ...
class QuotaExhausted(ProviderError): ...
class ToolCallError(Exception): ...
class StateTransitionError(Exception): ...
```

所有错误都带 `code` 字段，HTTP 层映射到统一响应。

### 6.7 日志

- **structlog** 结构化 JSON
- 关键字段：goal_id / task_id / station_id / model_id / event_type / level / timestamp
- 写入 `execution_logs` 表（不可变）+ 打印到 stdout（容器里走 Loki 可选）

---

## 7. 数据模型

### 7.1 ER 简图

```text
goals ─┬─ tasks ─┬─ worker_sessions ─┬─ tool_calls
       │         │                   ├─ handoffs (from/to_worker)
       │         │                   └─ execution_logs
       │         ├─ execution_logs
       │         └─ artifacts
       └─ execution_logs

stations (独立表，is_builtin 区分预制/用户)
models   (独立表，provider/model_name/api_base)
quota_records (按 model 聚合)
tools    (MCP tool 元数据 + 权限)
```

### 7.2 主要表

```sql
-- stations
CREATE TABLE stations (
  id              UUID PRIMARY KEY,
  slug            TEXT UNIQUE NOT NULL,
  name            TEXT NOT NULL,
  role            TEXT NOT NULL,
  description     TEXT,
  system_prompt   TEXT NOT NULL,
  default_model_id UUID REFERENCES models(id),
  backup_model_ids JSONB DEFAULT '[]',
  allowed_tools   JSONB DEFAULT '[]',
  max_steps_per_task INT DEFAULT 10,
  handoff_policy  JSONB NOT NULL,
  is_builtin      BOOLEAN DEFAULT FALSE,
  is_enabled      BOOLEAN DEFAULT TRUE,
  created_at, updated_at
);

-- models
CREATE TABLE models (
  id            UUID PRIMARY KEY,
  provider      TEXT NOT NULL,           -- 'openai' / 'anthropic' / 'deepseek' / 'mock'
  model_name    TEXT NOT NULL,
  display_name  TEXT NOT NULL,
  api_base      TEXT,
  capability_tags JSONB DEFAULT '[]',
  cost_level    INT DEFAULT 3,           -- 1..5
  speed_level   INT DEFAULT 3,
  is_enabled    BOOLEAN DEFAULT TRUE,
  created_at, updated_at,
  UNIQUE(provider, model_name)
);

-- goals
CREATE TABLE goals (
  id          UUID PRIMARY KEY,
  title       TEXT NOT NULL,
  description TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'draft',
  station_chain JSONB NOT NULL,          -- 计划用哪几个 Station 链
  run_config  JSONB NOT NULL DEFAULT '{}',
  final_summary TEXT,
  created_at, updated_at
);

-- tasks
CREATE TABLE tasks (
  id              UUID PRIMARY KEY,
  goal_id         UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
  parent_task_id  UUID REFERENCES tasks(id),
  title           TEXT NOT NULL,
  description     TEXT,
  status          TEXT NOT NULL DEFAULT 'pending',
  station_id      UUID REFERENCES stations(id),
  priority        INT DEFAULT 0,
  output          JSONB,
  completion_criteria JSONB,
  tokens_used     INT DEFAULT 0,
  duration_ms     INT,
  created_at, updated_at
);

-- worker_sessions
CREATE TABLE worker_sessions (
  id              UUID PRIMARY KEY,
  task_id         UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  station_id      UUID NOT NULL REFERENCES stations(id),
  model_id        UUID NOT NULL REFERENCES models(id),
  status          TEXT NOT NULL DEFAULT 'created',
  inherited_from_handoff_id UUID,
  total_tokens_used INT DEFAULT 0,
  created_at, updated_at
);

-- handoffs
CREATE TABLE handoffs (
  id              UUID PRIMARY KEY,
  task_id         UUID NOT NULL REFERENCES tasks(id),
  from_worker_id  UUID NOT NULL REFERENCES worker_sessions(id),
  to_worker_id    UUID REFERENCES worker_sessions(id),
  to_station_id   UUID NOT NULL REFERENCES stations(id),
  to_model_id     UUID NOT NULL REFERENCES models(id),
  reason          TEXT NOT NULL,
  summary         JSONB NOT NULL,
  status          TEXT NOT NULL DEFAULT 'requested',
  result_after_handoff TEXT,
  created_at, summary_generated_at, accepted_at, completed_at
);

-- execution_logs (不可变)
CREATE TABLE execution_logs (
  id          BIGSERIAL PRIMARY KEY,
  goal_id     UUID, task_id UUID, station_id UUID, model_id UUID,
  event_type  TEXT NOT NULL,         -- 'goal_started' / 'task_status_change' / 'llm_call' / ...
  level       TEXT NOT NULL,         -- 'info' / 'warn' / 'error'
  payload     JSONB NOT NULL,        -- 完整结构化数据
  created_at  TIMESTAMPTZ DEFAULT now()
);

-- quota_records
CREATE TABLE quota_records (
  id          UUID PRIMARY KEY,
  model_id    UUID NOT NULL REFERENCES models(id),
  date        DATE NOT NULL,
  request_count INT DEFAULT 0,
  input_tokens  INT DEFAULT 0,
  output_tokens INT DEFAULT 0,
  total_tokens  INT GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
  token_limit   INT,
  quota_status  TEXT DEFAULT 'unknown',
  UNIQUE(model_id, date)
);
```

### 7.3 Seed 数据

启动时自动 seed：
- 6 个预制 Station（planner/coder/reviewer/researcher/summarizer/supervisor）
- 6 个常见 Model（OpenAI / Anthropic / DeepSeek / Kimi / GLM / mock）
- 4 个常用 MCP Tool（file_read / file_write / shell_run / git_diff）

---

## 8. 阶段化交付

> 全部阶段由我（Mavis）实现 + 推送到 GitHub。每阶段结束有可运行 demo + 测试通过 + 文档更新。

### V1.0 — 核心闭环（目标：2-3 周）

**目标**：本地能跑 `Goal → Task → Worker → Model → Final Summary`，不接 Handoff / 不接 Quota / 不接并行。

**包含**：
- 后端：FastAPI + SQLAlchemy 异步 + Alembic + LiteLLM + 状态机
- 6 个预制 Station seed
- 6 个预制 Model seed（包含 mock）
- Goal/Task/Worker CRUD + 同步执行
- Router（基础 6 维评分）
- Final Summary
- 前端：Studio + Workspace + 简单 Logs
- 基础设计系统（shadcn/ui + tailwind）
- Docker Compose 起后端 + 前端 + 可选 PG

**验收**：
- `docker compose up` 后浏览器能创建 Run 并看到执行完成
- 后端 pytest 通过
- 前端 build + typecheck 通过

### V1.1 — Handoff + Quota（目标：+1-2 周）

**包含**：
- Handoff 状态机 + Summary 生成（LLM 优先，fallback 模板）
- Quota 记录 + 状态机 + 拦截
- Workspace Task Card 的 Handoff 状态条
- Quota Overview 页

**验收**：
- 模拟 quota 耗尽，能看到 auto-handoff
- Logs 能看到 Handoff 事件链

### V1.2 — 实时 + 打磨（目标：+1 周）

**包含**：
- SSE 实时事件流
- Workspace 状态恢复（URL 刷新继续看）
- Task Detail 侧栏（Router 决策 / Token / Context / Logs tab）
- Pixel Office 简化版（一张静态图，可选）
- 全局错误处理 / Toast / 加载态

### V1.3 — 自定义 Station + MCP（目标：+2 周）

**包含**：
- Agents 页（编辑 / 克隆 / 试运行）
- Models 页（注册 / 测试连接 / 启禁用）
- Tools 页（MCP tool 列表 / 权限）
- Station 试运行（独立小窗口）

### V1.4 — 进阶（按需）

- 有限并行 Task
- Goal 复制 / 模板
- Export Final Summary
- Nightly Provider Benchmark runner
- Postgres + Redis 切换
- (V2.0 再考虑) Memory / Skill / 自进化

---

## 9. 仓库结构

```text
.
├── DESIGN.md                    ← 指向本文档的入口
├── README.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/versions/
│   ├── src/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── api/v1/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── providers/
│   │   ├── runtime/
│   │   ├── middleware/
│   │   └── data/seed.py
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── components.json          ← shadcn 配置
│   ├── src/
│   │   ├── main.tsx
│   │   ├── routes/              ← TanStack Router file-based
│   │   ├── components/
│   │   │   ├── ui/              ← shadcn 生成
│   │   │   └── app/             ← 业务组件
│   │   ├── pages/               ← 路由直接组合的页面
│   │   ├── hooks/
│   │   ├── api/                 ← api 客户端
│   │   ├── stores/              ← zustand
│   │   ├── lib/                 ← 工具
│   │   ├── types/
│   │   └── styles/
│   └── public/
├── docs/
│   ├── DESIGN.md                ← 链接到此文档
│   ├── design/2026-09-06-platform-redesign.md   ← 本文档
│   ├── architecture/            ← 演进中的子设计
│   └── _archive_2026/           ← 旧文档归档
└── .github/
    └── workflows/
        ├── backend-ci.yml
        ├── frontend-ci.yml
        └── integration-ci.yml
```

---

## 10. 推送到 GitHub

- 默认分支：`main`
- 提交规范：`<type>(<scope>): <subject>`（feat / fix / refactor / docs / test / chore）
- 推送策略：每完成一个可验收的子任务就 commit + push（不是攒一大堆）
- 不创建 Release Tag（V1.0 之前不发版）

---

## 11. 给 Mavis 的执行约定

每完成一个阶段：
1. 跑本地验证（test / build / 端到端 demo）
2. 写本阶段的 changelog
3. git commit + push
4. 给用户简报

每个 commit 信息里**必须**包含阶段标签：`[V1.0]` / `[V1.1]` 等。

---

> 文档结束。后续变更请直接修改本文档，**不要**在别处另开新规划文档。
