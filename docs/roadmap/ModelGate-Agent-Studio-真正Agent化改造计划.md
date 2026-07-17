# ModelGate Agent Studio：从工作流原型到真正 Agent 的全新改造计划

> 文档定位：ModelGate Agent Studio 下一阶段总路线图  
> 核心目标：将当前“可观察的多 Agent 工作流原型”升级为“能够调用真实模型、动态规划、操作真实项目、验证结果、失败重试、跨模型交接并沉淀经验”的开发者 Agent 工作台。  
> 当前阶段建议名称：**Agent Runtime v2 / Autonomous Execution Foundation**

---

## 1. 当前阶段重新判断

ModelGate Agent Studio 当前已经具备以下有价值的控制面能力：

- Agent Registry
- Model Manager / 多模型管理
- Model Router
- Task 与 Goal 数据结构
- Runtime 基础骨架
- Quota Manager
- Handoff Manager
- Supervisor Review
- Logs / Observability
- Memory Draft
- Agent Workspace 可视化

这些模块证明产品已经具备“多 Agent 系统的外形、控制面和运行骨架”。

但当前系统尚未形成真正 Agent 的关键闭环：

```text
理解目标
→ 动态决定执行策略
→ 调用真实模型
→ 读取真实环境
→ 使用工具产生修改
→ 执行测试或检查
→ 观察真实结果
→ 根据结果继续修复
→ 通过验收标准判断完成
→ 交付可验证产物
```

因此，下一阶段的目标不是继续增加页面，也不是继续增加更多 Agent 名称，而是让现有架构真正拥有行动能力与结果验证能力。

---

## 2. 新阶段产品定位

下一阶段的 ModelGate Agent Studio 应定义为：

> 一个面向开发项目的多模型 Agent Runtime。它能够根据用户目标动态组织 Agent 团队，在受控工作区内读取和修改文件、执行命令、运行测试、检查结果、失败重试、跨模型交接，并将成功经验沉淀为可复用 Memory 与 Skill。

它仍然不应被定位为完全无人监督、可以处理所有开放任务的通用自治 Agent。

更准确的阶段名称是：

> **Verified Multi-Agent Execution Platform**  
> 可验证的多模型 Agent 执行平台

---

## 3. 本阶段最重要的六个转变

### 3.1 从 Mock 默认执行转向真实模型默认执行

当前问题：

- Runtime 默认 Provider 为 Mock。
- Workspace 中的完成状态可能来自预设输出。
- Mock 与 Production 路径没有被严格区分。

目标状态：

- 用户已在 Model Manager 配置真实 Provider 与模型后，Runtime 默认从可用真实模型中选择。
- Mock 仅用于测试、演示和离线开发。
- 每次运行明确标记 `execution_mode`。

建议模式：

```text
execution_mode:
- live        真实模型 + 真实工具
- dry_run     真实模型 + 禁止写入
- sandbox     真实模型 + 沙箱工具
- mock        Mock 模型 + Mock 工具，仅测试使用
```

必须实现：

1. Provider Factory 不再默认回退到 Mock。
2. 未配置真实模型时明确报错或进入用户指定的 Mock 模式。
3. Model Manager 中启用的模型成为 Runtime 的唯一候选来源。
4. Runtime 启动前执行模型可用性检查。
5. 每次模型调用保存 provider、model、request id、token、耗时和错误。
6. 前端显著展示当前是否为 Live、Sandbox、Dry Run 或 Mock。

验收标准：

- 创建一个 Goal 后，日志能证明调用了真实 Provider。
- 关闭所有真实模型后，系统不会静默使用 Mock 冒充真实执行。
- Mock 模式只能被显式选择或测试环境启用。

---

### 3.2 从固定 Planner → Coder → Reviewer 转向动态编排

当前问题：

- 主链路固定调用 Planner、Coder、Reviewer。
- 简单问题也可能经过全部 Agent。
- Agent 角色不是按任务需求动态激活。
- 计划生成后缺少执行中重规划。

目标状态：

第一个接收目标的 Agent 不应直接固定调用所有 Agent，而应先判断：

1. 任务是否可以直接回答。
2. 是否需要读取项目。
3. 是否需要写文件。
4. 是否需要终端或测试。
5. 是否需要搜索资料。
6. 是否需要拆成多个子任务。
7. 哪些子任务可以并行。
8. 每个任务需要哪类 Agent、模型和工具。
9. 是否需要 Reviewer 或 Supervisor。
10. 什么条件下结束、返工或交接。

建议引入统一的 **Orchestrator Agent**，合并早期 Router 与 Planner 的决策入口。

Orchestrator 输出结构：

