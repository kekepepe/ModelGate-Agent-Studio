# ModelGate Agent Studio 产品路线图

> 本文件是 ModelGate Agent Studio 的项目总路线。后续版本规划以本文档为主，已有的 MVP 冻结文档、Workspace PRD、API Contract 和 Schema 文档作为对应阶段的详细执行依据。

## 0. 路线图原则

ModelGate Agent Studio 的核心不是“接入很多模型”，而是把不同模型组织成可协作、可交接、可沉淀经验的 Agent 团队。

版本推进必须遵守以下原则：

1. **V0 只跑通演示闭环**：证明“Goal → Task → Agent → Handoff → Workspace → Final Summary”成立。
2. **MVP 覆盖核心产品对象**：Goal、Task、Agent、Model Router、Handoff、Workspace 必须形成真实可用的产品骨架。
3. **V1 再做自进化**：Memory、Skill Library、Knowledge Evolution 不提前塞进 V0，避免污染核心闭环。
4. **先串行后并行**：早期用线性流程降低复杂度，等核心状态稳定后再做并行调度和复杂依赖图。
5. **先本地单用户后平台化**：短期不做多人协作、账号权限、市场生态。
6. **先可解释后自动化**：所有自动拆解、路由、交接、记忆写入都要让用户看得见、可确认、可追溯。

---

## 1. 阶段总览

| 阶段 | 目标 | 核心判断 | 不做什么 |
|------|------|----------|----------|
| V0 | 可以跑通演示的最小闭环 | 用户能看到多个 Agent 围绕一个 Goal 协作并完成一次交接 | 不追求真实复杂执行、不做 Memory、不做 Skill、不做复杂动画 |
| MVP | 核心工作台可用 | Goal、Task、Agent、Model Router、Handoff、Workspace 形成稳定产品骨架 | 不做自动知识进化、不做插件生态、不做多人协作 |
| V1 | 形成自进化知识闭环 | 任务结束后能沉淀 Memory、生成 Skill 草稿，并在新任务中被调用 | 不做市场、不做企业权限、不做全自动无审核写入 |

---

## 2. V0：演示闭环版

### 2.1 阶段目标

V0 只做一个可以完整演示的最小闭环：

```text
用户输入 Goal
↓
Planner 拆解 Task
↓
任务分配给 Agent
↓
Agent 状态流转
↓
手动触发 Handoff
↓
生成 Handoff Summary
↓
接手 Agent 继续执行
↓
Supervisor 生成最终汇总
↓
Workspace 展示完整过程
```

V0 的成功标准不是“Agent 真正自动完成复杂开发任务”，而是让用户一眼看懂 ModelGate 的核心产品价值：多模型 Agent 可以像团队一样协作、交接、被观察。

### 2.2 功能范围

#### P0 功能

| 功能 | 说明 |
|------|------|
| Goal 输入 | 用户可以输入一个目标并启动流程 |
| 简单 Task 拆解 | 将 Goal 拆成 3-5 个线性任务 |
| 固定 Agent Station | Planner、Coder、Reviewer、Summarizer、Supervisor |
| Mock Model + 少量真实模型 | 内置 Mock Model，支持至少一种真实 OpenAI-compatible 调用 |
| 简单任务分配 | 按固定规则把 Task 分给 Agent |
| Agent 状态流转 | idle、running、handoff、done、error 等基础状态可视化 |
| 半模拟执行 | Agent 输出可以使用模板、Mock 或少量真实模型调用 |
| 手动 Handoff | 用户可以手动触发一次交接 |
| Handoff Summary | 生成结构化交接摘要 |
| 最终汇总 | Supervisor 输出最终结果 |
| 执行日志 | 记录关键事件、状态变化和交接事件 |

#### P1 功能

| 功能 | 说明 |
|------|------|
| 基础模型配置 | 支持录入 provider、model_name、base_url、api_key 状态 |
| 基础 Agent 配置 | 支持查看固定 Agent 的职责、默认模型、备用模型 |
| Quota 模拟 | 手动设置模型额度上限，支持“模拟额度不足”触发交接 |
| Demo Script | 固定一条可稳定演示的 Demo 用例 |

### 2.3 页面范围

