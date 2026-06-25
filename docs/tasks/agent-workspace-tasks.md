# Agent Workspace 开发任务拆解

> 基于 `docs/stories/agent-workspace-stories.md` 的 6 条 P0 + 2 条 P1 用户故事拆解
>
> 拆分模式：Workflow Steps (Pattern 1) + Simple/Complex (Pattern 7)
> ——先做 Goal/Task 数据模型和状态聚合 API，再搭建 Workspace 页面框架，最后集成 Logs/Handoff/Quota/Router 的已有组件。

---

## Epic: Agent Workspace

**目标：** 提供一个统一的 Workspace 页面，让用户输入 Goal、启动任务、实时观察 Task/Agent/Worker 状态变化、查看执行日志和 Handoff 过程。

**Epic 验收标准：**
1. 用户在左侧输入 Goal 并点击开始，系统创建 Goal 并进入 planning 状态
2. Workspace 中间实时展示 TaskCard 状态变化（颜色、图标、动画同步更新）
3. 点击 TaskCard 右侧展开 TaskDetailPanel，展示任务详情和输出
4. AgentStationBoard 展示每个 Agent Station 和绑定的 Worker 状态
5. 底部 ExecutionLogPanel 实时追加执行日志
6. Handoff 发生时 TaskCard 显示 HandoffStatusIndicator（P0）
7. WorkerBadge 显示 RiskBadge 反映模型额度状态（P1）
8. 模型路由决策时弹出 RoutingResultCard（P1）

---

## Feature 1: Workspace 核心数据模型

> 对应 Story: US-AW-01 / US-AW-02 / US-AW-03 / US-AW-04
> 说明：Goal、Task、WorkerSession 的表结构和状态枚举是 Workspace 的根基，也是其他模块的依赖基础。

### Task 1.1: 创建 goals 数据库表

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T1.1 |
| **story_id** | US-AW-01 / US-AW-02 |
| **任务类型** | database |
| **文件** | `migrations/00x_create_goals.sql` |
| **任务说明** | 创建 `goals` 表，字段对齐 Goal 接口：id, title, description, status, created_at, updated_at。status 默认值为 idle。创建索引 idx_status。 |
| **完成标准** | 1. 迁移脚本执行成功<br>2. 字段类型、NOT NULL 约束、默认值正确<br>3. 索引覆盖按 status 查询场景 |
| **依赖任务** | 无 |
| **推荐顺序** | 1 |

---

### Task 1.2: 创建 tasks 数据库表

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T1.2 |
| **story_id** | US-AW-01 / US-AW-02 / US-AW-03 |
| **任务类型** | database |
| **文件** | `migrations/00x_create_tasks.sql` |
| **任务说明** | 创建 `tasks` 表，字段对齐 Task 接口：id, goal_id, title, description, status, assigned_agent_id, assigned_worker_id, output, tokens_used, duration_ms, priority, created_at, updated_at。外键关联 goals.id。创建索引 idx_goal_id、idx_status、idx_assigned_agent_id。 |
| **完成标准** | 1. 迁移脚本执行成功<br>2. 外键关系正确，级联删除<br>3. 索引覆盖高频查询场景（按 goal / status / agent 查询）<br>4. 字段类型与 TypeScript 接口对齐 |
| **依赖任务** | AW-T1.1 |
| **推荐顺序** | 2 |

---

### Task 1.3: 创建 worker_sessions 数据库表

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T1.3 |
| **story_id** | US-AW-04 |
| **任务类型** | database |
| **文件** | `migrations/00x_create_worker_sessions.sql` |
| **任务说明** | 创建 `worker_sessions` 表，字段对齐 WorkerSession 接口：id, agent_id, model_id, goal_id, task_id, inherited_from_handoff_id, status, total_tokens_used, created_at, updated_at。外键关联 tasks.id、agents.id。创建索引 idx_agent_id、idx_task_id、idx_status。 |
| **完成标准** | 1. 迁移脚本执行成功<br>2. 外键关系正确<br>3. 索引覆盖高频查询场景<br>4. inherited_from_handoff_id 可为 null |
| **依赖任务** | AW-T1.2 |
| **推荐顺序** | 3 |

---

