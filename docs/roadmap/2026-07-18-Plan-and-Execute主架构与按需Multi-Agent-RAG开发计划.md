# ModelGate Agent Studio：Plan-and-Execute 主架构、按需 Multi-Agent 与共享 RAG 开发计划（P0–P2）

> 制定日期：2026-07-18  
> 文档性质：下一阶段 Runtime、Knowledge 与 Workspace 的统一开发基线。  
> 关联文档：  
> - [真正 Agent 化改造计划](ModelGate-Agent-Studio-真正Agent化改造计划.md)  
> - [下一阶段产品与开发总方案](2026-07-14-下一阶段产品与开发总方案.md)  
> - [团队模板与 Dify 式易用性改造计划](2026-07-17-团队模板与Dify式易用性改造计划.md)  
> - [双模式工作区与团队模板融合改造方案](2026-07-17-双模式工作区与团队模板融合改造方案.md)

---

## 1. 核心决策

ModelGate 下一步统一采用以下架构原则：

> **Plan-and-Execute 是主架构，Multi-Agent 是按需执行策略，RAG 是共享上下文层。**

这三者不是三个平级产品模式，也不能被理解为“每个任务必须经过多个 Agent，并且每个 Agent 都必须调用一次 RAG”。

正确关系是：

```text
用户 Goal
  ↓
Orchestrator 判断任务复杂度、风险、工具和上下文需求
  ↓
选择执行模式
  ├─ direct：直接回答，不创建多余 Agent
  ├─ single_agent：一个 Agent 完成工具循环
  ├─ sequential_multi_agent：多个能力按依赖顺序执行
  └─ parallel_multi_agent：只有独立且低冲突的任务才并行
  ↓
所有规划和执行角色按需使用统一 Context Service
  ↓
工具执行、证据验证、Replan、Handoff、Supervisor 验收
```

### 1.1 产品定位

不建议将产品定位为普通的“Multi-Agent RAG 平台”。推荐定位为：

> ModelGate Agent Studio 是一个可视化、可验证的 Multi-Agent Plan-and-Execute 工作区。系统通过共享 RAG、动态模型路由、真实工具执行、Handoff 和验证证据，让 Agent 能够规划、执行、验证和修复真实任务。

### 1.2 必须避免的错误方向

1. 简单问答也固定创建 Planner、Coder、Reviewer。
2. 团队模板直接等同于固定执行链。
3. 每个 Agent 维护互相隔离的知识库和检索逻辑。
4. 只要存在知识库，就在每个 Task 前强制做向量检索。
5. Planner 只输出一段自然语言计划，Runtime 无法执行或修改。
6. Reviewer 只给文字意见，不产生返工 Task。
7. 模型声称“已经完成”就把 Goal 标记为完成。
8. 为了让像素工位显得热闹而伪造并行 Agent。

---

## 2. 当前实现基线与真实差距

当前项目已经具备 Plan-and-Execute 的部分骨架，不需要推倒重做。

| 能力 | 当前状态 | 下一步差距 |
|---|---|---|
| Goal 规划 | `orchestrator_service.plan_goal()` 可创建 Task | 仍以关键词和团队预设为主，不是模型驱动的结构化 Orchestrator |
| Task Graph | Task 已保存 `dependencies` | 需要正式 Plan 对象、Plan 版本、变更原因与图级校验 |
| 依赖调度 | `ready_tasks()` 能选择依赖已完成的 Task | 需要循环检测、跳过、取消、动态插入和重规划后的图更新 |
| 并行执行 | `parallel_safe` 可触发隔离执行 | 并行判断仍简单，需要冲突风险、资源预算和合并策略 |
| Agent 选择 | 已按 capability 映射部分角色 | 仍依赖固定 role 映射，需要 Capability Registry 和候选评分 |
| 验证 | 已有 acceptance criteria、Artifact、VerificationResult | 需要统一 Completion Contract 和 Goal 级证据门禁 |
| Replan | Supervisor 可创建 `Replan:` 子 Task | 只覆盖部分验证失败场景，需要运行中统一 Replan 协议 |
| Handoff | 已有摘要、接手 Worker 与状态追踪 | 需要纳入 Orchestrator 决策，并区分 Replan、Retry、Handoff |
| Memory / Skill | 完成后可生成草稿并人工审核 | 需要提升检索质量、使用反馈和错误知识治理 |
| RAG | `context_service` 可检索已审核 Memory/Skill | 当前是轻量关键词重合评分，缺少文档接入、Chunk、混合检索和 Rerank |
| Workspace | 已有 Card Flow / Pixel Office 双模式 | 需要展示计划模式、激活理由、Context 来源和真实动态 Task Graph |