```json
{
  "task_mode": "direct | single_agent | sequential_multi_agent | parallel_multi_agent",
  "goal_summary": "",
  "assumptions": [],
  "required_context": [],
  "tasks": [
    {
      "id": "task-1",
      "objective": "",
      "agent_capability": "code_edit",
      "required_tools": ["file_read", "file_write", "terminal_execute"],
      "dependencies": [],
      "completion_criteria": [],
      "risk_level": "low | medium | high"
    }
  ],
  "final_acceptance_criteria": [],
  "human_approval_points": []
}
```

动态执行逻辑：

```text
用户 Goal
↓
Orchestrator 判断任务模式
├─ 简单问答 → 单模型直接完成
├─ 单一任务 → 单 Agent 工具循环
├─ 多步骤任务 → 动态任务图
└─ 可并行任务 → 多 Worker 隔离执行
↓
每个任务独立执行与验证
↓
Orchestrator 根据观察结果重规划
↓
Supervisor 只在需要时验收
```

必须实现：

- Task Graph，而不是固定角色链。
- Agent 选择基于 capability，而不是硬编码名称。
- 支持运行中新增、取消、拆分和重试 Task。
- 支持简单任务跳过 Planner、Reviewer。
- 支持 Supervisor 返回 `complete / revise / replan / ask_user / blocked`。

验收标准：

- 简单总结任务只调用一个 Agent。
- 代码修改任务可以动态调用 Coder 与测试能力。
- 需要研究再编码的任务能生成 Research → Code 的依赖。
- Reviewer 发现架构问题时，系统可以生成新的修复任务，而不是只输出评价。

---

### 3.3 从“模型输出文本”转向“Agent 操作真实环境”

真正 Agent 的核心不是生成一段看似完成的文本，而是对环境产生可追踪的影响。

第一阶段工具范围必须聚焦开发任务，不要一次接入所有外部服务。

#### P0 工具

读取类：

- `workspace_list`
- `file_read`
- `file_search`
- `glob_search`
- `git_status`
- `git_diff`
- `git_log`

写入类：

- `file_create`
- `file_write`
- `file_patch`
- `file_delete`，默认需审批
- `directory_create`

执行类：

- `terminal_execute`
- `test_run`
- `lint_run`
- `typecheck_run`
- `build_run`

状态类：

- `artifact_register`
- `checkpoint_create`
- `checkpoint_restore`

#### 工具调用统一返回结构

```json
{
  "tool_call_id": "",
  "tool_name": "",
  "status": "success | failed | denied | timeout",
  "exit_code": 0,
  "stdout": "",
  "stderr": "",
  "changed_files": [],
  "artifacts": [],
  "duration_ms": 0,
  "truncated": false
}
```

工具设计原则：

1. 所有路径必须限制在 Workspace Root。
2. 所有命令必须有超时。
3. 输出必须限制长度并支持分段读取。
4. 高风险命令必须拦截或审批。
5. 每次写入前创建 checkpoint。
6. 每次工具调用必须进入日志与事件流。
7. Agent 不直接获得宿主机无限 Shell 权限。

验收标准：

- Agent 能创建一个真实文件。
- Agent 能修改已有代码。
- Workspace 能展示真实 diff。
- Agent 能运行一次真实测试并读取结果。
- 禁止越过 Workspace Root 读取或写入。

---

### 3.4 从“Agent 说完成”转向“基于证据的完成判断”

当前问题：

- `completed` 更接近模型自我声明。
- 缺少可执行验收标准。
- 缺少产物、diff 和测试结果证据。

目标状态：

每个 Task 必须包含 Completion Contract。

```json
{
  "completion_criteria": [
    {
      "type": "file_exists",
      "target": "backend/src/services/live_provider.py"
    },
    {
      "type": "tests_pass",
      "command": "pytest tests/providers -q"
    },
    {
      "type": "lint_pass",
      "command": "ruff check backend/src"
    },
    {
      "type": "review_score",
      "minimum": 0.8
    }
  ]
}
```

建议完成状态：

```text
pending
ready
running
waiting_tool
waiting_approval
verifying
revision_required
blocked
failed
completed_verified
completed_unverified
cancelled
```

`completed_verified` 必须满足：

- 必需文件或产物存在。
- 相关命令执行成功。
- 变更已被读取并确认。
- 不存在未处理的阻塞错误。
- Supervisor 或规则引擎确认验收标准通过。

`completed_unverified` 仅用于：

- 无法运行验证环境。
- 用户明确允许跳过验证。
- 任务本身为主观内容生成且没有自动测试。

最终交付必须包含 Evidence Bundle：

- 修改文件列表
- Git diff 摘要
- 执行命令
- 测试结果
- 失败与重试记录
- 生成产物
- 未解决风险

验收标准：