### Task 1.4: 定义 GoalStatus / TaskStatus / WorkerStatus / AgentStatus 枚举与流转规则

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T1.4 |
| **story_id** | US-AW-01 / US-AW-02 / US-AW-04 |
| **任务类型** | backend |
| **文件** | `src/domain/workspace.ts` |
| **任务说明** | 1. 定义 `GoalStatus` 枚举：idle / planning / running / waiting / handoff / reviewing / completed / failed<br>2. 定义 `TaskStatus` 枚举：pending / assigned / running / completed / failed / handoff<br>3. 定义 `WorkerStatus` 枚举：idle / running / handoff_required / completed / failed<br>4. 定义 `AgentStatus` 枚举：idle / running / error / disabled / queued / reviewing / blocked / done（与 Agent Registry 对齐）<br>5. 实现状态流转校验器：Goal idle → planning → running → completed/failed；Task pending → assigned → running → completed/failed；非法转换返回 400<br>6. 实现状态颜色映射函数（供前端复用） |
| **完成标准** | 1. 枚举值与 PRD / Schema 文档完全一致<br>2. 状态流转校验覆盖全部合法/非法路径<br>3. 状态颜色映射函数返回正确颜色值（pending=灰/running=蓝/completed=绿/failed=红/handoff=紫）<br>4. 单元测试覆盖全部枚举和流转规则 |
| **依赖任务** | AW-T1.1 / AW-T1.2 / AW-T1.3 |
| **推荐顺序** | 4 |

---

## Feature 2: Goal + Task 核心 API

> 对应 Story: US-AW-01 / US-AW-02 / US-AW-03 / US-AW-04

### Task 2.1: POST /goals + POST /goals/:goalId/start API

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T2.1 |
| **story_id** | US-AW-01 |
| **任务类型** | backend |
| **文件** | `src/routes/goals.ts`、`src/services/workspace/goal.service.ts` |
| **任务说明** | 1. `POST /goals`：接收 { title, description }，创建 Goal status=idle，返回 { goal_id, status: "idle" }<br>2. `POST /goals/:goalId/start`：校验 Goal 存在且 status=idle，更新 status=planning，创建第一个 Task（分配给 Planner Agent，status=pending），触发 goal_status_changed 事件<br>3. 返回 { goal_id, status: "planning" }<br>4. MVP 阶段 Planner Agent 自动创建 Task 的逻辑用硬编码简化，不引入复杂的 Planning 引擎 |
| **完成标准** | 1. POST /goals 返回 201 + { goal_id, status }<br>2. POST /goals/:goalId/start 返回 200 + { goal_id, status }<br>3. Goal 不存在返回 404，非 idle 状态 start 返回 400<br>4. start 后自动创建 1 个初始 Task（分配给 Planner）<br>5. 集成测试覆盖 |
| **依赖任务** | AW-T1.1 / AW-T1.2 / AW-T1.4 |
| **推荐顺序** | 5 |

---

### Task 2.2: GET /tasks/:taskId 详情 API

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T2.2 |
| **story_id** | US-AW-03 |
| **任务类型** | backend |
| **文件** | `src/routes/tasks.ts`、`src/services/workspace/task.service.ts` |
| **任务说明** | 1. 实现 `GET /tasks/:taskId` 接口<br>2. 返回完整 Task 对象：id, goal_id, title, description, status, assigned_agent_id, assigned_worker_id, output, tokens_used, duration_ms, priority, created_at, updated_at<br>3. 关联 Agent 和 Worker 基本信息一并返回（agent_name, agent_role, model_name, worker_status）<br>4. 减少前端多次请求 |
| **完成标准** | 1. 正常请求返回 200 + 完整 Task JSON<br>2. taskId 不存在返回 404<br>3. 关联的 Agent 和 Worker 信息正确填充<br>4. 返回的 assigned_agent_id 和 assigned_worker_id 可关联到有效记录<br>5. 集成测试覆盖 |
| **依赖任务** | AW-T1.2 / AW-T1.3 |
| **推荐顺序** | 6 |

---

### Task 2.3: GET /workspace/:goalId/state 聚合状态查询 API

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T2.3 |
| **story_id** | US-AW-02 / US-AW-04 |
| **任务类型** | backend |
| **文件** | `src/routes/workspace.ts`、`src/services/workspace/workspace-state.service.ts` |
| **任务说明** | 1. 实现 `GET /workspace/:goalId/state` 接口——Workspace 的核心聚合接口<br>2. 返回结构：{ goal: Goal, tasks: Task[], agents: AgentStation[], workers: WorkerSession[] }<br>3. tasks[] 包含该 Goal 下的全部 Task 最新状态<br>4. agents[] 包含系统中全部 AgentStation（由 Agent Registry 模块维护，此处只查询）<br>5. workers[] 包含与该 Goal 相关的全部 WorkerSession，worker.agent_id 可关联到 Agent<br>6. Worker 的 model_id 对应 Model 表中的有效记录<br>7. 该接口供前端轮询使用（每 2 秒），响应需快速（< 100ms） |
| **完成标准** | 1. 正常请求返回 200 + 完整聚合状态<br>2. goalId 不存在返回 404<br>3. 返回的 tasks/agents/workers 数组完整<br>4. worker.agent_id 可正确关联到 Agent，worker.model_id 对应有效 Model<br>5. 响应时间 < 100ms（使用索引优化）<br>6. 集成测试覆盖 |
| **依赖任务** | AW-T1.1 / AW-T1.2 / AW-T1.3 / AW-T1.4 |
| **推荐顺序** | 7 |

---