### 2.1 当前架构可以保留的部分

- `Goal → Task → Worker → Tool → Verification` 数据主线。
- `Task.dependencies` 和 `ready_tasks()` 调度入口。
- `required_capabilities`、`required_tools`、`acceptance_criteria`。
- `WorkerSession.current_context` 和 Workspace Scope。
- Artifact、VerificationResult、ExecutionLog。
- HandoffRecord 和接手 Worker 机制。
- Supervisor Review 与 Replan 子 Task。
- MemoryDraft、SkillDraft 和人工审核机制。
- Workspace 双模式渲染及 Agent Detail Modal / Popover。

### 2.2 不应继续扩大的临时实现

- 在 `_preset_specs()` 中持续添加更多固定角色链。
- 在 `plan_goal()` 中持续添加更多关键词判断。
- 用 Agent 名称代替 capability 选择。
- 用 Task 标题前缀推断真实运行语义。
- 把所有 Knowledge 对象继续塞进 `MemoryDraft` 而不区分来源文档、Chunk、运行 Memory 和 Skill。

---

## 3. 目标架构

```text
┌─────────────────────────────────────────────────────────────┐
│ Goal Intake                                                  │
│ 目标、约束、完成标准、Workspace、预算、风险、Team Policy     │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Shared Context Service                                       │
│ Workspace 文件 / 代码索引 / 项目知识 / Memory / Skill       │
│ 权限过滤 / Hybrid Retrieval / Rerank / Context Budget       │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Orchestrator                                                 │
│ direct / single / sequential / parallel                     │
│ 输出结构化 ExecutionPlan、Task Graph 和选择理由              │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Task Graph Scheduler                                         │
│ 依赖、并发、预算、重试、暂停、审批、动态插入、取消            │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Agent Worker Loop                                            │
│ Observe → Decide → Tool → Observe → Verify                  │
│ 每个 Task 获取任务级 Context Package                         │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Verifier / Supervisor                                        │
│ complete / revise / replan / handoff / ask_user / blocked   │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Evolution                                                    │
│ Memory Draft / Skill Draft / Routing Rule Draft / 人工审核   │
└─────────────────────────────────────────────────────────────┘
```

### 3.1 Shared Context Service 的调用时机

RAG 不是只在 Worker 开始前调用一次。目标态至少有四个受控调用点：

| 阶段 | 检索目的 | 默认策略 |
|---|---|---|
| Goal Intake 后 | 帮助 Orchestrator 理解项目和历史约束 | 项目概览、架构文档、相关历史 Goal；低数量高精度 |
| Plan 生成后 | 校验计划是否遗漏关键文件、规则和依赖 | 根据每个候选 Task 做轻量检索 |
| Task 执行前 | 形成任务级 Context Package | 按 capability、工具、Workspace Scope 和 Token 预算检索 |
| 验证 / Replan 时 | 找到验收规则、历史失败和修复经验 | 验证证据、失败日志、相关 Skill 和 Handoff Memory |

### 3.2 Team Template 的新定位

Team Template 不再表示固定调用顺序，而是表示一组可用能力和默认政策：

```json
{
  "name": "代码交付团队",
  "available_capabilities": ["planning", "code_edit", "test", "review"],
  "default_models": {},
  "allowed_tools": [],
  "execution_policy": {
    "prefer_single_agent_for_small_change": true,
    "review_required_for_high_risk": true,
    "max_parallel_tasks": 3
  }
}
```

同一个“代码交付团队”应能产生不同调用路径：

```text
解释一个函数
→ direct

修改一个文案
→ single Coder

修复 Bug 并测试
→ Coder → Verifier

同时修改前端和后端
→ Planner → [Frontend Worker || Backend Worker] → Verifier

高风险数据库迁移
→ Planner → Coder → Reviewer → Human Approval
```

---

## 4. P0：建立真正的 Plan-and-Execute 主闭环

### 4.1 P0 目标

让同一套 Runtime 能根据不同 Goal 产生明显不同、可执行、可解释的调用路径，并在执行失败后修改计划，而不是继续扩展固定 Planner → Coder → Reviewer 模板。

### 4.2 P0-1：定义结构化 Planning Contract

新增正式 `ExecutionPlan` Schema：

