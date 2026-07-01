# ModelGate Agent Studio 下一步完整开发计划

> 当前阶段：MVP-A Control Plane 已完成，MVP-B Runtime MVP 已完成。  
> 下一阶段目标：把 Runtime MVP 从“API 可执行”推进到“Workspace 可演示、状态可追踪、链路可测试、后续可接真实模型”的稳定版本。

---

## 1. 当前项目状态判断

### 1.1 已完成内容

当前项目已经完成两个核心阶段。

#### MVP-A：Control Plane

已完成 6 个基础模块：

1. Agent Registry
2. Model Router
3. Quota Manager
4. Handoff Manager
5. Logs / Observability
6. Agent Workspace

这些模块已经形成基础管理闭环：

```text
Goal / Task / Agent / Worker / Model / Quota / Handoff / Logs / Workspace
```

#### MVP-B-1：Runtime MVP

已完成 Runtime 最小执行链路：

```text
Goal
→ Router 选模型
→ Quota 检查
→ WorkerSession 创建
→ Mock Model 调用
→ Logs 写入
→ Quota 记录
→ Task / Agent 状态更新
→ Handoff 拦截或继续执行
```

当前测试结果：

```text
Backend: 157 passed
Frontend: 145 passed
Total: 302 passed
Status: 零回归
```

### 1.2 当前项目已经具备的价值

当前项目已经不是普通的多 API 管理工具，而是已经具备了一个多模型 Agent 协作平台的基础形态：

1. 有 Agent 角色管理。
2. 有模型能力路由。
3. 有额度感知机制。
4. 有任务交接机制。
5. 有执行日志记录。
6. 有 Workspace 可视化入口。
7. 有 Runtime 执行链路雏形。
8. 有较完整的前后端测试。

### 1.3 当前最主要的短板

当前短板不是“模块不够多”，而是：

```text
Runtime 还没有变成一个稳定、可演示、可复现的端到端工作流。
```

具体表现为：

1. Workspace 虽然能触发执行，但运行态展示还不够完整。
2. Runtime 执行状态还需要统一查询接口。
3. 还没有完整 E2E 证明 Goal → Task → Worker → Model → Logs → Quota → Handoff → Final Output 的闭环。
4. Mock Provider 已完成，但真实 OpenAI-compatible Provider 尚未接入。
5. Supervisor 审查还没有进入完整 Runtime 链路。
6. Memory / RAG / Skill 自进化还没有开始实现。

---

## 2. 下一阶段总目标

下一阶段不要急着扩展 Memory、RAG、Skill 或 MCP，而是先完成：

```text
Runtime E2E Demo & Stabilization
```

核心目标是：

> 让用户在 Workspace 输入或选择一个 Goal 后，可以点击执行，并清楚看到 Task 状态变化、模型路由结果、Worker 执行状态、日志刷新、额度记录、Handoff 触发和最终输出。

换句话说，下一阶段要把当前系统从：

```text
API 可以跑
```

推进到：

```text
用户可以看懂整个 Agent 协作执行过程
```

---

## 3. 下一步总体开发路线

建议后续按 8 个阶段推进。

```text
阶段 0：补 Runtime Implementation Log
阶段 1：Runtime E2E Demo & Stabilization
阶段 2：真实 Provider 接入
阶段 3：Supervisor 审查链路
阶段 4：Memory / RAG / Skill 自进化 MVP
阶段 5：MCP / Tool Layer MVP
阶段 6：可视化与统计增强
阶段 7：部署、演示与工程包装
```

优先级如下：

| 阶段 | 名称 | 优先级 | 是否立即做 |
|---|---|---:|---:|
| 阶段 0 | Runtime Implementation Log | P0 | 是 |
| 阶段 1 | Runtime E2E Demo & Stabilization | P0 | 是 |
| 阶段 2 | 真实 Provider 接入 | P1 | 阶段 1 后做 |
| 阶段 3 | Supervisor 审查链路 | P1 | 阶段 2 后做 |
| 阶段 4 | Memory / RAG / Skill 自进化 MVP | P1 | Runtime 稳定后做 |
| 阶段 5 | MCP / Tool Layer MVP | P2 | 后期做 |
| 阶段 6 | 可视化与统计增强 | P2 | 穿插做 |
| 阶段 7 | 部署、演示与工程包装 | P0 / P1 | Demo 稳定后马上做 |