## Feature 3: Workspace 页面框架 + Goal 输入

> 对应 Story: US-AW-01 / US-AW-02 / US-AW-04
> 说明：先做页面框架和布局（mock 数据），让页面可独立运行和视觉验收。

### Task 3.1: Workspace 页面框架 + 三栏布局（mock 数据）

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T3.1 |
| **story_id** | US-AW-01 / US-AW-02 / US-AW-04 |
| **任务类型** | frontend |
| **文件** | `src/pages/WorkspacePage.tsx`、`src/layouts/WorkspaceLayout.tsx` |
| **任务说明** | 1. 实现 Workspace 页面路由 `/workspace`<br>2. 三栏布局：左侧 GoalInputPanel + TaskTree（宽度 280px），中间 AgentStationBoard（弹性宽度），右侧 TaskDetailPanel（宽度 360px）<br>3. 底部 BottomConsole 区域（高度可展开/收起，收起时 40px，展开时 300px）<br>4. 使用 mock 数据让页面可独立运行：1 个 Goal + 4-5 个 Task（涵盖 pending/running/completed/failed/handoff）+ 3 个 Agent Station + 2-3 个 Worker<br>5. 布局使用 CSS Grid/Flexbox，支持响应式（最小宽度 1280px）<br>6. 预留 ExecutionLogPanel、HandoffStatusIndicator、RiskBadge、RoutingResultCard 的挂载点 |
| **完成标准** | 1. 页面可访问 `/workspace`<br>2. 三栏布局正确，各区域边界清晰<br>3. 底部区域可展开/收起，有平滑动画（300ms）<br>4. mock 数据覆盖 5 种 Task 状态和 3 种 Worker 状态<br>5. 页面最小宽度 1280px，不出现布局错乱 |
| **依赖任务** | 无（与后端并行） |
| **推荐顺序** | 8 |

---

### Task 3.2: GoalInputPanel 组件

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T3.2 |
| **story_id** | US-AW-01 |
| **任务类型** | frontend |
| **文件** | `src/components/GoalInputPanel.tsx` |
| **任务说明** | 1. 左侧 Goal 输入区：多行文本域（最小 3 行，最大 8 行），placeholder "描述你的目标..."<br>2. [开始] 按钮：空 Goal 时禁用（文本为空或仅空白字符）<br>3. 点击 [开始] 后：调用 POST /goals → POST /goals/:goalId/start，输入区收起，显示 "Planning..." 动画<br>4. Goal 创建成功后，TopStatusBar 状态标签变为紫色 planning<br>5. 错误时显示红色提示文本 "创建失败，请重试"<br>6. 支持已创建 Goal 的标题回显（只读模式） |
| **完成标准** | 1. 空 Goal 时 [开始] 按钮禁用<br>2. 点击开始后输入区收起，显示 "Planning..."<br>3. TopStatusBar 同步显示 planning 状态<br>4. API 错误时显示友好错误提示<br>5. 组件测试覆盖：空输入禁用、正常提交、错误处理 |
| **依赖任务** | AW-T2.1 / AW-T3.1 |
| **推荐顺序** | 9 |

---

### Task 3.3: TopStatusBar 组件

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T3.3 |
| **story_id** | US-AW-01 / US-AW-02 |
| **任务类型** | frontend |
| **文件** | `src/components/TopStatusBar.tsx` |
| **任务说明** | 1. 顶部固定状态栏：显示当前 Goal 标题（截断显示前 30 字）、状态标签、进度统计<br>2. 状态标签颜色映射：idle=灰/planning=紫/running=蓝/waiting=黄/handoff=紫/reviewing=橙/completed=绿/failed=红<br>3. 进度统计："已完成 3/5 个 Task" 或进度条<br>4. 右侧显示当前运行中的 Task 数量<br>5. 状态变化时有 300ms 过渡动画 |
| **完成标准** | 1. 状态标签颜色与 GoalStatus 严格对应<br>2. 进度统计数字正确（基于 Task 状态计算）<br>3. 状态变化有 300ms CSS transition<br>4. 组件测试覆盖全部 8 种 GoalStatus 渲染 |
| **依赖任务** | AW-T3.1 |
| **推荐顺序** | 10 |

---

## Feature 4: Task + Agent 状态可视化

> 对应 Story: US-AW-02 / US-AW-04
> 说明：TaskCard 和 AgentStationCard 是 Workspace 的核心视觉组件，先做 mock 数据跑通动画。