```json
{
  "plan_id": "",
  "version": 1,
  "task_mode": "direct | single_agent | sequential_multi_agent | parallel_multi_agent",
  "goal_summary": "",
  "assumptions": [],
  "required_context": [],
  "activation_reason": "",
  "tasks": [
    {
      "client_task_id": "task-1",
      "objective": "",
      "task_type": "direct | research | coding | verification",
      "required_capabilities": [],
      "required_tools": [],
      "dependencies": [],
      "acceptance_criteria": [],
      "risk_level": "low | medium | high",
      "parallel_safe": false,
      "context_query": "",
      "approval_required": false
    }
  ],
  "final_acceptance_criteria": [],
  "human_approval_points": [],
  "estimated_cost": {},
  "fallback_reason": null
}
```

必须校验：

- Task ID 唯一。
- dependencies 指向存在的 Task。
- 任务图无环。
- direct 模式只能有零个或一个执行 Task。
- parallel Task 不能写入相同 Workspace Scope，除非有明确合并策略。
- 每个写任务必须有至少一个可验证完成条件。
- 高风险任务必须声明审批点或 Reviewer。

### 4.3 P0-2：实现模型驱动 Orchestrator

改造 `orchestrator_service.py`：

1. 将当前关键词判断保留为 `RuleBasedPlanningFallback`，不再作为主 Planner。
2. 新增 `ModelOrchestrator`，要求模型按 Planning Contract 输出 JSON。
3. 增加 JSON Schema 校验、修复重试和最大规划次数。
4. 规划输入包含：Goal、完成标准、Team Policy、可用 capability、工具权限、预算、初次 Context Package。
5. 保存模型原始输出、结构化计划、修复记录和最终选择理由。
6. 无可用真实模型时明确进入 fallback，并在 Workspace 标注“规则兜底计划”。

Orchestrator 必须先回答：

1. 是否需要拆 Task。
2. 是否需要工具。
3. 是否需要项目上下文。
4. 是否需要多个 capability。
5. 是否真的可以并行。
6. 是否需要验证或人工审批。

### 4.4 P0-3：正式化 Task Graph Scheduler

在当前 `ready_tasks()` 基础上增加：

- DAG 循环检测和无效依赖阻断。
- `skipped`、`cancelled`、`waiting_approval`、`replanning` 状态。
- Task 动态插入、替换和取消。
- Plan Version 与 Task 来源追踪。
- 并行度、Token、时长和工具资源限制。
- 无 Ready Task 但仍有未完成 Task 时，输出明确 blocked 原因。
- 每次调度选择都写入 `ExecutionLog`。

建议新增事件：

```text
plan.created
plan.validated
plan.fallback_used
plan.replan_requested
plan.updated
task.ready
task.skipped
task.blocked
task.cancelled
task.parallel_group_started
```

### 4.5 P0-4：统一 Replan 协议

不能只在 Goal 最后由 Supervisor 创建 `Replan:` Task。以下场景都可以触发 Replan：

- 工具执行连续失败。
- 验收条件无法满足。
- Context 证明原假设错误。
- Workspace 文件发生冲突。
- 预算不足，需要缩小范围。
- 用户修改 Goal 或完成标准。
- Handoff 接手方发现上下文不完整。

统一决策结果：

```text
complete
revise_current_task
replan_graph
handoff
ask_user
blocked
```

Replan 必须：

- 创建新的 Plan Version，不覆盖旧计划。
- 保存触发原因和证据。
- 标记保留、取消、新增和替换的 Task。
- 不重复执行已经验证完成且仍然有效的 Task。
- 在 Workspace 中显示计划变更前后差异。

### 4.6 P0-5：把验证升级为完成门禁

Task 完成必须同时满足：

```text
模型输出完成声明
+ 必要 Artifact 存在
+ Completion Contract 通过
+ VerificationResult 通过
+ 无未处理高风险问题
```

代码任务至少支持：

- `diff_exists`
- `tests_pass`
- `lint_pass`
- `build_pass`
- `file_exists`
- `command_exit_code`
- `user_approval`

Goal 只有在所有必要 Task 满足终态条件后才允许 `completed`。否则必须进入 `revision_required`、`blocked`、`ask_user` 或 `failed`。

### 4.7 P0-6：Workspace 前端改造

#### Plan 区

- 显示 `task_mode`。
- 显示“为什么直接执行 / 为什么启用多个 Agent / 为什么并行”。
- 显示 Plan Version 和 Replan 次数。
- 执行前允许用户确认、修改或降级计划。
- 区分模型计划和规则 fallback 计划。