- 测试失败时任务不能标为 `completed_verified`。
- Agent 必须读取测试失败内容并尝试修复。
- 最终结果页面能展示完成证据，而不只是模型总结。

---

### 3.5 从单次调用转向 Observe → Think → Act → Verify 循环

每个执行 Agent 都应运行独立 Agent Loop。

```text
加载 Task 与上下文
↓
观察当前环境
↓
决定下一步动作
↓
调用模型或工具
↓
记录 Observation
↓
更新 Working State
↓
判断：继续、验证、重试、交接、请求审批或结束
```

建议 Runtime 核心对象：

```text
Run
├─ Goal
├─ Task Graph
├─ Worker Sessions
├─ Events
├─ Tool Calls
├─ Checkpoints
├─ Artifacts
├─ Verification Results
└─ Memory Candidates
```

每个 Worker 应具备：

- 最大步数
- 最大连续失败次数
- 最大 token / cost
- 最大执行时长
- 允许工具列表
- 当前 workspace
- 当前上下文窗口
- 当前任务状态
- 最近观察结果
- 下一步行动意图

终止条件：

- 验收通过。
- 明确阻塞且无法自动解决。
- 达到资源限制。
- 需要用户提供缺失信息。
- 命中安全策略。
- 用户中止。

防止死循环：

- 相同工具参数重复调用检测。
- 相同错误连续出现检测。
- 无文件变化却重复宣称修复检测。
- 连续多步无进展触发 replan。
- 最大重试后转交其他模型或请求用户。

---

### 3.6 从任务后 Memory Draft 转向执行前检索与任务后进化

Memory 必须同时进入执行前、执行中和执行后。

#### 执行前

检索：

- Project Memory
- User Preference Memory
- Skill Memory
- 历史错误与修复
- 相关 Handoff
- 模型历史表现

生成 Context Package：

```json
{
  "project_facts": [],
  "user_preferences": [],
  "relevant_skills": [],
  "known_failures": [],
  "prior_decisions": [],
  "source_references": []
}
```

#### 执行中

保存：

- 重要决策
- 新发现的项目事实
- 工具观察
- 阻塞原因
- 临时工作状态
- 可供 Handoff 使用的压缩上下文

#### 执行后

提取：

- 成功路径
- 失败路径
- 有效工具顺序
- 有效提示或约束
- 模型表现
- 可复用 Skill 草稿
- 项目事实更新
- 用户偏好候选

早期继续采用人工审核：

```text
Memory Candidate
→ 自动分类与置信度评分
→ 用户或规则审核
→ 写入正式 Memory / Skill
```

必须避免：

- 把模型猜测写成事实。
- 把一次性要求写成长久偏好。
- 把失败步骤直接沉淀为成功 Skill。
- 不带来源地保存记忆。

验收标准：

- 第二次运行同一项目任务时，日志显示检索了已有项目记忆。
- Agent 能引用历史决策避免重复探索。
- Memory 条目可追溯到原始 Run、Task、文件或工具结果。

---

## 4. 参考成熟 Agent 后应借鉴的设计

### 4.1 Hermes Agent：借鉴什么

应借鉴：

- 模型无关的 Provider 设计。
- 闭环学习与 Skill 沉淀。
- 会话历史检索与压缩。
- 项目上下文文件。
- 独立子 Agent 与并行任务。
- 多种隔离执行后端。
- 工具与 Toolset 的分组管理。
- 长任务中断后继续。

不应直接复制：

- 泛个人助理与多消息渠道优先路线。
- 大量与开发者场景无关的工具。
- 完全自动写入长期记忆。

ModelGate 的差异化应是：

> Hermes 更强调一个 Agent 持续成长，ModelGate 应强调多个模型组成的 Agent 团队如何动态协作、交接、验证和共同积累项目经验。

### 4.2 OpenHands：借鉴什么

应借鉴：

- 沙箱化代码执行。
- Agent 与 Runtime 解耦。
- Event Stream 驱动的状态记录。
- 终端、文件和浏览器工具。
- 可暂停、恢复和中断的执行生命周期。
- 基于真实环境反馈继续行动。
- 软件工程任务的测试与基准评估。

ModelGate 不需要立即复制完整远程运行基础设施，但必须先建立本地 Docker Sandbox 抽象，以便未来扩展到 SSH、云容器或远程 Runner。

### 4.3 Claude Code / Codex 类 Coding Agent：借鉴什么

应借鉴：

- 先理解仓库，再进行最小修改。
- 工具调用与模型对话交替。
- 修改后自动读取 diff。
- 运行测试并根据报错修复。
- 任务完成时输出修改摘要和验证结果。
- 将项目规则放入仓库级上下文文件。

### 4.4 LangGraph / CrewAI 类框架：借鉴什么

应借鉴：