### Task 4.1: TaskCard 组件 + 状态颜色/图标/动画（mock 数据）

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T4.1 |
| **story_id** | US-AW-02 |
| **任务类型** | frontend |
| **文件** | `src/components/TaskCard.tsx`、`src/styles/animations.css` |
| **任务说明** | 1. 实现 TaskCard 组件：展示 Task 标题（前 2 行）、状态图标、优先级标记<br>2. 状态样式映射：<br>   - pending：灰色虚线边框 + ⏸ 图标<br>   - running：蓝色实线边框 + ▶ 图标 + breathe 动画（box-shadow 呼吸，2s infinite）<br>   - completed：绿色实线边框 + ✓ 图标<br>   - failed：红色实线边框 + ✗ 图标 + shake 动画（左右抖动 300ms）<br>   - handoff：紫色实线边框 + 🔄 图标 + rotate-border 动画<br>3. 状态变化时有 300ms CSS 过渡动画（border-color、background-color、box-shadow）<br>4. 点击 TaskCard 触发 onSelect 回调，边框高亮 1 秒后恢复<br>5. 先使用 mock 数据 |
| **完成标准** | 1. 5 种状态渲染正确，边框/图标/颜色与定义一致<br>2. running 状态的 breathe 动画流畅（CSS @keyframes）<br>3. failed 状态的 shake 动画只播放一次（300ms）<br>4. 状态切换有 300ms CSS transition<br>5. 点击后触发 onSelect，组件测试覆盖 |
| **依赖任务** | AW-T3.1 |
| **推荐顺序** | 11 |

---

### Task 4.2: AgentStationCard + WorkerBadge 组件（mock 数据）

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T4.2 |
| **story_id** | US-AW-04 |
| **任务类型** | frontend |
| **文件** | `src/components/AgentStationCard.tsx`、`src/components/WorkerBadge.tsx` |
| **任务说明** | 1. AgentStationCard：显示 Agent 名称、角色标签（Planner/Coder/Reviewer 等彩色标签）、当前 WorkerBadge 区域、状态边框<br>2. WorkerBadge：显示模型名称文本（如 "GPT-4o"）和状态灯（彩色圆点，8px）<br>3. WorkerBadge 状态灯映射：idle=灰色、running=蓝色（breathe 2s infinite）、handoff_required=紫色（脉冲）、completed=绿色、failed=红色（闪烁）<br>4. AgentStationCard 边框颜色随 AgentStatus 变化（同 TaskCard 状态色）<br>5. Handoff 后 WorkerBadge 模型名称平滑过渡到新模型（300ms CSS transition）<br>6. 先使用 mock 数据 |
| **完成标准** | 1. AgentStationCard 正确展示名称、角色标签、WorkerBadge<br>2. WorkerBadge 状态灯颜色与定义一致<br>3. running 状态灯有 breathe 动画<br>4. 模型名切换有 300ms transition<br>5. AgentStationCard 边框颜色与 AgentStatus 对应<br>6. 组件测试覆盖 |
| **依赖任务** | AW-T3.1 |
| **推荐顺序** | 12 |

---

### Task 4.3: TaskTree 组件

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T4.3 |
| **story_id** | US-AW-02 |
| **任务类型** | frontend |
| **文件** | `src/components/TaskTree.tsx` |
| **任务说明** | 1. 左侧 Goal 下方的任务树：以层级列表展示 Goal → Task 的关系<br>2. 每个 Task 行左侧显示状态图标（与 TaskCard 一致：⏸/▶/✓/✗/🔄）<br>3. 点击 Task 行可高亮对应 TaskCard（中间区域滚动到对应卡片并闪烁边框）<br>4. running 状态的 Task 行有左侧蓝色竖条标记<br>5. 支持 Task 数量统计（底部显示 "5 个 Task · 2 个进行中"） |
| **完成标准** | 1. 树形结构正确渲染全部 Task<br>2. 状态图标与 TaskCard 同步<br>3. 点击后中间区域 TaskCard 高亮（border flash 1 秒）<br>4. running 状态行有蓝色左侧竖条<br>5. 组件测试覆盖 |
| **依赖任务** | AW-T4.1 / AW-T3.1 |
| **推荐顺序** | 13 |

---

## Feature 5: Task 详情面板 + 真实数据对接

> 对应 Story: US-AW-03

### Task 5.1: TaskDetailPanel 组件（mock 数据）

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T5.1 |
| **story_id** | US-AW-03 |
| **任务类型** | frontend |
| **文件** | `src/components/TaskDetailPanel.tsx` |
| **任务说明** | 1. 右侧抽屉/面板：从右侧滑出（300ms CSS transition），宽度 360px<br>2. Tab 切换：Overview / Task / Context / Logs<br>3. Overview Tab：任务状态（彩色标签）、优先级、分配 Agent（可点击跳转）、Worker 模型、Token 消耗、耗时（duration_ms）<br>4. Task Tab：任务描述、完成标准、当前输出内容（支持复制和展开/折叠）<br>5. Context Tab：预留，MVP 阶段显示 "上下文信息待实现"<br>6. Logs Tab：预留，显示该 Task 相关日志的缩略列表（点击跳转完整日志）<br>7. 先使用 mock 数据 |
| **完成标准** | 1. 面板从右侧滑出，300ms 动画<br>2. 默认显示 Overview Tab<br>3. 输出内容区域支持复制按钮<br>4. 代码块保留语法高亮<br>5. 组件测试覆盖 Tab 切换和字段展示 |
| **依赖任务** | AW-T3.1 |
| **推荐顺序** | 14 |