#### Card Flow / Pixel Office

- 只显示已经被计划激活的工位。
- 未激活 Agent 不应伪装成等待执行。
- 并行 Task 使用真实分叉线和并行状态。
- Replan 显示任务图变化，而不是简单追加一张卡片。
- Handoff 显示责任和上下文转移；Replan 显示计划改变，两者视觉语义不同。

#### Agent Detail Modal / Popover

- Overview：激活原因、Task、状态、模型。
- Context：检索内容、来源、使用原因、Token 占用。
- Tools：真实调用及结果。
- History：Task 状态、Replan、Handoff 和验证事件。

### 4.8 P0 验收场景

| 场景 | 预期路径 |
|---|---|
| “解释这个函数做什么” | direct；不创建 Planner、Reviewer |
| “修改 README 中的一句话” | single_agent；一个写入 Task + 最小验证 |
| “修复登录 Bug 并运行测试” | Coder → Verifier；测试失败可 revise |
| “先调研方案再修改代码” | Research → Coder → Verifier |
| “前后端分别实现接口和页面” | Planner → 两个隔离并行 Worker → Merge → Verifier |
| Reviewer 发现架构问题 | 创建新 Plan Version 和修复 Task，不只输出评论 |

### 4.9 P0 退出门槛

必须全部满足才能进入 P1：

1. 六个验收场景拥有自动化测试。
2. direct、single、sequential、parallel 四种模式都可重复运行。
3. Workspace 不再固定显示 Planner → Coder → Reviewer。
4. 所有 Plan、Replan 和调度决定可追溯。
5. 代码任务不能在验证失败时被标记为完成。

---

## 5. P1：建设共享、可追溯、受预算约束的 RAG 层

### 5.1 P1 目标

把当前轻量 Memory/Skill 关键词检索升级为统一 Context Service，但不让 RAG 成为每个 Task 的强制步骤。

### 5.2 知识对象分层

| 类型 | 示例 | 是否需要人工审核 | 默认检索方式 |
|---|---|---|---|
| Workspace Live Context | 当前文件、Git diff、测试输出 | 否，来自真实环境 | 文件、符号、命令和结构化查询 |
| Project Document | README、架构、规范、接口文档 | 接入时确认来源 | 关键词 + 向量 + Metadata |
| Approved Memory | 历史决策、失败经验、用户偏好 | 是 | Hybrid Retrieval |
| Approved Skill | SOP、步骤、Prompt 模板 | 是 | 场景匹配 + 结构过滤 |
| Runtime Evidence | Tool Call、Artifact、Verification | 否，来源不可变 | Task / Goal / Run 精确查询 |

### 5.3 建议新增数据模型

| 对象 | 关键字段 |
|---|---|
| `KnowledgeSource` | id、name、type、uri、workspace_scope、status、sync_policy |
| `KnowledgeDocument` | id、source_id、path、title、checksum、mime_type、metadata、indexed_at |
| `KnowledgeChunk` | id、document_id、content、chunk_index、token_count、embedding、symbol_path、metadata |
| `RetrievalRun` | id、goal_id、task_id、agent_id、query、policy、filters、latency_ms、token_budget |
| `RetrievedContextItem` | retrieval_run_id、source_type、source_id、chunk_id、score、rank、used、citation |
| `ContextPackageSnapshot` | worker_id、plan_version_id、payload、token_count、checksum |

保留现有 `MemoryDraft` 和 `SkillDraft`，通过批准状态进入可检索范围，不直接改造成普通文档 Chunk。

### 5.4 检索管线

```text
Query Builder
  ↓
权限与 Workspace Scope 过滤
  ↓
精确路径 / 关键词检索
  +
向量语义检索
  ↓
合并、去重、Metadata 过滤
  ↓
Rerank
  ↓
Context Budget 裁剪
  ↓
Context Package + Citation
```

第一阶段可采用：

- SQLite FTS 或现有数据库关键词检索。
- Embedding Adapter 接口。
- 可替换的 Vector Store Adapter；先不绑定单一供应商。
- 轻量 Reranker；不可用时退化为加权规则。

### 5.5 不同角色使用不同 Retrieval Policy

| 角色 / 阶段 | 优先上下文 |
|---|---|
| Orchestrator | 项目概览、架构、完成标准、类似历史 Goal |
| Coder | 目标文件、符号引用、测试、代码规范、相关 Skill |
| Researcher | 项目资料、已批准外部来源、研究标准 |
| Reviewer / Verifier | 验收规则、Git diff、测试证据、风险规则 |
| Supervisor | Plan、全部 Verification、未解决风险、Handoff 记录 |