- 显式状态机。
- 可恢复的工作流状态。
- 条件边与动态分支。
- Task Graph 与并行执行。

不应退化为：

- 用户手动画固定节点。
- 每个任务永远按照预定义 DAG 执行。

ModelGate 的 Task Graph 应由 Orchestrator 动态生成，并允许运行中修改。

---

## 5. 目标技术架构

```text
User Goal
│
▼
Goal Intake
- 目标
- 约束
- 工作区
- 风险级别
- 自动执行权限
│
▼
Orchestrator
- 判断 direct / single / multi / parallel
- 动态生成 Task Graph
- 定义验收标准
- 选择 Agent Capability
│
▼
Context Builder
- Workspace Scan
- Project Memory Retrieval
- Skill Retrieval
- Handoff Retrieval
│
▼
Model Router
- 能力
- 质量
- 成本
- 延迟
- 上下文
- 额度
- 历史表现
│
▼
Worker Runtime
- Observe
- Decide
- Act
- Tool Call
- Verify
- Retry / Replan
│
├───────────────┐
▼               ▼
Tool Gateway    Model Gateway
- File          - OpenAI-compatible
- Terminal      - Anthropic
- Git           - DeepSeek
- Test          - Kimi
- Browser       - GLM
- MCP           - MiniMax / others
│
▼
Sandbox / Workspace
- 文件系统隔离
- 命令审批
- Checkpoint
- Diff
- Artifact
│
▼
Verifier
- Rule checks
- Tests
- Lint
- Build
- Reviewer
│
├─ 不通过 → Worker 修复 / Orchestrator 重规划
└─ 通过 → completed_verified
│
▼
Supervisor
- Goal-level acceptance
- Missing work detection
- Final delivery
│
▼
Evolution Pipeline
- Memory Candidate
- Skill Candidate
- Model performance
- Handoff experience
```

---

## 6. 核心数据模型改造

### 6.1 Run

新增字段建议：

```text
run_id
execution_mode
workspace_id
status
orchestrator_model_id
budget_tokens
budget_cost
max_duration
started_at
ended_at
final_verification_status
```

### 6.2 Task

新增字段建议：

```text
task_type
required_capabilities
required_tools
dependencies
acceptance_criteria
risk_level
retry_policy
assigned_worker_id
verification_status
blocked_reason
parent_task_id
```

### 6.3 WorkerSession

新增字段建议：

```text
worker_session_id
agent_profile_id
model_id
workspace_scope
allowed_tools
step_count
failure_count
context_snapshot_id
status
last_observation
next_action
```

### 6.4 RuntimeEvent

建议统一事件流：

```text
run.created
plan.created
plan.updated
task.created
task.assigned
task.started
model.requested
model.responded
tool.requested
tool.approved
tool.completed
tool.failed
file.changed
checkpoint.created
verification.started
verification.failed
verification.passed
handoff.started
handoff.completed
memory.retrieved
memory.candidate_created
skill.candidate_created
task.completed
run.completed
run.failed
```

### 6.5 Artifact

```text
artifact_id
run_id
task_id
type
path
mime_type
checksum
created_by
verification_status
metadata
```

### 6.6 VerificationResult

```text
verification_id
task_id
criterion_type
command_or_rule
status
evidence
exit_code
created_at
```

---

## 7. 全新开发阶段与优先级

## Phase 0：冻结演示扩展，建立真实执行基线

目标：避免一边继续加 UI，一边底层仍停留在 Demo。

任务：

1. 暂停像素动画、复杂 Dashboard 和非核心页面扩展。
2. 明确 `main` 分支当前可运行基线。
3. 建立 Runtime v2 功能分支。
4. 为现有 Mock 流程补充回归测试。
5. 为 Live、Sandbox、Dry Run、Mock 定义环境变量和配置。
6. 建立 Agent 成熟度验收清单。

完成标准：

- 现有演示不被破坏。
- Runtime v2 可以独立迭代。
- 每个后续 Phase 都有明确自动化验收。

---

## Phase 1：真实模型 Runtime 接管默认执行

目标：所有正式 Goal 默认使用 Model Manager 中配置的真实模型。

开发内容：

1. 重构 Provider Interface。
2. 将 Model Manager 配置接入 Provider Factory。
3. 增加模型健康检查。
4. 增加真实模型流式输出。
5. 增加工具调用格式兼容层。
6. 增加模型错误标准化。
7. 禁止生产模式自动回退 Mock。
8. 前端展示真实模型和执行模式。

建议新增：

```text
backend/src/services/providers/base.py
backend/src/services/providers/live_provider.py
backend/src/services/providers/provider_registry.py
backend/src/services/providers/error_mapper.py
backend/src/services/model_gateway.py
```

测试：