---

### Task 5.2: 对接真实 Workspace 状态数据（轮询）

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T5.2 |
| **story_id** | US-AW-02 / US-AW-03 / US-AW-04 |
| **任务类型** | frontend |
| **文件** | `src/hooks/useWorkspaceState.ts`、`src/api/workspace.ts` |
| **任务说明** | 1. 实现 `api.getWorkspaceState(goalId)` 封装 `GET /workspace/:goalId/state`<br>2. useWorkspaceState hook：每 2 秒轮询获取最新状态，支持增量对比（只更新变化的 Task/Agent/Worker，减少重渲染）<br>3. 状态数据驱动：TaskCard、AgentStationCard、WorkerBadge、TopStatusBar、TaskTree 全部基于同一数据源渲染<br>4. 点击 TaskCard 后调用 `GET /tasks/:taskId` 填充 TaskDetailPanel<br>5. 切换 Goal 时清空旧状态并重新加载<br>6. API 错误时显示降级提示 "状态同步失败，正在重试..." |
| **完成标准** | 1. 轮询间隔 2 秒，新状态自动更新 UI<br>2. Task 状态变化时 TaskCard 动画同步触发<br>3. 点击 TaskCard 后 TaskDetailPanel 显示真实数据（GET /tasks/:taskId）<br>4. WorkerBadge 模型名变化有平滑过渡<br>5. 断网/错误时有降级提示，恢复后自动刷新<br>6. 组件测试覆盖轮询逻辑 |
| **依赖任务** | AW-T2.3 / AW-T2.2 / AW-T4.1 / AW-T4.2 / AW-T4.3 / AW-T5.1 / AW-T3.3 |
| **推荐顺序** | 15 |

---

## Feature 6: 第三方模块前端集成

> 对应 Story: US-AW-05 / US-AW-06 / US-AW-07 / US-AW-08
> 说明：ExecutionLogPanel、HandoffStatusIndicator、RiskBadge、RoutingResultCard 的核心组件由对应模块独立开发，Workspace 只做集成挂载和参数传递。

### Task 6.1: ExecutionLogPanel 集成（Logs 模块组件）

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T6.1 |
| **story_id** | US-AW-05 |
| **任务类型** | frontend |
| **文件** | `src/pages/WorkspacePage.tsx` |
| **任务说明** | 1. 在 Workspace BottomConsole 中集成 Logs 模块的 ExecutionLogPanel 组件<br>2. 通过 props 传入当前 goal_id，让日志只筛选显示当前 Goal 的相关事件<br>3. BottomConsole 可展开/收起，收起时显示摘要条："运行中 · X 次模型调用 · Y 个 Task · Z 次 Handoff"<br>4. 摘要条数字从 ExecutionLogPanel 组件的统计回调获取，或基于当前状态计算<br>5. 展开/收起动画 300ms |
| **完成标准** | 1. ExecutionLogPanel 在 BottomConsole 中正确渲染<br>2. goal_id 正确传递，日志只显示当前 Goal<br>3. 收起状态摘要条数字正确<br>4. 展开/收起动画流畅<br>5. 错误日志自动展开功能正常工作 |
| **依赖任务** | AW-T3.1 / LO-T4.1（Logs 模块的 ExecutionLogPanel 组件需先完成） |
| **推荐顺序** | 16 |

---

### Task 6.2: HandoffStatusIndicator 集成（Handoff 模块组件）

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T6.2 |
| **story_id** | US-AW-06 |
| **任务类型** | frontend |
| **文件** | `src/components/TaskCard.tsx` |
| **任务说明** | 1. 在 TaskCard 中集成 Handoff 模块的 HandoffStatusIndicator 组件<br>2. 当 Task.status = handoff 时，在 TaskCard 底部渲染 HandoffStatusIndicator<br>3. 传入 handoff_id，Indicator 自动查询 Handoff 状态并展示进度条<br>4. Handoff 完成后 Indicator 3 秒后自动消失，TaskCard 状态恢复为 running（由接手 Agent 接管）<br>5. TaskCard 边框在 handoff 状态时变为紫色 |
| **完成标准** | 1. Task.status = handoff 时 HandoffStatusIndicator 可见<br>2. 进度条状态与 Handoff 后端状态同步<br>3. Handoff 完成后 Indicator 3 秒消失<br>4. TaskCard 边框在 handoff 时为紫色<br>5. 组件测试覆盖 |
| **依赖任务** | AW-T4.1 / HM-T5.1（Handoff 模块的 HandoffStatusIndicator 组件需先完成） |
| **推荐顺序** | 17 |

---