### 5.6 RAG 调用门控

满足以下条件之一才调用 Knowledge RAG：

- Orchestrator 声明 `required_context`。
- Task 的 capability 需要项目或领域知识。
- 当前 Observation 表明上下文不足。
- 验证失败需要查找历史修复经验。
- 用户显式选择知识源。

以下任务默认不调用 Knowledge RAG：

- 与项目无关的简单问答。
- 输入本身已经包含全部必要上下文。
- 纯状态查询或确定性操作。
- 检索成本超过该 Task 的 Context Budget。

### 5.7 来源与可信度

每个 Context Item 必须保存：

- 来源类型和来源 ID。
- 文档路径或历史 Goal / Task。
- 检索分数和排序。
- 是否真正注入 Prompt。
- 占用 Token 数。
- 哪个 Agent 使用。
- 最终任务成功或失败。

禁止：

- 未审核 Memory 默认进入长期检索。
- 没有来源的“系统经验”。
- 把 Agent 自己刚生成的内容立即作为可信知识回灌。
- 跨 Workspace 越权检索。
- UI 只显示“使用了 RAG”而不显示具体来源。

### 5.8 P1 前端范围

#### Knowledge

- 数据源接入和同步状态。
- 文档、Chunk、更新时间、错误和权限范围。
- Memory / Skill 审核与启用状态。

#### Workspace Context Tab

- 本次是否触发 RAG及原因。
- 查询词和 Retrieval Policy。
- 检索结果、来源、分数和引用。
- 实际注入项与被丢弃项。
- Context Token 占用。
- 用户可以禁用错误来源并重新执行 Task。

### 5.9 P1 验收标准

1. Planner 能在规划前加载项目架构资料，并显示来源。
2. Coder 只获得与当前 Task 和 Workspace Scope 相关的上下文。
3. Reviewer 可以引用验收规则和真实 Verification Evidence。
4. 同一知识库不会被每个 Agent 无差别全量注入。
5. 关闭 RAG 的简单任务仍能正常执行。
6. 错误 Memory 被禁用后不会再次进入 Context Package。
7. 每次检索都有 RetrievalRun、引用和 Token 成本记录。

---

## 6. P2：把 Multi-Agent 升级为真正的按需执行策略

### 6.1 P2 目标

只有当任务存在能力分工、独立子问题、并行收益或上下文隔离需求时才启用多个 Agent。

### 6.2 Capability Registry

Agent 选择从固定角色映射升级为 capability-based selection。

建议 capability：

```text
planning
research
code_read
code_edit
test
review
security_review
document_write
data_analysis
tool_orchestration
supervision
```

每个 Agent 声明：

- capabilities 和熟练度。
- 可用模型和备用模型。
- 允许工具。
- Workspace 权限。
- 支持的输入 / 输出类型。
- 最大并发、Token、步骤和失败阈值。
- 历史成功率、成本和平均耗时。

### 6.3 Agent 选择评分

Orchestrator 给出 capability 需求，Selector 根据以下因素选择：

```text
能力匹配
+ 模型任务适配度
+ 工具可用性
+ Context Window
+ 历史成功率
+ 成本和延迟
+ Quota
+ 风险政策
+ 当前负载
```

选择结果必须包括候选、淘汰原因、最终 Agent、模型和可覆盖入口。

### 6.4 启用多个 Agent 的条件

满足以下情况才建议 Multi-Agent：

- 存在两个以上需要不同 capability 的 Task。
- 子任务可以独立验证。
- 并行执行能显著减少时间。
- 需要独立 Reviewer 降低高风险改动偏差。
- 当前 Agent 缺少工具、上下文或额度，需要 Handoff。

不应启用多个 Agent：

- 一个 Agent 一次工具循环即可完成。
- 多个 Agent 会修改相同文件且无法隔离。
- 任务无法独立验收。
- Multi-Agent 增加的 Token 和协调成本高于收益。
- 只是为了匹配团队模板或让 UI 显得忙碌。

### 6.5 并行执行与合并

- 每个并行 Worker 使用独立 worktree / Workspace Scope。
- 调度前计算潜在文件冲突。
- 合并顺序可复现。
- 冲突产生专门的 Merge / Resolution Task。
- 并行 Task 独立记录 Context Package、工具和验证证据。
- 不允许多个 Worker 无隔离写同一工作区。