- Provider 配置读取测试。
- 模型连通性测试。
- 不同 Provider 响应标准化测试。
- 未配置模型时失败测试。
- Mock 显式启用测试。

里程碑：

> 用户输入一个问题，系统通过真实模型返回结果，完整记录调用证据。

---

## Phase 2：动态 Orchestrator 与 Task Graph

目标：不再固定调用 Planner → Coder → Reviewer。

开发内容：

1. 新建 Orchestrator Agent。
2. 定义结构化 Planning Schema。
3. 实现任务模式判断。
4. 实现 Task Graph。
5. 实现依赖调度。
6. 实现 capability-based Agent selection。
7. 支持运行中 replan。
8. 支持 Supervisor 创建返工任务。

核心规则：

- 简单任务不拆分。
- 单文件小改动优先单 Agent。
- 只有存在独立子问题时才启用多 Agent。
- 只有真正可并行且上下文冲突低时才并行。
- Reviewer 不是强制步骤。
- Supervisor 负责 Goal 级判断，不负责代替所有任务 Reviewer。

测试场景：

1. 简单解释问题。
2. 单文件修复。
3. 需要先研究再修改的任务。
4. 前后端可并行任务。
5. 测试失败后生成修复任务。

里程碑：

> 同一套 Runtime 能根据不同 Goal 生成明显不同的 Agent 调用路径。

---

## Phase 3：受控文件写入与 Workspace Sandbox

目标：Agent 能真实改变项目文件，但不能无限制操作宿主机。

开发内容：

1. Workspace Root 管理。
2. 文件读取、搜索、创建、Patch、删除工具。
3. Path Traversal 防护。
4. 单次写入大小限制。
5. Checkpoint 与 Restore。
6. Git diff 捕获。
7. Docker Sandbox 基础抽象。
8. Tool Permission Policy。
9. 高风险操作审批。

审批建议：

无需审批：

- 读取 Workspace 内文件。
- 搜索代码。
- 创建普通代码文件。
- 修改普通项目文件。
- 运行白名单测试命令。

需要审批：

- 删除文件。
- 修改 `.env`、密钥或部署配置。
- 安装系统依赖。
- 网络访问。
- 数据库写操作。
- Git push、merge、force 操作。
- 工作区外访问。

里程碑：

> Agent 能在沙箱中完成一次真实文件修改，并提供可回滚 diff。

---

## Phase 4：终端执行、测试与自动修复闭环

目标：打通真正 Agent 的最小闭环。

标准 Demo 任务：

> 在一个带有失败测试的小型项目中，Agent 读取项目、定位问题、修改文件、运行测试、读取错误、再次修复，直到测试通过。

开发内容：

1. `terminal_execute`。
2. 命令白名单与风险分类。
3. 超时和进程终止。
4. stdout / stderr 流式传输。
5. pytest / npm test / lint / build adapter。
6. 失败结果结构化。
7. 修复重试策略。
8. 无进展检测。
9. Evidence Bundle。

Agent Loop：

```text
read
→ inspect
→ edit
→ test
→ observe failure
→ edit
→ test
→ verify
```

里程碑：

> 系统第一次真正完成“修改代码并以测试通过证明完成”。

这是整个项目从 Demo 进入真正 Agent 的关键分界线。

---

## Phase 5：Verifier 与 Supervisor 重构

目标：完成判断基于证据，而不是语言判断。

开发内容：

1. Completion Contract。
2. Rule-based Verifier。
3. Test Verifier。
4. Diff Verifier。
5. Artifact Verifier。
6. LLM Reviewer 作为补充，而不是唯一标准。
7. Goal-level Supervisor。
8. `completed_verified` 与 `completed_unverified` 区分。

Supervisor 输入：

- 原始 Goal
- 用户约束
- Task Graph
- 每个 Task 的 Verification Result
- Diff
- Tests
- Artifacts
- 未解决风险

Supervisor 输出：

```text
complete
revise
replan
blocked
needs_user_input
```

里程碑：

> 任何标记为完成的代码任务都能展示对应测试、diff 和产物证据。

---

## Phase 6：真正的 Handoff 与上下文接力

目标：Handoff 不只是状态变化，而是接手 Agent 能继续执行并重新验证。

触发条件：

- 额度不足。
- 上下文接近上限。
- 模型连续失败。
- 任务能力不匹配。
- 成本超预算。
- 用户手动切换。

Handoff Package：

```json
{
  "goal": {},
  "task": {},
  "current_status": "",
  "completed_actions": [],
  "changed_files": [],
  "tool_results": [],
  "decisions": [],
  "failed_attempts": [],
  "remaining_work": [],
  "verification_state": [],
  "workspace_checkpoint": "",
  "recommended_next_action": ""
}
```

接手流程：