| 页面 | V0 范围 | 验收重点 |
|------|---------|----------|
| Workspace | P0，核心页面 | 可以输入 Goal、展示任务卡片、Agent 状态、Handoff、日志、最终汇总 |
| Dashboard | P1，轻量入口 | 展示最近 Goal、活跃状态、快速进入 Workspace |
| Agent Registry | P1，只读为主 | 查看固定 Agent 列表和职责 |
| Models | P1，最小配置 | 配置 Mock Model 和少量真实模型 |
| Handoff | P1，记录查看 | 查看一次完整交接记录和摘要 |
| Logs | P1，事件日志 | 查看 Goal 执行全过程日志 |
| Quota | P2，可并入 Models 或 Workspace | 展示模拟额度状态即可 |

### 2.4 后端模块

| 模块 | V0 范围 |
|------|---------|
| Goal Service | 创建 Goal、启动 Goal、更新 Goal 状态、保存 final_summary |
| Planner Service | 基于模板或模型调用生成 3-5 个 Task |
| Task Service | 创建 Task、更新状态、保存输出 |
| Agent Registry | 初始化固定 Agent Station，提供查询接口 |
| Simple Runtime | 串行执行 Task，写入 WorkerSession 和 ExecutionLog |
| Model Gateway | 支持 Mock Model 与 OpenAI-compatible 基础调用 |
| Handoff Manager | 手动触发交接，生成结构化 Handoff Summary |
| Log Service | 记录执行事件、模型调用、状态变化、交接事件 |
| Workspace State Adapter | 聚合 Goal、Task、Agent、Worker、Handoff、Log 给前端渲染 |

### 2.5 数据对象

V0 只落地核心对象：

| 数据对象 | V0 字段要求 |
|----------|-------------|
| Goal | id、title、description、status、progress、final_summary、created_at、updated_at |
| Task | id、goal_id、title、description、status、assigned_agent_id、output、completion_criteria |
| AgentStation | id、name、role、description、status、default_model_id、backup_model_ids、allow_handoff |
| Model | id、provider、model_name、display_name、capability_tags、is_enabled、quota_token_daily_limit、quota_token_daily_used |
| WorkerSession | id、agent_id、model_id、goal_id、task_id、status、current_context、final_output |
| HandoffRecord | id、goal_id、task_id、from_agent_id、to_agent_id、reason、handoff_summary、status、result_after_handoff |
| ExecutionLog | id、goal_id、task_id、agent_id、level、action、message、created_at |
| WorkspaceState | 前端聚合对象，不持久化，用于 Card Flow View 和 Pixel Office View 共享状态 |

### 2.6 验收标准

V0 完成的标志是可以稳定跑完以下 Demo：

1. 用户在 Workspace 输入一个 Goal。
2. 点击开始后，Planner 生成 3-5 个 Task。
3. Task 依次分配给 Coder、Reviewer、Summarizer、Supervisor。
4. Card Flow View 中可以看到 Agent Card、状态颜色、任务流转。
5. 每个 Agent 至少产生一段中间输出。
6. 用户可以手动触发一次 Handoff。
7. 系统生成结构化 Handoff Summary。
8. 接手 Agent 读取交接摘要并继续执行。
9. Supervisor 生成最终汇总。
10. Logs 页面或 Bottom Console 能看到完整执行记录。
11. Handoff 页面能看到交接记录和摘要。
12. 切换到 Pixel Office View 时，能看到固定工位和当前状态，不要求复杂动画。

---

## 3. MVP：核心工作台版

### 3.1 阶段目标

MVP 要从“可演示”升级为“核心工作台可用”。这一阶段必须覆盖：

```text
Goal
Task
Agent
Model Router
Handoff
Workspace
```

MVP 的目标是让用户可以用 ModelGate 管理真实的多 Agent 任务流程，但仍然不追求完全自动化开发、不做完整自进化知识库。

### 3.2 功能范围

#### Goal

| 功能 | 说明 |
|------|------|
| Goal 创建与管理 | 创建、查看、暂停、继续、完成 Goal |
| Goal 运行配置 | 是否允许多 Agent、是否允许自动模型切换、是否允许 Handoff |
| Goal 进度统计 | 展示 total_tasks、completed_tasks、handoff_count、tokens_used |
| Final Summary | Supervisor 生成最终报告 |

#### Task