### 6.6 Handoff、Retry 与 Replan 的边界

| 动作 | 使用场景 | 是否更换计划 | 是否更换 Worker |
|---|---|---|---|
| Retry | 瞬时错误、可恢复工具失败 | 否 | 通常否 |
| Handoff | Agent / 模型 / 额度 / 能力不合适 | 通常否 | 是 |
| Revise | 当前 Task 输出不合格但目标仍正确 | 局部 | 可选 |
| Replan | 假设、依赖、范围或任务图错误 | 是 | 按新计划决定 |

Workspace 必须明确显示四种动作，不能全部用 Handoff 表达。

### 6.7 Supervisor 按需启用

Supervisor 不应成为每次 Goal 的固定最后一步。

建议启用条件：

- high-risk Goal。
- 多个并行分支需要 Goal 级合并判断。
- 存在失败、Replan 或 Handoff。
- 用户要求独立审查。
- Completion Contract 包含主观质量标准。

简单且完全由确定性验证覆盖的任务，可以直接通过 Verifier 完成。

### 6.8 P2 前端范围

- Studio / Team Builder 显示“可用能力”和执行政策，不再承诺固定 Agent 顺序。
- Workspace 根据 ExecutionPlan 动态创建和回收工位。
- Card Flow 支持真实分支、汇合、Replan 和 Handoff 连线。
- Pixel Office 仅让已激活 Agent 进入工位。
- 顶栏显示：当前模式、激活 Agent 数、并行度、协调成本。
- 运行总结增加“为什么使用 Multi-Agent”和与单 Agent 基线的收益比较。

### 6.9 P2 验收标准

1. 简单任务不会激活多个 Agent。
2. 单文件修复默认由一个 Agent 完成。
3. 前后端独立任务可以并行并安全合并。
4. 高风险任务能按政策激活独立 Reviewer 或 Supervisor。
5. Quota / 模型失败可以 Handoff，而不是重新执行全部 Goal。
6. Multi-Agent 的额外 Token、耗时和收益可量化。
7. 双模式 Workspace 中显示的并行和交接都来自真实 Runtime 状态。

---

## 7. 建议 API 与数据结构调整

### 7.1 Planning API

```text
POST /goals/{goal_id}/plan
GET  /goals/{goal_id}/plans
GET  /goals/{goal_id}/plans/{version}
POST /goals/{goal_id}/plans/{version}/confirm
POST /goals/{goal_id}/replan
PATCH /goals/{goal_id}/plans/{version}/tasks/{task_id}
```

### 7.2 Context / RAG API

```text
POST /knowledge/sources
POST /knowledge/sources/{id}/sync
GET  /knowledge/sources/{id}/documents
POST /context/retrieve
GET  /goals/{goal_id}/context-runs
GET  /tasks/{task_id}/context-package
POST /context/items/{id}/disable
```

### 7.3 Runtime API 扩展

Workspace State 建议增加：

```json
{
  "active_plan": {},
  "plan_versions": [],
  "task_mode": "parallel_multi_agent",
  "activation_reason": "",
  "task_edges": [],
  "parallel_groups": [],
  "context_runs": [],
  "replan_events": [],
  "completion_evidence": []
}
```

### 7.4 兼容策略

- 现有 Goal 没有 ExecutionPlan 时，由当前 Task 数据生成只读 Plan v0。
- `_preset_specs()` 保留为 fallback，P0 验收完成后停止新增固定模板逻辑。
- 现有 `MemoryDraft` / `SkillDraft` API 保持兼容。
- 现有 `Task.dependencies` 继续使用，新 Plan 表保存计划版本和变更关系。
- 现有 Card Flow / Pixel Office 继续消费统一 Workspace ViewModel，逐步增加动态图字段。

---

## 8. 建议代码落点

### 8.1 后端

| 文件 / 模块 | 动作 |
|---|---|
| `services/orchestrator_service.py` | 拆分模型 Orchestrator、规则 fallback、Plan 校验和持久化 |
| `services/runtime_service.py` | 接入 Plan Version、动态调度、统一 Replan 和完成门禁 |
| `services/context_service.py` | 升级为统一 Context Service 和 Retrieval Policy |
| `services/review_service.py` | 将文字审查结果映射为统一决策协议 |
| `services/handoff_service.py` | 与 Replan/Retry 分离，保留责任和上下文转移语义 |
| `services/curator_service.py` | 增加知识使用结果和错误 Memory 治理 |
| `services/verifier_service.py` | 建议新增；统一 Completion Contract 和 Evidence Bundle |
| `services/retrieval_service.py` | 建议新增；Hybrid Retrieval、Rerank、预算和引用 |
| `services/agent_selector_service.py` | 建议新增；capability-based Agent / Model 选择 |
| `models/workspace.py` | 增加 ExecutionPlan、PlanVersion、PlanChange 等对象 |
| `models/knowledge.py` | 增加 Source、Document、Chunk、RetrievalRun |
| `routes/goals.py` / `routes/runtime.py` | 增加 Plan、Replan、确认和 Workspace 聚合字段 |
| `routes/knowledge.py` | 增加数据源、同步、检索和 Context 查询接口 |