```text
生成结构化 Handoff
→ 保存 Context Snapshot
→ 选择接手模型
→ 接手 Agent 读取真实 Workspace
→ 校验 Handoff 与当前环境是否一致
→ 继续执行
→ 重新运行验证
```

必须验证：

- Handoff 前后的文件状态一致。
- 接手 Agent 不能只相信摘要，必须检查 Workspace。
- 接手后需要重新确认未完成任务和验证状态。

里程碑：

> 模型 A 修改一半并触发交接，模型 B 能继续修改并使测试通过。

---

## Phase 7：Memory Retrieval 与 Project Context

目标：让历史经验在任务开始前真正影响执行。

开发内容：

1. Project Memory Store。
2. Skill Store。
3. Error/Fix Memory。
4. Memory Retrieval Service。
5. Context Builder。
6. 文件级引用与来源追踪。
7. 记忆置信度与过期机制。
8. 用户审核流程。

初期不必直接上复杂向量数据库。

建议先实现：

- SQLite / PostgreSQL 元数据。
- Markdown 或 JSON 内容存储。
- FTS 全文检索。
- 标签、项目、任务类型过滤。
- 后续再加入 embedding 混合检索。

里程碑：

> Agent 第二次处理同一项目时，能读取上次沉淀的项目约束和错误修复经验。

---

## Phase 8：Skill 自进化闭环

目标：将成功任务轨迹沉淀成可复用执行方法。

Skill 应包含：

```text
name
version
applicable_when
inputs
required_tools
recommended_capabilities
procedure
validation
failure_patterns
examples
source_runs
confidence
human_approved
```

Skill 生成条件：

- 任务最终验证通过。
- 执行路径具有复用价值。
- 不包含项目私密信息或密钥。
- 能抽象为明确步骤。
- 经用户或规则审核。

Skill 使用流程：

```text
新 Goal
→ Skill Router 检索候选 Skill
→ Orchestrator 决定是否加载
→ Worker 执行
→ 比较结果
→ 更新 Skill 成功率和版本候选
```

里程碑：

> 相似任务第二次执行时，Agent 自动加载上次成功 Skill，并减少探索步骤。

---

## Phase 9：并行子 Agent 与隔离工作区

目标：在确有价值时并行执行，而不是为了展示多 Agent 而并行。

适用场景：

- 前端与后端独立修改。
- 多个互不依赖的研究任务。
- 多方案并行评估。
- Reviewer 并行检查不同维度。

实现建议：

- 每个子 Agent 使用独立 branch 或 worktree。
- 每个 Worker 使用独立 Context 与工具权限。
- Orchestrator 负责合并结果。
- 合并后统一运行测试。
- 冲突时创建 conflict-resolution Task。

里程碑：

> 两个 Agent 在隔离工作区完成互不冲突的修改，系统合并并统一验证。

---

## Phase 10：Workspace 从演示视图升级为真实控制台

目标：让现有视觉优势展示真实执行，而非模拟动画。

卡片视图必须展示：

- 当前真实 Agent / 模型
- 当前 Task
- 当前步骤
- 最近工具调用
- 文件变化
- 测试状态
- token / cost / quota
- 阻塞原因
- Handoff 状态
- 验收状态

任务详情必须展示：

- Task 目标
- 依赖关系
- Completion Criteria
- Tool Timeline
- Diff
- Test Results
- Artifacts
- Handoff Package
- Memory Used

像素办公室：

- 保留为第二视图。
- 动画必须由 Runtime Event 驱动。
- 不允许前端自行模拟 Agent 已完成。
- 同一事件在卡片视图与像素视图中保持一致。

里程碑：

> 用户看到的每个“工作、测试、失败、交接、完成”状态，都能追溯到底层真实事件。

---

## 8. 推荐的第一条真实 Agent 纵向切片

不要一开始支持所有开发任务。

建议先做一个非常明确的 Vertical Slice：

> **小型 Python / FastAPI 项目的 Bug Fix Agent**

用户输入：

```text
修复指定项目中的一个后端 Bug，并保证相关 pytest 通过。
```

完整链路：

1. 用户选择 Workspace。
2. Orchestrator 判断为单 Agent 或 Research + Coder。
3. Context Builder 读取项目结构。
4. Model Router 选择真实模型。
5. Coder 读取相关代码。
6. Coder 运行 pytest 获得失败。
7. Coder 修改文件。
8. Coder 再次运行 pytest。
9. 失败则继续修复。
10. Verifier 检查测试与 diff。
11. Supervisor 判断 Goal 是否完成。
12. 输出文件列表、diff、测试结果和风险。
13. Evolution Agent 生成 Memory / Skill Candidate。

首条切片暂不支持：