| 功能 | 说明 |
|------|------|
| 任务树 | Task 支持 parent_task_id 和 dependencies |
| 状态管理 | pending、assigned、running、waiting、handoff、completed、failed |
| 手动运行 Task | 用户可以单独运行或重跑某个 Task |
| 输出保存 | 每个 Task 保存 output、tokens_used、duration_ms |
| 简单依赖处理 | 依赖未完成时进入 waiting，不做复杂 DAG 自动优化 |

#### Agent

| 功能 | 说明 |
|------|------|
| Agent Registry | 创建、查看、编辑 Agent Station |
| 角色职责 | Planner、Coder、Reviewer、Research、Summarizer、Supervisor |
| 模型绑定 | default_model_id、backup_model_ids |
| Prompt 配置 | system_prompt、output_format_requirement |
| 执行限制 | max_steps_per_task、allow_handoff、handoff_threshold_tokens |
| 状态统计 | completed_count、handoff_count、average_tokens |

#### Model Router

| 功能 | 说明 |
|------|------|
| 模型能力标签 | code、planning、review、long-context、fast、low-cost 等 |
| 路由规则 | 按任务类型、Agent 角色、能力标签、上下文长度、成本、额度选择模型 |
| 备用模型 | 当前模型不可用或额度告警时选择 backup model |
| 路由解释 | 在 Agent Detail 中展示“为什么选择这个模型” |
| Quota 感知 | 使用手动配置和实际 token 统计判断 warning/blocked |

#### Handoff

| 功能 | 说明 |
|------|------|
| 手动 Handoff | 用户从 Task 或 Agent Detail 中触发交接 |
| 半自动 Handoff | 额度达到阈值、模型报错、任务失败时提示交接 |
| Handoff Summary | 保存 original_goal、current_task、completed_work、unfinished_work、constraints、decisions、risks、next_steps |
| 接手流程 | 新 WorkerSession 继承 handoff_summary 并继续执行 |
| 交接历史 | Handoff 页面可筛选、查看详情、查看接手结果 |

#### Workspace

| 功能 | 说明 |
|------|------|
| Card Flow View | 默认视图，展示 Agent Card、Task 流转、状态、连线 |
| Pixel Office View | 差异化视图，展示固定工位、Worker、任务文件夹、Handoff 表达 |
| Agent Detail Modal | Overview、Task、Context、Tools、History 五个 Tab |
| Station Popover | Pixel 视图点击工位展示轻量详情 |
| Bottom Console | Event Log、Model Calls、Token Usage、Handoff Records、Error Logs |
| 双视图共享状态 | 使用同一份 WorkspaceState，不因切换视图中断任务 |
| 错误状态 | Agent 出错时卡片变红、日志展开、提供 Retry 或 Handoff |

### 3.3 页面范围

| 页面 | MVP 范围 |
|------|----------|
| Dashboard | 活跃 Goal、最近任务、Agent 状态、模型额度、最近 Handoff |
| Workspace | 核心工作区，双视图、任务树、运行配置、详情、日志 |
| Agent Registry | Agent 列表、创建、编辑、默认模型、备用模型、Prompt 配置 |
| Models | Provider 配置、模型列表、能力标签、连接测试、启用/禁用 |
| Quota | 每个模型请求数、token 用量、阈值、告警、历史趋势 |
| Handoff | 交接列表、详情、摘要、原因、接手结果 |
| Logs | 全局日志、按 Goal/Task/Agent/level 筛选 |

### 3.4 后端模块

| 模块 | MVP 范围 |
|------|----------|
| Goal Service | 完整 Goal 生命周期、统计字段、暂停/继续 |
| Task Planner | 模型生成 + 模板兜底，支持简单依赖 |
| Task Orchestrator | 串行执行、依赖等待、失败处理、重跑 |
| Agent Registry Service | Agent CRUD、Prompt 配置、模型绑定 |
| Model Service | Provider 与 Model CRUD、连接测试、能力标签 |
| Model Router | 按角色、任务、标签、成本、额度选择模型并返回解释 |
| Agent Runtime | 加载任务、调用模型、保存 WorkerSession、写日志、保存输出 |
| Quota Manager | 统计 token 和请求数，计算 warning/blocked，触发交接建议 |
| Handoff Manager | 生成、保存、接受、完成 Handoff |
| Workspace Aggregator | 为前端输出 WorkspaceState、CardFlowData、PixelOfficeData |
| Log Service | 统一执行日志、模型调用日志、错误日志 |
| WebSocket/SSE | 推送 Task 状态、Log、Handoff、Goal 进度更新；若实现成本高，可先用轮询 |