---

# 阶段 0：补 Runtime Implementation Log

## 0.1 目标

补写本轮 Runtime MVP 的实现记录，方便后续 Claude Code、Codex 或其他模型接手时快速理解 Runtime 当前状态。

## 0.2 建议新增文件

```text
docs/implementation/runtime-mvp-implementation-log.md
```

## 0.3 文件内容结构

```markdown
# Runtime MVP Implementation Log

## 1. 本轮目标
实现最小可运行的 Goal → Task → Worker → Model → Logs → Quota → Handoff 执行链路。

## 2. 新增文件
- backend/src/services/mock_provider.py
- backend/src/services/runtime_service.py
- backend/src/schemas/runtime.py
- backend/src/routes/runtime.py
- backend/tests/test_mock_provider.py
- backend/tests/test_runtime_service.py
- backend/tests/test_runtime_api.py
- frontend/src/types/runtime.ts
- frontend/src/api/runtime.ts

## 3. 修改文件
- backend/src/main.py
- frontend/src/hooks/useWorkspace.ts
- frontend/src/pages/WorkspacePage.tsx
- frontend/src/components/BottomConsole.tsx

## 4. 当前执行链路
Goal → Router 选模型 → Quota 检查 → WorkerSession 创建 → Mock Model 调用 → Logs 写入 → Quota 记录 → Task/Agent 状态更新 → Handoff

## 5. 测试结果
- Backend: 157 passed
- Frontend: 145 passed
- Total: 302 passed

## 6. 当前限制
- 仍使用 Mock Provider
- 尚未接入真实 OpenAI-compatible Provider
- Workspace 运行态展示仍需增强
- Handoff 接手后的继续执行还需要验证
- Supervisor 审查尚未进入完整 Runtime 链路

## 7. 下一步
进入 Runtime E2E Demo & Stabilization。
```

## 0.4 验收标准

完成后需要满足：

1. 文档存在于 `docs/implementation/`。
2. 记录新增文件和修改文件。
3. 记录 Runtime 执行链路。
4. 记录测试结果。
5. 记录当前限制和下一步。

---

# 阶段 1：Runtime E2E Demo & Stabilization

## 1.1 阶段目标

把 Runtime MVP 从“API 可执行”变成“Workspace 可演示、状态可追踪、链路可测试”。

本阶段结束后，项目应该可以完成一条稳定 Demo：

```text
用户创建 Goal
→ 系统创建 Task
→ 点击执行
→ Router 选择模型
→ WorkerSession 被创建
→ Mock Provider 输出结果
→ Logs 实时刷新
→ Quota 写入记录
→ Task 状态更新
→ Workspace 同步展示
→ 触发或不触发 Handoff
→ 最终输出展示
```

## 1.2 本阶段不要做什么

本阶段限制：

1. 不做完整 Memory / RAG / Skill。
2. 不做复杂 MCP 工具调用。
3. 不大改页面结构。
4. 不一次性接入多个真实模型。
5. 不做复杂动画。
6. 不做企业级权限。

## 1.3 任务 1：新增 RuntimeRun / RuntimeStatus

### 目标

当前 Runtime 只有执行 API，但 Workspace 需要一个稳定的状态读取入口。

建议引入最小 RuntimeRun 概念。

### 建议数据结构

```text
RuntimeRun
- run_id
- goal_id
- status
- started_at
- ended_at
- current_task_id
- total_tasks
- completed_tasks
- failed_tasks
- handoff_count
- final_output
- error_message
```

### 建议状态枚举

```text
pending
running
completed
failed
handoff_required
cancelled
```

### 建议新增后端 API