### Task 6.3: RiskBadge 集成（P1，Quota 模块组件）

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T6.3 |
| **story_id** | US-AW-07 |
| **任务类型** | frontend |
| **文件** | `src/components/WorkerBadge.tsx` |
| **任务说明** | 1. 在 WorkerBadge 中集成 Quota 模块的 RiskBadge 组件<br>2. RiskBadge 显示在 WorkerBadge 右上角（绝对定位，圆形或小型标签）<br>3. 传入当前 Worker 的 model_id，RiskBadge 自动查询并展示额度状态<br>4. 颜色映射：normal=绿色✓、warning=黄色⚠、near_limit=橙色🔴、limited=红色✗、cooldown=蓝色⏱、unknown=灰色?<br>5. 鼠标悬停显示 Tooltip：使用率、剩余额度、最近错误 |
| **完成标准** | 1. RiskBadge 显示在 WorkerBadge 右上角<br>2. 6 种状态颜色与 QuotaStatus 严格对应<br>3. Tooltip 显示 usage_percent 和 estimated_remaining<br>4. Quota 状态变化时 RiskBadge 同步更新（通过 Workspace 轮询或 Quota 模块自身轮询）<br>5. 组件测试覆盖 |
| **依赖任务** | AW-T4.2 / QM-T4.2（Quota 模块的 RiskBadge 组件需先完成） |
| **推荐顺序** | 18（P1，延后） |

---

### Task 6.4: RoutingResultCard 集成（P1，Router 模块组件）

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T6.4 |
| **story_id** | US-AW-08 |
| **任务类型** | frontend |
| **文件** | `src/pages/WorkspacePage.tsx` |
| **任务说明** | 1. 在 Workspace 中集成 Model Router 模块的 RoutingResultCard 组件<br>2. 当 Task 被分配给 Agent（Task.status 从 pending → assigned）时，自动弹出 RoutingResultCard<br>3. 弹出位置：对应 AgentStationCard 附近（不阻塞主流程）<br>4. 用户点击 [接受] 后卡片关闭，WorkerBadge 显示推荐模型<br>5. 用户点击 [切换模型] 后弹出 ModelOverrideModal（Router 模块组件）<br>6. 5 秒无操作后自动收起 |
| **完成标准** | 1. Task assigned 时自动弹出 RoutingResultCard<br>2. 卡片位置不遮挡主流程<br>3. [接受] 后卡片关闭，WorkerBadge 更新模型名<br>4. [切换模型] 弹出备用模型列表<br>5. 5 秒无操作自动收起<br>6. 组件测试覆盖 |
| **依赖任务** | AW-T4.2 / MR-T4.2（Router 模块的 RoutingResultCard 组件需先完成） |
| **推荐顺序** | 19（P1，延后） |

---

## Feature 7: 测试与质量保障

### Task 7.1: API 集成测试

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T7.1 |
| **story_id** | US-AW-01 / US-AW-02 / US-AW-03 / US-AW-04 |
| **任务类型** | test |
| **文件** | `tests/workspace.api.test.ts` |
| **任务说明** | 1. POST /goals — 正常/空标题/超长标题<br>2. POST /goals/:goalId/start — 正常/Goal不存在/非idle状态<br>3. GET /workspace/:goalId/state — 正常/Goal不存在/数据结构完整性<br>4. GET /tasks/:taskId — 正常/不存在/关联实体完整性 |
| **完成标准** | 1. 全部 4 个 API 的 happy path 和主要错误 path 都有测试<br>2. 每个 API 至少 3 个测试用例<br>3. 数据库状态在每次测试后正确清理<br>4. GET /workspace/:goalId/state 返回的结构与前端期望一致 |
| **依赖任务** | AW-T2.1 / AW-T2.2 / AW-T2.3 |
| **推荐顺序** | 20（与开发并行） |

---

### Task 7.2: 前端组件测试

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T7.2 |
| **story_id** | US-AW-01 / US-AW-02 / US-AW-03 / US-AW-04 |
| **任务类型** | test |
| **文件** | `tests/components/TaskCard.test.tsx`、`tests/components/AgentStationCard.test.tsx`、`tests/components/WorkerBadge.test.tsx`、`tests/components/TaskDetailPanel.test.tsx`、`tests/components/GoalInputPanel.test.tsx`、`tests/components/TaskTree.test.tsx` |
| **任务说明** | 1. TaskCard：5 种状态渲染、动画触发、点击事件<br>2. AgentStationCard：Agent 信息渲染、WorkerBadge 区域、边框颜色<br>3. WorkerBadge：状态灯颜色、breathe 动画、模型名切换<br>4. TaskDetailPanel：Tab 切换、字段展示、滑出动画<br>5. GoalInputPanel：禁用逻辑、提交、错误提示<br>6. TaskTree：树形渲染、状态图标、点击高亮 |
| **完成标准** | 1. 全部 6 个组件有独立测试文件<br>2. 每个组件覆盖主要渲染状态和用户交互<br>3. 快照测试覆盖关键 UI 状态 |
| **依赖任务** | AW-T4.1 / AW-T4.2 / AW-T4.3 / AW-T5.1 / AW-T3.2 |
| **推荐顺序** | 21（与开发并行） |