### 8.2 前端

| 文件 / 模块 | 动作 |
|---|---|
| `pages/WorkspacePage.tsx` | 接入 Plan 版本、动态模式、Replan 和 Context 选择状态 |
| `components/CardFlowRenderer.tsx` | 支持真实 DAG、分支、汇合和计划变更 |
| `components/PixelOfficeRenderer.tsx` | 只渲染已激活工位，支持动态入场 / 退出 |
| `components/AgentDetailModal.tsx` | Context 来源、激活原因、证据和计划历史 |
| `components/TaskTree.tsx` | 显示依赖、并行组、取消、跳过和 Replan 来源 |
| `components/BottomConsole.tsx` | 增加 Plan / Retrieval / Replan / Verification 事件 |
| `utils/workspaceViewModel.ts` | 从线性 Station 模型升级为统一 Task Graph ViewModel |
| `pages/EvolutionReviewPage.tsx` | 增加 Memory 使用结果、禁用和来源治理 |
| `types/workspace.ts` | 增加 ExecutionPlan、TaskEdge、ContextRun、Evidence 类型 |

---

## 9. 实施顺序与依赖

```text
P0-1 Planning Contract
  ↓
P0-2 Model Orchestrator + Rule Fallback
  ↓
P0-3 Task Graph Scheduler
  ↓
P0-4 Replan Protocol
  ↓
P0-5 Verifier Completion Gate
  ↓
P0-6 Workspace Plan / Graph UI
  ↓
P1 Shared Context / RAG
  ↓
P2 Capability Selection + On-demand Multi-Agent
```

说明：

- 可以先复用当前轻量 Context Service 完成 P0，不应等待完整向量 RAG 才做 Orchestrator。
- P1 必须建立在 P0 的 Task 和 Plan Contract 上，否则无法做任务级检索。
- P2 必须建立在 P0 的真实 Task Graph、验证和 Replan 上，否则多 Agent 只会放大错误和成本。
- 双模式前端可以持续使用，但任何并行、交接和激活状态必须由 Runtime 数据驱动。

---

## 10. 测试矩阵

### 10.1 Planning

- direct 不生成多余 Task。
- single_agent 只激活一个 capability。
- sequential 依赖顺序正确。
- parallel 只并行 `parallel_safe` Task。
- 循环依赖被拒绝。
- 无可用 capability 时返回 blocked / ask_user。
- 模型输出无效 JSON 时修复或进入规则 fallback。

### 10.2 Runtime

- 暂停、恢复、停止不破坏 Plan 状态。
- 动态插入 Task 后调度器可继续运行。
- Replan 不重复执行已验证完成 Task。
- Verification 失败不能完成 Goal。
- 并行 worktree 合并冲突产生 Resolution Task。
- Handoff 后 Context、Workspace Scope 和 Evidence 可继承。

### 10.3 RAG

- 只检索当前 Workspace 允许的数据。
- 未审核 / 过期 / 禁用 Memory 不进入结果。
- 无相关知识时返回空 Context，而不是硬塞低相关内容。
- Context Budget 能稳定裁剪。
- Citation 指向真实来源。
- 关闭 RAG 后任务仍能运行。

### 10.4 前端

- 四种 task_mode 均有真实展示状态。
- Card Flow / Pixel Office 切换不改变 Runtime 数据。
- 动态工位数量和 Task Graph 一致。
- Plan、Replan、Handoff、Retry 在视觉上可区分。
- Modal 能展示 Context 来源和 Verification Evidence。
- 刷新页面后 Goal、Plan Version 和选中模式可恢复。

---

## 11. 运行指标与产品判断

下一阶段不只统计“调用了几个 Agent”，还要统计是否值得调用。