```text
GET /runtime/status/{goal_id}
GET /runtime/runs/{run_id}
GET /runtime/runs/{run_id}/events
```

最小版本可以先只做：

```text
GET /runtime/status/{goal_id}
```

### 验收标准

1. 执行 Goal 后可以通过 `GET /runtime/status/{goal_id}` 查询整体状态。
2. 返回当前运行状态、任务进度、当前任务、已完成数量、失败数量、Handoff 数量和最终输出。
3. 前端 Workspace 不需要再从多个接口手动拼接 Runtime 状态。
4. 后端新增单元测试或集成测试。

---

## 1.4 任务 2：优化 Workspace 运行态展示

### 目标

让用户在 Workspace 能看懂 Runtime 正在做什么。

### 优先补充内容

| 功能 | 优先级 | 说明 |
|---|---:|---|
| Task 卡片状态同步 | P0 | 显示 pending / running / completed / failed / handoff |
| Worker / Agent 工位显示模型名 | P0 | 显示当前 Worker 使用哪个模型 |
| RoutingResultCard 自动弹出 | P0 | 显示为什么选择该模型 |
| RiskBadge 接入 Quota / Handoff 状态 | P0 | 显示额度风险和交接原因 |
| BottomConsole 日志实时刷新 | P0 | 展示执行过程 |
| FinalOutputPanel | P1 | 展示最终输出 |
| Handoff timeline | P2 | 后续增强 |

### Workspace 理想展示效果

```text
左侧：Goal 输入 / 当前 Goal
中间：Agent Station / Worker / Task 卡片状态
右侧：Task Detail / Routing Result / RiskBadge / Final Output
底部：Runtime Logs / Execution Events
```

### 验收标准

1. 点击执行后，Task 卡片状态能从 pending 变为 running，再变为 completed 或 handoff。
2. 当前 Worker 能显示绑定模型。
3. 如果 Router 完成选择，前端能展示 RoutingResultCard。
4. 如果 Quota 风险出现，前端能展示 RiskBadge。
5. 执行日志能自动刷新。
6. 执行完成后能看到最终输出。

---

## 1.5 任务 3：新增三条核心 E2E / 集成测试

本阶段至少补 3 条核心测试。

### E2E 1：正常 Goal 执行完成

验证链路：

```text
创建 Goal
创建 3 个 Task
点击执行
所有 Task completed
Logs 有记录
Quota 有记录
Workspace 状态更新
Final Output 生成
```

验收标准：

1. Goal 状态变为 completed。
2. 所有 Task 状态变为 completed。
3. 至少生成一条 WorkerSession。
4. 至少生成一条 execution_log。
5. 至少生成一条 quota_record。
6. RuntimeStatus 返回 completed。

### E2E 2：Quota 风险触发 Handoff

验证链路：

```text
设置某模型 quota 接近限制
执行 Task
Quota Manager 拦截
Handoff Record 创建
Task 状态进入 handoff / blocked / waiting
Workspace 显示 RiskBadge
Logs 记录 handoff reason
```

验收标准：

1. RuntimeStatus 返回 handoff_required 或对应状态。
2. HandoffRecord 被创建。
3. Logs 中记录 handoff reason。
4. Workspace 显示 quota risk。
5. Task 状态正确变化。

### E2E 3：execute-step 单步执行

验证链路：

```text
选择一个 Task
点击执行单步
只执行当前 Task
不影响其他 Task
TaskDetailPanel 更新
BottomConsole 日志刷新
```

验收标准：

1. 只有目标 Task 状态变化。
2. 其他 Task 保持 pending。
3. 当前 Task 有 execution_log。
4. RuntimeStatus 能反映当前进度。
5. 前端页面无报错。

---

## 1.6 任务 4：整理 Runtime 事件流

### 目标

让 Runtime 执行过程可以用事件表达，方便前端展示，也方便后续 Memory、RAG、Skill 使用。

### 建议事件类型