### 3.5 数据对象

MVP 数据对象以现有 Schema 为主：

| 数据对象 | MVP 要求 |
|----------|----------|
| Goal | 完整生命周期、运行配置、统计和 final_summary |
| Task | 任务树、依赖、状态、输出、重试、Handoff 关联 |
| AgentStation | 可配置角色、模型、工具权限、Prompt、执行限制 |
| Model | Provider、能力标签、上下文、成本、速度、额度、API 配置 |
| WorkerSession | 单次任务执行实例，记录模型、上下文、token、输出、错误 |
| HandoffRecord | 完整交接摘要、原因、状态、接手结果、token 前后对比 |
| ExecutionLog | 支持按 Goal、Task、Agent、Worker、Model、Handoff 查询 |
| QuotaUsage | 按模型和日期统计请求数、token、使用比例 |
| WorkspaceState | 前端聚合态，保持双视图一致 |

### 3.6 验收标准

MVP 完成的标志：

1. 用户可以创建多个 Goal，并查看进行中、已完成、失败状态。
2. 一个 Goal 可以被拆成多个 Task，Task 有状态、依赖、输出和完成标准。
3. 用户可以创建或编辑 Agent Station，并绑定默认模型和备用模型。
4. Models 页面可以配置至少 3 类 Provider：OpenAI-compatible、Anthropic、DeepSeek，另有 Mock Model。
5. Model Router 能根据任务类型、Agent 角色、能力标签和额度状态选择模型。
6. Agent Detail 中能解释当前任务为什么选择该模型。
7. Workspace 可以展示 Card Flow View 和 Pixel Office View，并共享同一份运行状态。
8. 用户可以手动触发 Handoff，系统也能在额度 warning 或模型错误时建议 Handoff。
9. Handoff Summary 足够完整，接手 Agent 不需要重新询问用户即可继续。
10. Logs 能完整追踪一次 Goal 从创建到完成的关键事件。
11. Quota 页面能展示模型 token/request 用量和告警状态。
12. Supervisor 能根据 Task 输出生成最终汇总，并更新 Goal 为 completed 或 failed。

---

## 4. V1：自进化知识版

### 4.1 阶段目标

V1 在 MVP 的协作工作台基础上加入：

```text
Memory
Skill Library
Knowledge Evolution
```

V1 的核心目标是让系统不只完成一次任务，而是能从任务中沉淀经验，并在下一次任务中复用。

### 4.2 功能范围

#### Memory

| 功能 | 说明 |
|------|------|
| Memory Draft | 任务完成后生成可保存的记忆草稿 |
| Memory 类型 | Project Memory、User Preference、Agent Experience、Handoff Memory、Model Routing Rule |
| 人工确认 | 长期 Memory 必须经过用户确认后写入 |
| Memory 管理 | 查看、编辑、删除、禁用 Memory |
| 来源追溯 | 每条 Memory 关联 source_goal_id、source_task_id、source_agent_id |
| 基础检索 | 新任务开始前按项目、标签、类型检索相关 Memory |
| 置信度 | 支持 confidence 字段，但早期不做复杂自动评分 |

#### Skill Library

| 功能 | 说明 |
|------|------|
| 手动创建 Skill | 用户可以创建结构化任务执行模板 |
| Skill 草稿 | Knowledge Evolution Agent 可从任务中生成 Skill Draft |
| Skill 审核 | 用户确认后 Skill 才能启用 |
| Skill 调用 | Planner 或 Agent Runtime 可加载 Skill 步骤和 Prompt 模板 |
| Skill 版本 | 支持基础 version、is_active、updated_at |
| Skill 统计 | usage_count、success_rate、average_duration_ms |

#### Knowledge Evolution

| 功能 | 说明 |
|------|------|
| Knowledge Evolution Agent | 任务结束后复盘 Goal、Task、日志、Handoff、模型表现和最终输出 |
| 经验提取 | 提取用户偏好、项目决策、错误修复、可复用流程、模型路由经验 |
| Skill 识别 | 判断某段流程是否值得形成 Skill Draft |
| Review Flow | 在 Evolution Review 页面让用户确认、编辑、拒绝沉淀内容 |
| 反馈闭环 | 用户接受或拒绝的结果影响后续生成质量 |