| 指标 | 用途 |
|---|---|
| Plan validity rate | 衡量结构化计划一次通过率 |
| Replan rate | 判断初次计划质量和任务不确定性 |
| Task verification pass rate | 衡量真实完成率 |
| Context precision / used ratio | 检索结果中真正被使用的比例 |
| RAG empty-result rate | 判断索引覆盖与门控是否合理 |
| Multi-Agent activation rate | 防止所有任务都被强制拆分 |
| Parallel speedup | 判断并行是否真的节省时间 |
| Coordination overhead | Multi-Agent 额外 Token、延迟、冲突和 Handoff 成本 |
| Handoff success rate | 衡量责任转移是否恢复任务 |
| Human intervention rate | 衡量自动化与可控性的平衡 |

建议设置守门指标：

- 简单任务 Multi-Agent 激活率应接近 0。
- 没有相关知识时 RAG 应允许返回空结果。
- 代码任务 Verification 失败完成率必须为 0。
- 并行任务只有在预估收益高于协调成本时启用。

---

## 12. 本轮明确非目标

- 不建设无限自由的拖拽工作流平台。
- 不要求用户手动为每个 Goal 画 DAG。
- 不让每个 Agent 拥有独立向量数据库。
- 不一次接入多个复杂 Vector Store 产品。
- 不做未经审核的全自动长期 Memory 写入。
- 不因为已有 Planner、Coder、Reviewer 工位，就强制每次全部激活。
- 不在 Runtime 尚未支持前，用前端伪造并行、条件分支或成功状态。
- 不用 RAG 替代 Workspace 文件工具、符号查询、Git 和测试证据。

---

## 13. 下一步开发清单

### 第一批：P0 主闭环

- [ ] 定义 `ExecutionPlan` / `PlanTask` / `PlanChange` Schema。
- [ ] 增加 Plan JSON Schema 校验和 DAG 校验。
- [ ] 将当前关键词规划降级为 Rule Fallback。
- [ ] 实现模型驱动 Orchestrator。
- [ ] 保存 Plan Version、原始输出和激活理由。
- [ ] 扩展 Scheduler 的动态 Task 和阻塞处理。
- [ ] 建立统一 Replan 决策协议。
- [ ] 新增 Verifier Completion Gate。
- [ ] Workspace 显示 task_mode、Plan Version 和激活理由。
- [ ] Card / Pixel 只显示真实激活工位。
- [ ] 完成六个 P0 自动化验收场景。

### 第二批：P1 共享 RAG

- [ ] 定义 KnowledgeSource、Document、Chunk、RetrievalRun。
- [ ] 实现文档同步、Checksum 和增量更新。
- [ ] 实现关键词 + 向量混合检索 Adapter。
- [ ] 实现 Retrieval Policy 和 Context Budget。
- [ ] Orchestrator 规划前检索。
- [ ] Worker 执行前任务级检索。
- [ ] Verifier / Replan 检索历史证据和 Skill。
- [ ] Workspace Context Tab 展示来源和引用。
- [ ] 建立错误 Memory 禁用和使用反馈。
- [ ] 完成权限、过期、空结果、预算和引用测试。

### 第三批：P2 按需 Multi-Agent

- [ ] 建立 Capability Registry。
- [ ] 实现 Agent / Model 候选评分。
- [ ] Team Template 改为能力集合和执行政策。
- [ ] 加强并行安全和冲突预检。
- [ ] 合并冲突生成 Resolution Task。
- [ ] Handoff、Retry、Revise、Replan 明确分离。
- [ ] Supervisor 按风险和复杂度启用。
- [ ] Workspace 动态工位、分支、汇合和计划变更。
- [ ] 统计 Multi-Agent 收益与协调成本。
- [ ] 完成单 Agent / 串行 / 并行对比基准。

---

## 14. 最终完成定义

本轮 P0–P2 完成后，用户输入不同 Goal，系统应表现为：

```text
简单任务
→ 不拆分、不检索无关知识、不启用多个 Agent

单 Agent 工具任务
→ 获取必要上下文，完成操作并通过验证

多步骤任务
→ 生成可执行 Task Graph，按依赖推进

可并行任务
→ 激活多个隔离 Worker，安全合并并验证

执行失败
→ 根据证据 Retry、Handoff、Revise 或 Replan

任务完成
→ 有 Artifact、Verification、引用和运行成本证明

经验沉淀
→ 生成可追溯 Draft，审核后才进入共享知识层
```

最终判断标准不是“页面上同时出现了多少 Agent”，而是：

> 系统是否用最少且合适的 Agent、模型、工具和上下文，以可追溯证据完成了 Goal。