```text
runtime.started
runtime.completed
runtime.failed
task.started
task.completed
task.failed
router.selected_model
quota.checked
quota.risk_detected
worker.created
model.called
log.created
handoff.created
handoff.completed
final_output.generated
```

### 最小实现方式

早期不一定新增复杂事件表，可以先复用 execution_logs。

建议给 execution_logs 增加或规范以下字段：

```text
event_type
run_id
goal_id
task_id
agent_id
model_id
message
metadata
created_at
```

### 验收标准

1. 每次 Runtime 执行能形成清晰事件顺序。
2. BottomConsole 可以按时间顺序展示事件。
3. RuntimeRun / RuntimeStatus 可以读取这些事件。
4. 后续 Memory Curator 能基于这些事件复盘任务。

---

# 阶段 2：真实 Provider 接入

## 2.1 阶段目标

在 Mock Provider 稳定后，接入一个真实 OpenAI-compatible Provider。

不要一次性接入所有模型，先只做一个通用 Provider。

## 2.2 建议新增结构

```text
backend/src/services/providers/base.py
backend/src/services/providers/mock_provider.py
backend/src/services/providers/openai_compatible_provider.py
backend/src/services/providers/provider_factory.py
```

## 2.3 Provider Protocol

建议统一接口：

```python
class ModelProvider(Protocol):
    async def generate(self, request: ModelRequest) -> ModelResponse:
        ...
```

### ModelRequest

```text
- provider
- model
- messages
- temperature
- max_tokens
- tools
- metadata
```

### ModelResponse

```text
- content
- input_tokens
- output_tokens
- total_tokens
- latency_ms
- raw_response
- finish_reason
```

## 2.4 OpenAI-compatible Provider 支持配置

最小字段：

```text
base_url
api_key
model_name
temperature
max_tokens
timeout
```

## 2.5 错误处理

必须处理：

1. API key 缺失。
2. base_url 错误。
3. 模型不存在。
4. 请求超时。
5. 429 rate limit。
6. 5xx provider error。
7. 返回格式不符合预期。

## 2.6 验收标准

1. Mock Provider 仍然可用。
2. OpenAI-compatible Provider 可以通过配置启用。
3. Runtime 可以选择 mock 或 real provider。
4. 真实调用结果能写入 logs。
5. token usage 能写入 quota。
6. 所有测试保持通过。
7. 没有 API key 泄露到前端或日志。

---

# 阶段 3：Supervisor 审查链路

## 3.1 阶段目标

让 Runtime 执行完成后，不是直接结束，而是进入 Supervisor 审查。

Supervisor 负责判断：

1. Task 是否完成。
2. 输出是否符合 Goal。
3. 是否存在遗漏。
4. 是否需要返工。
5. 是否可以生成最终结果。

## 3.2 最小 Supervisor 流程

```text
所有 Task completed
→ Runtime 汇总 Task outputs
→ Supervisor Agent 读取 Goal / Tasks / Outputs / Logs
→ 生成 Review Result
→ 判断 passed / needs_revision / failed
→ passed 时生成 final_output
→ needs_revision 时创建补充 Task
```

## 3.3 建议新增对象

```text
SupervisorReview
- review_id
- goal_id
- run_id
- status
- summary
- issues
- suggested_tasks
- passed
- created_at
```

## 3.4 建议新增 API

```text
POST /runtime/review/{goal_id}
GET /runtime/review/{goal_id}
```

## 3.5 验收标准

1. Runtime 执行完成后可以触发 Supervisor Review。
2. Supervisor 能读取 Task 输出并生成审查结果。
3. 审查通过时 Goal 才进入 completed。
4. 审查不通过时可以生成 suggested_tasks。
5. Workspace 能显示 Supervisor Review 结果。

---

# 阶段 4：Memory / RAG / Skill 自进化 MVP

## 4.1 阶段目标

在 Runtime 和 Supervisor 稳定后，开始实现自进化机制。

核心目标：

```text
任务完成后，系统自动生成 Memory Draft 和 Skill Draft，由用户审核后写入本地知识库。
```