### 4.3 页面范围

| 页面 | V1 范围 |
|------|---------|
| Knowledge Base | 查看和管理 Memory，按类型、项目、标签、来源筛选 |
| Skill Library | Skill 列表、新建、编辑、启用/禁用、版本、统计 |
| Evolution Review | 任务完成后审核 Memory Draft、Skill Draft、路由规则草稿 |
| Handoff Memory | 从交接历史中查看成功交接经验，可保存为 Handoff Skill |
| Model Performance | 记录模型在不同任务类型中的表现、失败案例、用户评分 |
| Workspace 增强 | Agent Detail 的 Context Tab 展示 retrieved_memories 和 applied_skills |

### 4.4 后端模块

| 模块 | V1 范围 |
|------|---------|
| Memory Service | Memory CRUD、审核状态、启用/禁用、来源追溯 |
| Memory Retriever | 按类型、标签、项目、任务语义做基础检索；向量检索可后置 |
| Skill Service | Skill CRUD、版本、启用状态、使用统计 |
| Skill Runtime Adapter | 将 Skill 步骤、Prompt 模板、推荐 Agent 注入任务流程 |
| Knowledge Evolution Agent | 任务后复盘并生成 Memory Draft、Skill Draft、Routing Rule Draft |
| Evolution Review Service | 保存用户确认、修改、拒绝记录 |
| Model Performance Service | 统计模型在任务类型、Agent 角色、Handoff 后的表现 |
| RAG Adapter | 初期可用关键词/标签检索，后续再接 pgvector 或向量数据库 |

### 4.5 数据对象

| 数据对象 | V1 要求 |
|----------|---------|
| MemoryItem | id、type、title、content、tags、source_task_id、source_goal_id、source_agent_id、confidence、human_approved、usage_count、embedding、expires_at |
| Skill | id、name、description、applicable_scenarios、input_schema、output_schema、steps、prompt_template、usage_count、success_rate、version、is_active |
| EvolutionReviewItem | id、goal_id、task_id、type、draft_content、status、user_feedback、created_at、reviewed_at |
| ModelPerformanceRecord | id、model_id、agent_role、task_type、success、latency_ms、tokens_used、user_rating、failure_reason |
| RoutingRuleDraft | id、source_task_id、condition、recommended_model_id、reason、confidence、human_approved |
| HandoffMemory | 可复用 Handoff 经验，可由 HandoffRecord 提炼生成 |

### 4.6 验收标准

V1 完成的标志：

1. 一个 Goal 完成后，Knowledge Evolution Agent 自动生成 Memory Draft。
2. 用户可以在 Evolution Review 页面确认、编辑或拒绝 Memory Draft。
3. 被确认的 Project Memory 能在 Knowledge Base 中看到，并保留来源任务。
4. 用户可以手动创建一个 Skill，并在新任务中选择或自动推荐使用。
5. 系统可以从一次成功流程中生成 Skill Draft，用户确认后进入 Skill Library。
6. 新 Goal 开始时，系统能加载相关 Memory 或 Skill，并在 Agent Detail 中展示来源。
7. Handoff 成功经验可以被保存为 Handoff Memory 或 Handoff Skill。
8. Model Performance 页面可以看到不同模型在任务类型上的基础表现统计。
9. 所有长期知识写入都需要用户确认，不允许默认全自动写入。
10. 用户可以删除或禁用错误 Memory，后续任务不会继续调用。

---

## 5. 明确暂缓功能

以下功能不进入 V0、MVP、V1 的核心范围，避免项目过大。

### 5.1 平台和账号类

| 功能 | 暂缓原因 |
|------|----------|
| 用户登录系统 | 本地单用户足够验证核心价值 |
| 多人协作 | 会引入权限、同步、冲突处理，超出早期范围 |
| 团队知识库 | 需要账号、权限、审计和同步机制 |
| 企业权限管理 | 当前不是企业级 SaaS 阶段 |
| 多端同步 | 会增加数据一致性和安全复杂度 |

### 5.2 生态和市场类

| 功能 | 暂缓原因 |
|------|----------|
| Agent Marketplace | 需要分发、审核、评分、版本兼容机制 |
| Skill Marketplace | 需要质量控制和安全审核 |
| 插件市场 | MCP 工具生态未稳定前不做市场 |
| 第三方付费机制 | 不是当前产品验证重点 |