- 大型跨仓库任务。
- 自动部署。
- 数据库生产写入。
- 浏览器控制。
- 邮件与日历。
- 长时间后台任务。
- 完全无人审批的高风险操作。

这条链路跑通后，再扩展：

1. 前端 Bug Fix。
2. 小功能实现。
3. 文档生成与更新。
4. PR Review。
5. 项目 Onboarding。
6. 前后端联合任务。

---

## 9. 每个阶段的开发顺序

后续不再按照“Agent Registry → Router → Quota → Handoff → Workspace”这种模块顺序单独开发。

应改成按纵向闭环开发：

### Sprint A：真实模型单 Agent

```text
Goal
→ Live Model
→ Response
→ Logs
```

### Sprint B：真实文件修改

```text
Goal
→ Live Model
→ File Read
→ File Write
→ Diff
```

### Sprint C：测试修复闭环

```text
Goal
→ Read
→ Edit
→ Test
→ Repair
→ Verified Complete
```

### Sprint D：动态规划

```text
Goal
→ Orchestrator
→ Dynamic Task Graph
→ Selected Agents
→ Verified Complete
```

### Sprint E：真实 Handoff

```text
Agent A
→ Context Package
→ Agent B
→ Continue
→ Verify
```

### Sprint F：Memory / Skill

```text
Retrieve Before Run
→ Execute
→ Distill After Run
→ Reuse Next Run
```

### Sprint G：并行多 Agent

```text
Dynamic Parallel Tasks
→ Isolated Workspaces
→ Merge
→ Unified Verification
```

这种顺序可以确保每个 Sprint 都增加真实能力，而不是只增加更多 Demo 元素。

---

## 10. 测试与评估体系

真正 Agent 不能只测试接口是否返回 200。

### 10.1 单元测试

- Provider adapter
- Tool permission
- Path security
- Planning schema
- Task state transition
- Verification rules
- Handoff serialization
- Memory retrieval

### 10.2 集成测试

- 真实 Provider 调用，可使用低成本测试模型。
- Workspace 文件读写。
- Docker Sandbox。
- Terminal timeout。
- Test failure parsing。
- Checkpoint restore。

### 10.3 Agent 行为测试

建立固定任务集：

1. 修复一个有测试的 Python Bug。
2. 新增一个小 API Endpoint。
3. 修改一个前端组件并通过 lint。
4. 生成文档并检查目标文件。
5. 在模型 A 失败后交接模型 B。
6. 使用历史 Memory 完成重复任务。

每个任务记录：

- 成功率
- 验证通过率
- 平均步骤数
- 平均 token
- 平均成本
- 平均时间
- 人工干预次数
- 无效工具调用次数
- Handoff 成功率
- 回滚次数

### 10.4 反作弊验收

必须防止系统“口头完成”：

- 没有文件变化却声称修改完成。
- 测试未运行却声称测试通过。
- 命令失败却忽略错误。
- 只生成代码块而没有写入文件。
- Handoff 后重新从头做而非接续。
- 使用 Mock 却显示为 Live。

---

## 11. 安全与权限边界

### 11.1 默认最小权限

- 每个 Agent 只获得任务必需工具。
- 每个 Tool Call 都携带 Agent、Task、Run 身份。
- 写操作只在指定 Workspace。
- 网络访问默认关闭。
- Shell 命令经过策略检查。

### 11.2 风险等级

```text
Low
- 读取文件
- 搜索代码
- 运行测试

Medium
- 修改普通源代码
- 创建文件
- 安装项目依赖

High
- 删除文件
- 修改环境变量
- Git push
- 数据库写入
- 外部 API 写操作
- 工作区外访问
```

### 11.3 回滚与恢复

- 写操作前 checkpoint。
- 每个 Task 独立 diff。
- Run 结束时保留恢复点。
- 用户可以按 Task 回滚。
- Agent 连续失败时自动恢复到最近稳定 checkpoint。

---

## 12. 不应该立即做的内容

下一阶段暂缓：

- 更多纯展示页面。
- 更复杂像素动画。
- 大量固定 Agent 角色。
- Skill Marketplace。
- 多人企业权限体系。
- 全自动浏览器与桌面控制。
- 邮件、日历和社交平台接入。
- 完全自动长期记忆写入。
- 大型项目完全无人监督开发。
- 为了多 Agent 而强制多 Agent。

判断原则：

> 不能增强“真实执行、验证、恢复、交接和复用”的功能，暂时都不是最高优先级。

---

## 13. 最终成熟度里程碑

### Level 0：Workflow Demo

- Mock 输出
- 固定链路
- 可视化状态

### Level 1：Live Model Agent

- 真实模型
- 真实日志
- 单 Agent 推理

### Level 2：Tool-Using Agent

- 文件读写
- 终端执行
- 真实环境观察