## 4.2 不要一开始做完整自动记忆

早期必须采用：

```text
自动生成草稿 + 用户确认后保存
```

不要让系统自动把所有内容写入长期知识库，避免污染记忆。

## 4.3 建议新增模块

```text
Knowledge Base
Skill Library
Evolution Review
Memory Curator Service
Skill Distiller Service
```

## 4.4 Memory 类型

建议从 6 类开始：

```text
raw_memory
session_memory
project_memory
user_memory
agent_memory
skill_memory
```

## 4.5 Memory Draft 数据结构

```text
MemoryDraft
- draft_id
- source_run_id
- source_goal_id
- type
- title
- content
- confidence
- reason
- tags
- human_approved
- created_at
```

## 4.6 Skill Draft 数据结构

```text
SkillDraft
- skill_draft_id
- source_run_id
- name
- scenario
- input_requirements
- steps
- recommended_agents
- recommended_models
- tools
- output_format
- success_criteria
- common_failures
- status
- created_at
```

## 4.7 自进化 MVP 流程

```text
RuntimeRun completed
→ Supervisor Review passed
→ Memory Curator 读取 Goal / Tasks / Logs / Handoff / Final Output
→ 提取 Project Memory / User Memory / Agent Memory
→ Skill Distiller 判断是否可形成 Skill
→ 生成 MemoryDraft / SkillDraft
→ 用户在 Evolution Review 页面审核
→ 通过后写入 Knowledge Base / Skill Library
```

## 4.8 建议新增页面

```text
/knowledge
/skills
/evolution-review
```

## 4.9 验收标准

1. 完成任务后能生成 MemoryDraft。
2. 能区分 Project Memory、User Memory、Agent Memory、Skill Memory。
3. 用户可以 approve / reject / edit draft。
4. approved memory 能写入知识库。
5. SkillDraft 可以保存为 Skill。
6. 新任务开始前可以检索相关 Memory。
7. 所有 Memory 都有来源 run_id / goal_id。

---

# 阶段 5：MCP / Tool Layer MVP

## 5.1 阶段目标

让 Agent Runtime 不只调用模型，也能安全调用工具。

但早期只做最小 Tool Layer，不做复杂插件市场。

## 5.2 最小工具范围

建议先支持：

1. File Read Tool
2. File Search Tool
3. Git Diff Tool
4. Test Runner Tool
5. Browser Search Tool later

## 5.3 Tool Permission Policy

每个 Agent 需要配置允许工具。

示例：

```text
Coder Agent:
- read_file
- write_file
- run_test
- git_diff

Research Agent:
- web_search
- read_pdf
- search_knowledge

Supervisor Agent:
- read_logs
- read_outputs
- compare_results
```

## 5.4 Tool Call Log

每次工具调用必须记录：

```text
ToolCallLog
- tool_call_id
- run_id
- task_id
- agent_id
- tool_name
- input
- output
- status
- error
- created_at
```

## 5.5 安全限制

早期必须限制：

1. 不允许默认删除文件。
2. 不允许默认执行高风险 shell 命令。
3. 不允许访问用户隐私目录。
4. 不允许自动提交 git commit。
5. 所有高风险工具需要用户确认。

## 5.6 验收标准

1. Runtime 可以根据 Agent 权限加载工具。
2. 工具调用能写入 ToolCallLog。
3. Workspace 能显示工具调用记录。
4. 未授权工具调用会被拒绝。
5. 工具错误不会中断整个 Runtime，而是进入可恢复错误状态。

---

# 阶段 6：可视化与统计增强

## 6.1 阶段目标

在 Runtime 稳定后，补齐之前延后的 P1 / P2 展示能力。

## 6.2 优先级重排