### 5.3 高风险自动化

| 功能 | 暂缓原因 |
|------|----------|
| 全自动修改本地项目文件 | 需要权限、diff、回滚、安全边界 |
| Agent 自主执行高风险终端命令 | 安全风险高，必须等权限系统成熟 |
| 完整浏览器自动化 | 工程复杂度高，早期不影响核心价值验证 |
| 自动读取所有 Coding Plan 真实额度 | 第三方限制不可控，先用手动配置和统计估算 |

### 5.4 高级智能能力

| 功能 | 暂缓原因 |
|------|----------|
| 全自动长期 Memory 写入 | 容易污染知识库，V1 仍坚持人工确认 |
| 复杂置信度评分算法 | 需要大量真实使用数据 |
| Memory 自动过期策略 | 规则复杂，先做手动删除/禁用 |
| 元学习自动改 Prompt | 风险高，可解释性弱 |
| 跨项目知识迁移 | 需要成熟 Memory 分类和权限边界 |

### 5.5 复杂调度和架构

| 功能 | 暂缓原因 |
|------|----------|
| 复杂并行 Agent 调度 | 先保证串行状态机稳定 |
| 复杂 DAG 工作流编辑器 | 容易变成通用 Workflow Builder，偏离核心定位 |
| 微服务拆分 | 单体架构足够早期开发 |
| 事件驱动全量重构 | 等真实瓶颈出现后再做 |
| Kubernetes / 企业部署 | V1 之前不需要 |

---

## 6. 推荐开发顺序

### 6.1 V0 开发顺序

```text
1. 定义核心状态枚举和数据对象
2. 实现 Goal 创建和启动
3. 实现 Task 拆解模板或简单模型调用
4. 初始化固定 Agent Station 和 Mock Model
5. 实现串行 Runtime 和 ExecutionLog
6. 实现 Workspace Card Flow View
7. 实现 Agent Detail Modal 和 Bottom Console
8. 实现手动 Handoff 和 Handoff Summary
9. 实现 Supervisor Final Summary
10. 补齐 Handoff/Logs/Models 的最小页面
11. 加入 Pixel Office 静态视图
12. 固化 Demo Script 和验收用例
```

### 6.2 MVP 开发顺序

```text
1. 完善数据库 Schema 和 API Contract
2. 完善 Agent Registry 与 Models 配置
3. 实现 Model Router 和路由解释
4. 实现 Quota Manager 与 warning/blocked 状态
5. 完善 Task 依赖、重跑、失败处理
6. 完善 Handoff 接受、完成、接手流程
7. 完善 Workspace 双视图同步
8. 加入 Dashboard、Quota、Handoff、Logs 完整查询
9. 加入 WebSocket/SSE 或稳定轮询
10. 做端到端测试和 Demo 稳定性优化
```

### 6.3 V1 开发顺序

```text
1. 实现 MemoryItem 和 Skill 数据结构
2. 实现 Knowledge Base 和 Skill Library 基础 CRUD
3. 实现任务结束后的 Evolution Review 流程
4. 实现 Knowledge Evolution Agent 生成 Memory Draft
5. 实现用户确认后写入 Memory
6. 实现 Skill Draft 生成和审核启用
7. 实现新任务启动前加载相关 Memory/Skill
8. 在 Agent Detail 中展示 retrieved_memories 和 applied_skills
9. 实现 Model Performance 基础统计
10. 优化 Memory 防污染和用户可控机制
```

---

## 7. 版本边界确认

### V0 必须克制

V0 只回答一个问题：

> ModelGate 的“多 Agent 协作 + Handoff + Workspace 可视化”是否能被用户看懂？

只要能稳定跑通 Demo，V0 就成功。任何不影响 Demo 闭环的能力都不进入 V0。

### MVP 必须完整

MVP 回答的问题是：

> ModelGate 是否已经具备一个多模型 Agent 工作台的核心骨架？

Goal、Task、Agent、Model Router、Handoff、Workspace 六个对象缺一不可。

### V1 必须可控

V1 回答的问题是：

> ModelGate 是否能从历史任务中沉淀经验，并让下一次任务更好？

但所有长期知识写入必须可审核、可追溯、可删除，不能为了“智能”牺牲可靠性。