### Level 3：Verified Coding Agent

- 修改代码
- 运行测试
- 自动修复
- 证据验收

### Level 4：Dynamic Multi-Agent

- 动态任务图
- 按需调用 Agent
- 重规划
- 并行子 Agent

### Level 5：Resumable Multi-Model Agent

- 真实 Handoff
- 上下文压缩
- 模型接力
- 中断恢复

### Level 6：Self-Evolving Agent Team

- 执行前 Memory 检索
- 任务后 Skill 沉淀
- 模型表现学习
- 协作策略优化

本轮开发的现实目标应是：

> 先达到 Level 3，再进入 Level 4 和 Level 5。

不要在 Level 2 尚未完成时，优先宣传 Level 6。

---

## 14. 下一步立即执行清单

### 第一优先级

1. 让 Runtime 正式默认使用 Model Manager 中的真实模型。
2. 禁止生产模式静默回退 Mock。
3. 建立统一 Model Gateway 与错误结构。
4. 增加 `execution_mode`。

### 第二优先级

5. 实现 `file_write / file_patch`。
6. 实现 `terminal_execute`。
7. 实现 Workspace Root 隔离。
8. 实现 checkpoint 与 diff。

### 第三优先级

9. 选择一个固定 Bug Fix Benchmark。
10. 打通读取 → 修改 → 测试 → 修复 → 再测试。
11. 增加 Completion Contract。
12. 只有测试通过才标记 `completed_verified`。

### 第四优先级

13. 将固定 Planner → Coder → Reviewer 改成 Orchestrator 动态 Task Graph。
14. Agent 按 capability 选择。
15. 支持 replan 与返工任务。

### 第五优先级

16. 重构 Handoff Package。
17. 让接手 Agent 检查 Workspace 后继续执行。
18. 建立模型 A → 模型 B 的真实接力测试。

### 第六优先级

19. 将 Memory 接入执行前 Context Builder。
20. 任务通过验证后生成 Skill Candidate。
21. 建立用户审核后写入机制。

---

## 15. 建议的第一轮 Claude Code / Codex 开发指令

```text
请基于当前 ModelGate Agent Studio 仓库实施 Runtime v2 的第一阶段：真实模型执行接管。

目标：
将正式运行路径从默认 Mock Provider 改为从 Model Manager 中选择已启用、已配置且健康的真实模型。Mock 只能在显式 mock 模式或测试环境中使用，禁止生产模式静默回退 Mock。

本轮只完成以下内容：
1. 审查当前 Provider Factory、Model Manager、Runtime Service 和相关 Schema。
2. 设计并实现统一 Model Gateway。
3. 将 Model Manager 中的真实 Provider 配置接入 Runtime。
4. 增加 execution_mode：live、dry_run、sandbox、mock。
5. live 模式无真实模型时返回明确错误。
6. 保存 provider、model、耗时、token、错误和 request id。
7. 更新前端执行状态，明确显示 Live 或 Mock。
8. 补充单元测试与集成测试。
9. 不修改像素办公室和无关页面。

开始编码前：
- 先阅读相关文件。
- 输出当前调用链和修改计划。
- 列出准备修改的文件。

完成后必须：
- 运行相关测试。
- 输出真实修改文件列表。
- 输出 git diff 摘要。
- 输出测试结果。
- 说明仍未完成的风险。

验收标准：
- live 模式调用真实模型。
- 未配置真实模型时不会回退 Mock。
- mock 模式仍能支持自动化测试。
- 前端和日志可以区分真实运行与模拟运行。
```

---

## 16. 最终判断

ModelGate Agent Studio 现有方向不需要推翻。

现有的多模型管理、Agent Registry、Quota、Handoff、Supervisor、Memory Draft、Logs 和 Workspace 都是后续真正 Agent 的控制面基础。

需要推翻的是开发优先级：

```text
旧优先级：
模块数量
→ 页面完整度
→ 工作流演示
→ Agent 外观

新优先级：
真实模型
→ 真实工具
→ 真实环境
→ 真实验证
→ 自动修复
→ 动态编排
→ 真实交接
→ Memory / Skill 复用
→ 可视化呈现真实过程
```

产品真正跨过 Agent 门槛的标志不是新增多少 Agent，而是完成下面这件事：

> 用户给出一个真实开发目标，系统能够自主读取项目、决定步骤、调用合适模型和工具、修改文件、执行测试、根据错误继续修复，并最终用可验证证据证明任务完成。

当这条链路稳定跑通后，ModelGate Agent Studio 才真正从：

> Multi-Agent Workflow Prototype

升级为：

> Verified Multi-Model Agent Runtime

然后再以 Handoff、额度调度、Memory、Skill 和像素化可视工作区形成自己的差异化。