| 功能 | 优先级 | 建议时机 |
|---|---:|---|
| RiskBadge 集成 | P0 | 阶段 1 |
| RoutingResultCard 自动弹出 | P0 | 阶段 1 |
| Workspace E2E 测试 | P0 | 阶段 1 |
| Token 统计聚合 | P1 | 阶段 2 后 |
| QuotaStatusHistory | P1 | 阶段 2 后 |
| Usage Trend 图表 | P1 | 有真实调用数据后 |
| Handoff 前后对比视图 | P1 | Handoff 接手执行稳定后 |
| AgentStats 统计面板 | P2 | 后期 |
| RouterRulesPage | P2 | 后期 |
| 完整像素办公室动画 | P2 | Demo 稳定后 |

## 6.3 建议补充页面能力

### Logs 页面

增强：

1. event_type 过滤。
2. run_id 过滤。
3. task_id 过滤。
4. model_id 过滤。
5. token 聚合。
6. Handoff 前后对比。

### Quota 页面

增强：

1. usage trend。
2. token trend。
3. model risk status。
4. per-provider usage。
5. per-goal usage。

### Agent 页面

增强：

1. AgentStats。
2. 成功率。
3. 平均执行时间。
4. 常用模型。
5. Handoff 次数。

### Workspace 页面

增强：

1. 运行态动画。
2. Handoff timeline。
3. 模型选择说明。
4. Final output panel。
5. Supervisor review panel。
6. Memory draft prompt。

---

# 阶段 7：部署、演示与工程包装

## 7.1 阶段目标

把项目变成可以展示、可以录屏、可稳定部署的完整作品。

## 7.2 部署与工程化

需要补：

1. Docker Compose 稳定启动。
2. 数据库迁移固化。
3. `.env.example`。
4. README 启动说明。
5. Seed demo data。
6. 一键 reset demo data 脚本。
7. 前后端生产构建验证。
8. GitHub Actions CI。

## 7.3 Demo 数据

建议准备固定演示数据：

```text
Goal:
帮我为一个 Next.js 项目设计登录模块开发方案，并生成开发任务拆解。

Tasks:
1. 分析登录模块需求
2. 设计 API 与数据结构
3. 生成前端页面任务
4. 生成测试计划

Agents:
- Planner Agent
- Coder Agent
- Reviewer Agent
- Supervisor Agent

Models:
- Claude Mock
- GPT Mock
- DeepSeek Mock

Handoff 场景:
DeepSeek Mock quota risk → Handoff to Claude Mock
```

## 7.4 README 结构

建议 README 结构：

```markdown
# ModelGate Agent Studio

## 1. 项目简介
## 2. 解决的问题
## 3. 核心功能
## 4. 技术架构
## 5. 功能截图
## 6. Runtime 执行链路
## 7. Agent / Model / Handoff 设计
## 8. 本地运行
## 9. 测试结果
## 10. Roadmap
```

## 7.5 Demo 视频脚本

建议录制 2 分钟 Demo：

```text
0:00 - 0:15 展示项目首页和定位
0:15 - 0:35 展示 Agent Registry 和 Model Router
0:35 - 0:55 展示 Quota 和 Handoff 机制
0:55 - 1:35 在 Workspace 执行一个 Goal
1:35 - 1:50 展示 Logs 和 Quota 记录
1:50 - 2:00 展示最终输出和项目亮点总结
```

---

# 立即下一轮开发建议

## 推荐下一轮名称

```text
Runtime E2E Demo & Stabilization
```

## 下一轮目标

```text
把 Runtime MVP 从“API 可执行”推进到“Workspace 可演示、状态可追踪、链路可测试”。
```

## 下一轮任务清单

### P0 任务

1. 新增 Runtime Implementation Log。
2. 设计 RuntimeRun / RuntimeStatus。
3. 新增 `GET /runtime/status/{goal_id}`。
4. Workspace 接入 RuntimeStatus。
5. Task 卡片状态同步。
6. Worker 工位显示当前模型。
7. RoutingResultCard 自动弹出。
8. RiskBadge 接入 Quota / Handoff。
9. Final Output 展示。
10. 新增 3 条核心 E2E / 集成测试。

### P1 任务

1. Runtime events 结构规范。
2. BottomConsole 展示事件类型。
3. RuntimeRun 详情页或详情面板。
4. Handoff 状态可视化增强。
5. 测试 fixture / seed demo data。