---

### Task 7.3: Workspace 端到端工作流测试

| 属性 | 值 |
|------|-----|
| **task_id** | AW-T7.3 |
| **story_id** | US-AW-01 / US-AW-02 / US-AW-03 / US-AW-04 / US-AW-05 / US-AW-06 |
| **任务类型** | test |
| **文件** | `tests/e2e/workspace.workflow.spec.ts` |
| **任务说明** | 1. 完整工作流：访问 Workspace → 输入 Goal → 点击开始 → 查看 Task 状态变化（pending → running → completed）→ 点击 Task 查看详情 → 查看 AgentStationBoard 状态 → 查看底部日志<br>2. 验证每一步的 UI 状态：TopStatusBar 标签、TaskCard 边框颜色、AgentStationCard WorkerBadge、TaskDetailPanel 内容<br>3. 验证 Handoff 场景：Task 进入 handoff 状态 → HandoffStatusIndicator 显示 → 接受后 WorkerBadge 切换 |
| **完成标准** | 1. 1 条完整 happy path E2E 测试通过<br>2. 1 条 Handoff 场景 E2E 测试通过<br>3. 1 条错误场景 E2E 测试通过（Task failed）<br>4. 每个 E2E 测试断言 ≥ 10 个检查点 |
| **依赖任务** | 全部 Feature（最后执行） |
| **推荐顺序** | 22 |

---

## 推荐开发顺序

```
Phase 1 — 数据模型 + 核心 API（1 周）
  AW-T1.1   创建 goals 表
  AW-T1.2   创建 tasks 表
  AW-T1.3   创建 worker_sessions 表
  AW-T1.4   定义状态枚举与流转规则
  AW-T2.1   POST /goals + POST /goals/:goalId/start
  AW-T2.2   GET /tasks/:taskId
  AW-T2.3   GET /workspace/:goalId/state
  AW-T7.1   API 集成测试（与开发并行）

Phase 2 — 前端页面框架 + 核心组件（1 周）
  AW-T3.1   Workspace 页面框架 + 三栏布局（mock）
  AW-T3.2   GoalInputPanel
  AW-T3.3   TopStatusBar
  AW-T4.1   TaskCard + 状态动画（mock）
  AW-T4.2   AgentStationCard + WorkerBadge（mock）
  AW-T4.3   TaskTree
  AW-T5.1   TaskDetailPanel（mock）
  AW-T7.2   前端组件测试（与开发并行）

Phase 3 — 真实数据对接 + 第三方集成（3-4 天）
  AW-T5.2   对接真实 Workspace 状态数据（轮询）
  AW-T6.1   ExecutionLogPanel 集成
  AW-T6.2   HandoffStatusIndicator 集成
  AW-T7.3   E2E 测试

Phase 4 — P1 集成（2 天，可选）
  AW-T6.3   RiskBadge 集成
  AW-T6.4   RoutingResultCard 集成
```

---

## 按 Phase 排期的任务看板

### Phase 1 — 数据模型 + 核心 API（1 周）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| AW-T1.1 | goals 表结构 | database | 无 | AW-01/02 |
| AW-T1.2 | tasks 表结构 | database | AW-T1.1 | AW-01/02/03 |
| AW-T1.3 | worker_sessions 表结构 | database | AW-T1.2 | AW-04 |
| AW-T1.4 | 状态枚举与流转规则 | backend | AW-T1.1/1.2/1.3 | AW-01/02/04 |
| AW-T2.1 | POST /goals + start | backend | AW-T1.4 | AW-01 |
| AW-T2.2 | GET /tasks/:taskId | backend | AW-T1.2/1.3 | AW-03 |
| AW-T2.3 | GET /workspace/:goalId/state | backend | AW-T1.4 | AW-02/04 |
| AW-T7.1 | API 集成测试 | test | AW-T2.x | AW-01~04 |

**Phase 1 交付物：** 完整的 Goal/Task/Worker 数据模型和 API，可通过 HTTP 工具创建 Goal、启动任务、查询 Workspace 聚合状态。

### Phase 2 — 前端页面框架 + 核心组件（1 周）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| AW-T3.1 | Workspace 页面框架（mock） | frontend | 无 | AW-01/02/04 |
| AW-T3.2 | GoalInputPanel | frontend | AW-T2.1 | AW-01 |
| AW-T3.3 | TopStatusBar | frontend | AW-T3.1 | AW-01/02 |
| AW-T4.1 | TaskCard + 动画（mock） | frontend | AW-T3.1 | AW-02 |
| AW-T4.2 | AgentStationCard + WorkerBadge（mock） | frontend | AW-T3.1 | AW-04 |
| AW-T4.3 | TaskTree | frontend | AW-T4.1 | AW-02 |
| AW-T5.1 | TaskDetailPanel（mock） | frontend | AW-T3.1 | AW-03 |
| AW-T7.2 | 前端组件测试 | test | AW-T3/4/5.x | AW-01~04 |