### 暂缓任务

1. 真实 Provider。
2. Memory / RAG / Skill。
3. MCP 工具调用。
4. 复杂像素动画。
5. Usage Trend 高级图表。
6. RouterRulesPage。

---

# 下一轮 Claude Code 提示词

```text
请基于当前已完成的 Runtime MVP，执行下一轮开发：Runtime E2E Demo & Stabilization。

本轮目标：
把 Runtime 从“API 可执行”推进到“Workspace 可演示、状态可追踪、链路可测试”。

当前已完成：
- backend/src/services/mock_provider.py
- backend/src/services/runtime_service.py
- backend/src/schemas/runtime.py
- backend/src/routes/runtime.py
- POST /runtime/execute/{id}
- POST /runtime/execute-step/{id}
- frontend/src/types/runtime.ts
- frontend/src/api/runtime.ts
- Workspace 执行按钮
- BottomConsole 2s 日志轮询
- 后端 157 passed，前端 145 passed，总计 302 passed

本轮任务：

1. 新增文档：
   - docs/implementation/runtime-mvp-implementation-log.md
   - 记录上一轮 Runtime MVP 的目标、新增文件、修改文件、执行链路、测试结果、当前限制和下一步。

2. 设计并实现最小 RuntimeRun / RuntimeStatus 查询能力：
   - 至少支持 GET /runtime/status/{goal_id}
   - 返回 goal_id、status、current_task_id、total_tasks、completed_tasks、failed_tasks、handoff_count、final_output、error_message 等字段。

3. 优化 Workspace 运行态展示：
   - Task 卡片显示 pending / running / completed / failed / handoff 状态。
   - Worker / Agent 工位显示当前执行模型。
   - Router 完成后展示 RoutingResultCard。
   - Quota 风险或 Handoff 触发时展示 RiskBadge。
   - 执行完成后展示 final_output。
   - BottomConsole 保持日志轮询并展示 Runtime 事件。

4. 新增测试，至少覆盖：
   - 正常 Goal 执行完成。
   - Quota 风险触发 Handoff。
   - execute-step 只执行单个 Task。

5. 保持所有现有测试通过，不允许回归。

限制：
- 本轮仍使用 Mock Provider。
- 不接入真实模型。
- 不做完整 Memory / RAG / Skill。
- 不做 MCP 工具调用。
- 不大改现有页面结构，只增强 Runtime 状态联动和演示链路。

完成后请输出：
- 新增文件清单
- 修改文件清单
- Runtime 状态链路说明
- Workspace 展示变化
- E2E / 集成测试覆盖说明
- 最终测试结果
- 下一步建议
```

---

# 本阶段完成后的里程碑判断

完成 Runtime E2E Demo & Stabilization 后，项目可以进入新的里程碑：

```text
MVP-B：Runtime Closed Loop Completed
```

达到该里程碑时，项目应该可以这样描述：

> ModelGate Agent Studio 已完成从 Goal 输入、任务执行、模型路由、Worker 运行、日志记录、额度监控、任务交接到 Workspace 可视化展示的端到端闭环，并通过前后端自动化测试验证核心链路稳定性。

这时项目就可以开始做两件事：

1. 接入真实 Provider。
2. 录制 Demo / 整理 README / 完善文档。

---

# 最终优先级结论

当前不要平均补所有功能，应该按以下顺序推进：

```text
1. Runtime Implementation Log
2. RuntimeRun / RuntimeStatus
3. Workspace 运行态展示
4. Runtime E2E 测试
5. Demo 数据与录屏
6. 真实 OpenAI-compatible Provider
7. Supervisor 审查
8. Memory / RAG / Skill 自进化
9. MCP Tool Layer
10. 部署与工程包装
```

一句话总结：

> 下一步的核心不是继续堆模块，而是把 Runtime 做成一条稳定、可视化、可测试、可录屏的端到端 Agent 协作 Demo。