**Phase 2 交付物：** Workspace 页面可独立运行（mock 数据），包含完整的三栏布局、Goal 输入、Task 状态可视化、Agent 状态展示、Task 详情面板。

### Phase 3 — 真实数据对接 + 第三方集成（3-4 天）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| AW-T5.2 | 对接真实状态数据（轮询） | frontend | AW-T2.3/5.1/4.x | AW-02/03/04 |
| AW-T6.1 | ExecutionLogPanel 集成 | frontend | AW-T3.1/LO-T4.1 | AW-05 |
| AW-T6.2 | HandoffStatusIndicator 集成 | frontend | AW-T4.1/HM-T5.1 | AW-06 |
| AW-T7.3 | E2E 测试 | test | 全部 | AW-01~06 |

**Phase 3 交付物：** Workspace 连接真实后端数据，Task/Agent/Worker 状态实时同步，底部显示 Logs，Handoff 状态可视化。

### Phase 4 — P1 集成（2 天，可选）

| 任务 | 内容 | 类型 | 依赖 | 对应 Story |
|------|------|------|------|------------|
| AW-T6.3 | RiskBadge 集成 | frontend | AW-T4.2/QM-T4.2 | AW-07 |
| AW-T6.4 | RoutingResultCard 集成 | frontend | AW-T4.2/MR-T4.2 | AW-08 |

**Phase 4 交付物：** WorkerBadge 显示额度风险，Task 分配时弹出路由决策卡片。

---

## 风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| GET /workspace/:goalId/state 聚合查询慢 | Phase 3 轮询卡顿 | AW-T2.3 使用数据库索引优化，响应目标 < 100ms；MVP 阶段不引入缓存，后续如慢再加 Redis |
| Task/Agent/Worker 状态轮询造成前端频繁重渲染 | Phase 3 页面卡顿 | AW-T5.2 使用增量对比（shallowEqual），只更新变化的组件；React.memo 包裹 TaskCard/AgentStationCard |
| 第三方模块组件未就绪导致集成阻塞 | Phase 3 延迟 | AW-T6.1/6.2 先用占位组件（显示 "日志加载中" / "Handoff 状态待加载"），等对应模块就绪后替换 |
| WorkerBadge 模型名切换动画与状态变化不同步 | 视觉跳跃 | AW-T4.2 使用 CSS transition 监听 model_id 变化，不依赖 JS 动画；状态变化和模型名变化在同一轮渲染中完成 |
| TaskCard 动画性能问题（大量 Task 同时动画） | 页面卡顿 | AW-T4.1 动画仅使用 CSS（transform/opacity），不使用 JS 动画；will-change 属性仅在动画期间添加 |
| P1 集成功能（RiskBadge/RoutingResultCard）依赖其他模块 API | Phase 4 阻塞 | AW-T6.3/6.4 为 P1 功能，延后到对应模块完成后集成；Workspace 自身功能不受阻塞 |

---

## Story → Task 映射表

| Story | 涉及 Task | 是否完整覆盖 |
|-------|-----------|--------------|
| US-AW-01 输入 Goal 并启动任务 | AW-T1.1 / AW-T1.2 / AW-T1.4 / AW-T2.1 / AW-T3.1 / AW-T3.2 / AW-T3.3 | 是 |
| US-AW-02 实时观察 Task 状态变化 | AW-T1.1 / AW-T1.2 / AW-T1.3 / AW-T1.4 / AW-T2.3 / AW-T3.1 / AW-T3.3 / AW-T4.1 / AW-T4.3 / AW-T5.2 | 是 |
| US-AW-03 查看 Task 详情和输出 | AW-T1.2 / AW-T2.2 / AW-T3.1 / AW-T5.1 / AW-T5.2 | 是 |
| US-AW-04 查看 Agent Station 和 Worker 状态 | AW-T1.3 / AW-T1.4 / AW-T2.3 / AW-T3.1 / AW-T4.2 / AW-T5.2 | 是 |
| US-AW-05 查看执行日志 | AW-T3.1 / AW-T6.1 | 是 |
| US-AW-06 Handoff 状态可视化 | AW-T4.1 / AW-T6.2 | 是 |
| US-AW-07 额度风险徽章展示 | AW-T4.2 / AW-T6.3 | 是 |
| US-AW-08 模型路由决策展示 | AW-T4.2 / AW-T6.4 | 是 |

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
>
> 相关文档：
> - `docs/stories/agent-workspace-stories.md` — 用户故事来源
> - `docs/prd/agent-workspace-prd.md` — 产品需求
> - `docs/architecture/数据结构与数据库Schema.md` — Schema 定义
