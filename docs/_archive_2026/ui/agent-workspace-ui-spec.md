# Agent Workspace 前端页面设计方案

> 基于 `docs/prd/agent-workspace-prd.md`，面向 MVP-A 阶段的前端设计决策文档。
> 本文档只讨论设计（信息层级、布局、组件结构、交互状态），不包含代码实现。
>
> 设计时间：2026-06-25

---

## 1. Design Read

**Reading this as:** a developer productivity tool for AI-native engineers, with a calm / clarity-first language, leaning toward a Claude-inspired light neutral palette + restrained functional motion.

**关键信号：**
- **页面类型：** 复杂多面板工具界面（IDE-like workspace），不是 landing page。
- **风格词：** "低饱和、非深色、类 Claude" = 暖灰中性基底，充足留白，清晰层级，微妙分隔。
- **反 AI 味：** 不用紫/蓝渐变、不用发光效果、不用机器人 emoji、不用 "AI" 语言。
- **受众：** 多模型重度开发者，需要同时追踪多个 Agent / Task / Worker 的状态变化。
- **核心挑战：** 在一个页面里可视化 6+ 种实体（Goal, Task, Agent, Worker, Model, Handoff, Quota, Log）的状态流转，且不变成 "dashboard slop"。

---

## 2. 三表盘设定

| 表盘 | 数值 | 理由 |
|------|------|------|
| **DESIGN_VARIANCE** | 4 | 工具界面需要可预测的网格布局，但三栏比例（280 : flex : 360）和底部面板形成非对称节奏，避免 "三等分" 的呆板感。 |
| **MOTION_INTENSITY** | 3 | 状态变化需要被感知（呼吸灯、状态切换），但动效必须是功能性的 —— 引导注意力而非装饰。禁止无限循环的纯视觉动画。 |
| **VISUAL_DENSITY** | 6 | 这是一个状态密集的工具界面，需要同时展示 Agent Station、Task Card、Worker Badge、Log 等多种信息。密度高于普通 SaaS，但低于传统运维 dashboard。通过充足的 panel gutter（12px）和卡片内部 padding（16px）来控制压迫感。 |

---

## 3. 信息层级（Information Hierarchy）

Workspace 的信息结构是 "漏斗式" 的：全局状态在顶部，中间是核心工作区，底部是审计追踪，右侧是详情抽屉。

```
L0 ── 全局状态层（Global State）
       └─ TopStatusBar: Goal 状态、进度、统计、预警
       └─ QuotaAlertBanner: 额度预警（条件渲染，插入 TopStatusBar 下方）
       └─ ErrorBanner: 错误提示（条件渲染，悬浮或插入顶部）

L1 ── 主工作区层（Primary Workspace）
       ├─ Left Panel (280px): 控制与导航
       │   └─ GoalInputPanel
       │   └─ TaskTree
       ├─ Center Panel (flex): 核心观察区
       │   └─ AgentStationBoard (卡片网格)
       │       └─ AgentStationCard
       │           └─ WorkerBadge
       │           └─ TaskCard
       │           └─ HandoffStatusIndicator
       │       └─ RoutingResultCard (浮层)
       └─ Right Panel (360px, 可收起): 详情抽屉
           └─ TaskDetailPanel (Tab 切换)

L2 ── 审计追踪层（Audit Trail）
       └─ ExecutionLogPanel (底部，可收起/展开)
           └─ Tab: Event Log / Model Calls / Handoff Records / Error Logs

L3 ── 模态/浮层层（Transient Layer）
       └─ HandoffConfirmModal
       └─ ModelOverrideModal
       └─ LogDetailDrawer
       └─ HandoffCompareDrawer
```

**层级原则：**
- **L0 永远可见**，任何状态变化第一时间在全局层表达（用户不需要滚动或点击就能看到系统健康度）。
- **L1 是用户的注意力中心**，Agent Station Board 占据最大视觉面积。
- **L2 默认收起**，只露摘要条；出错时自动展开， push 内容向上。
- **L3 按需出现**，不阻塞主流程。

---

## 4. 布局方案（Layout Architecture）

### 4.1 整体布局

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Top Status Bar (56px)                                                        │
│ ┌─────────────────────────────────────────────────────────────────────────┐  │
│ │ Agent Workspace                                    [Settings] [Help]    │  │
│ ├─────────────────────────────────────────────────────────────────────────┤  │
│ │ Goal: Implement user auth system    [running ▶]  3/5  12.5kT  8m32s   │  │
│ └─────────────────────────────────────────────────────────────────────────┘  │
├───────────────┬──────────────────────────────┬───────────────────────────────┤
│               │                              │                               │
│ Left Panel    │   Center Panel               │  Right Panel (collapsible)    │
│ (280px fixed) │   (flex, min 560px)          │  (360px fixed, 可收至 48px)   │
│               │                              │                               │
│ GoalInput     │   AgentStationBoard          │  TaskDetailPanel              │
│ ┌───────────┐ │   ┌──────┐ ┌──────┐ ┌────┐ │  ┌─────────────────────────┐  │
│ │ Describe  │ │   │Agent1│ │Agent2│ │A3  │ │  │ Overview | Task | Logs  │  │
│ │ your goal │ │   │[Task]│ │[Task│ │[T] │ │  │                         │  │
│ │ ...       │ │   └──────┘ └──────┘ └────┘ │  │ Selected entity details │  │
│ │           │ │   ┌──────┐ ┌──────────────┐ │  │                         │  │
│ │ [Start]   │ │   │Agent4│ │Agent5        │ │  │                         │  │
│ └───────────┘ │   └──────┘ └──────────────┘ │  └─────────────────────────┘  │
│               │                              │                               │
│ TaskTree      │                              │                               │
│ ┌───────────┐ │                              │                               │
│ │ Goal      │ │                              │                               │
│ │  Task 1   │ │                              │                               │
│ │  Task 2   │ │                              │                               │
│ └───────────┘ │                              │                               │
│               │                              │                               │
├───────────────┴──────────────────────────────┴───────────────────────────────┤
│ ExecutionLogPanel (40px collapsed / 280px expanded)                          │
│ ┌──────────────────────────────────────────────────────────────────────────┐ │
│ │ Running · 12 calls · 5 tasks · 1 handoff · 0 errors          [Expand ▲]  │ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 布局参数

| 区域 | 宽度 | 高度 | 行为 |
|------|------|------|------|
| TopStatusBar | 100% | 56px | 固定顶部，不滚动 |
| QuotaAlertBanner | 100% | auto (max 48px) | 条件渲染，push 内容向下 |
| Left Panel | 280px | calc(100vh - 56px - 40px) | 固定左侧，独立滚动 |
| Center Panel | flex: 1 | 同上 | 主滚动区 |
| Right Panel | 360px (展开) / 48px (收起) | 同上 | 可收起为图标栏，点击展开 |
| Bottom Panel | 100% | 40px (收起) / 280px (展开) | 可拖拽调整高度 |

### 4.3 响应式策略

| 断点 | 布局变化 |
|------|---------|
| >= 1440px | 完整三栏布局，所有面板展开 |
| 1024px - 1439px | Left Panel 可收至 48px（只显示图标 + TaskTree 缩略），Right Panel 默认收起 |
| < 1024px | 单栏布局，Left/Right 变为底部 Tab 或全屏抽屉，Center 占据全部宽度 |

> MVP-A 阶段优先实现 >= 1280px 的桌面布局，移动端适配标记为 P1。

---

## 5. 组件结构设计

### 5.1 组件树（Component Tree）

```
WorkspacePage
├── TopStatusBar
│   ├── WorkspaceTitle
│   ├── GoalStatusBadge
│   ├── ProgressIndicator
│   ├── StatsRow (Token / Handoff / Duration)
│   └── GlobalActions
├── QuotaAlertBanner (conditional)
│   ├── AlertIcon
│   ├── AlertMessage
│   └── AlertActions
├── ErrorBanner (conditional)
│   ├── ErrorIcon
│   ├── ErrorMessage
│   └── ErrorActions
├── MainLayout (3-column grid)
│   ├── LeftPanel
│   │   ├── GoalInputPanel
│   │   │   ├── GoalTextarea
│   │   │   ├── RunConfigToggle
│   │   │   └── StartButton
│   │   └── TaskTree
│   │       ├── GoalNode
│   │       └── TaskNode (recursive, for future subtasks)
│   ├── CenterPanel
│   │   └── AgentStationBoard
│   │       ├── AgentStationCard (grid item)
│   │       │   ├── AgentHeader (name + role tag)
│   │       │   ├── WorkerBadge
│   │       │   │   ├── ModelName
│   │       │   │   ├── StatusDot
│   │       │   │   ├── RiskBadge
│   │       │   │   └── RoutingConfidenceBadge
│   │       │   └── TaskCardSlot
│   │       │       └── TaskCard (or EmptyState)
│   │       │           ├── TaskHeader (status icon + title)
│   │       │           ├── TaskMeta (agent, worker, tokens)
│   │       │           ├── ProgressBar (conditional)
│   │       │           ├── OutputSnippet (conditional)
│   │       │           └── HandoffStatusIndicator (conditional)
│   │       └── FloatingOverlay
│   │           ├── RoutingResultCard
│   │           └── HandoffCompareDrawer
│   └── RightPanel
│       └── TaskDetailPanel
│           ├── PanelHeader (entity type + name + close)
│           ├── TabNav (Overview | Task | Context | Logs | Handoff | Quota | Router)
│           └── TabContent
│               ├── OverviewTab
│               ├── TaskTab
│               ├── ContextTab
│               ├── LogsTab
│               ├── HandoffTab
│               ├── QuotaTab
│               └── RouterTab
└── BottomPanel
    └── ExecutionLogPanel
        ├── CollapsedBar (summary + expand button)
        └── ExpandedContent
            ├── LogTabNav
            ├── LogFilterBar
            ├── LogList
            │   └── LogRow
            └── LogDetailDrawer (inline or overlay)
```

### 5.2 关键组件设计决策

#### AgentStationCard — 状态表达的容器

每个 Agent Station 是一个独立的 "工位卡片"，内部包含 WorkerBadge 和 TaskCard。

**卡片结构（从上到下）：**
1. **Agent Header** — 名称 + 角色标签（Planner/Coder/Reviewer 等），一行
2. **Worker Badge** — 模型名 + 状态灯 + RiskBadge，紧凑的一行
3. **Task Card Slot** — 当前 Task 的卡片，或空闲时的占位符
4. **History Footer** — 历史任务统计（小字，去强调）

**卡片尺寸：**
- 最小宽度：280px
-  padding：16px
-  gap（内部元素间距）：12px
-  圆角：12px
-  边框：1px solid，颜色随 AgentStatus 变化

#### TaskCard — 状态可视化的核心

TaskCard 是用户最频繁注视的组件，其视觉表达必须一目了然。

**结构层次（从上到下）：**
1. **Header Row** — 状态图标 + Task 标题 + 优先级标记
2. **Meta Row** — Agent 名 / Worker 模型名 / RiskBadge / Confidence（一行，小字）
3. **Progress Row** — 进度条（仅 running / assigned 状态显示）
4. **Output Row** — 最新输出片段（仅 running 状态显示，最大 3 行，截断）
5. **Stats Row** — Token / Duration / Step 计数（一行，小字，去强调）
6. **Action Row** — 操作按钮（仅 failed / handoff 状态显示）

**尺寸：**
- 宽度：填满 AgentStationCard 内部宽度
- padding：12px
- 圆角：8px（小于外层卡片，形成嵌套层级）

#### WorkerBadge — 模型实例的快照

WorkerBadge 是模型状态的 "身份证"，需要在极小空间内传达模型名、执行状态、额度健康度、路由决策质量四个维度的信息。

**结构（从左到右，单行）：**
1. **Status Dot** — 8px 圆形状态灯，颜色 + 动画表达 WorkerStatus
2. **Model Name** — 模型显示名（如 "GPT-4o"），主体文字
3. **Risk Badge** — 圆角小标签，颜色表达 QuotaStatus
4. **Confidence Badge** — 可选，数字或进度条微缩版

> 设计上 RiskBadge 用颜色而非图标来传达状态，减少视觉噪音。Tooltip 承载详细信息。

#### ExecutionLogPanel — 审计追踪的底线

日志面板是用户排查问题的最后防线，其设计目标是 "在需要时立刻找到关键信息"。

**收起状态（Collapsed Bar）：**
- 单行高度：40px
- 左对齐摘要文本，右对齐展开按钮
- 摘要有颜色编码：Running（灰）、Calls（蓝）、Tasks（紫）、Handoffs（橙）、Errors（红）

**展开状态：**
- Tab 切换：Event Log（默认）/ Model Calls / Handoff Records / Error Logs / Token Summary
- 日志列表：每行固定高度 36px，时间戳 + 图标 + 类型 + Agent + Model + Task + 摘要
- 筛选栏：类型多选 + 关键词搜索 + 时间范围

---

## 6. 视觉设计系统建议

### 6.1 颜色系统（低饱和、非深色）

**中性基底（Neutrals）：**
| Token | 色值建议 | 用途 |
|-------|---------|------|
| surface-bg | #fafaf9 (warm gray-50) | 页面背景 |
| panel-bg | #ffffff | 面板背景 |
| card-bg | #ffffff | 卡片背景 |
| border-default | #e7e5e4 (warm gray-200) | 默认边框 |
| border-strong | #d6d3d1 (warm gray-300) | 强调边框 |
| text-primary | #292524 (warm gray-800) | 主文本 |
| text-secondary | #78716c (warm gray-500) | 次要文本 |
| text-tertiary | #a8a29e (warm gray-400) | 占位文本、禁用态 |

> 使用 warm gray（Stone）而非 cool gray（Slate/Zinc），营造更柔和、更人文的工具感，避免 "工业冷感"。

**功能色（全部去饱和，避免 AI 味）：**

| 语义 | 色值建议 | 用途 |
|------|---------|------|
| running | #57534e (warm gray-600) 或 #6366f1 极低饱和版 | running 状态边框、呼吸动画 |
| completed | #78716c (warm gray-500) 或 #6b8e6b (sage) | completed 状态边框、成功提示 |
| failed | #b4534a (muted terracotta) | failed 状态边框、错误提示 |
| handoff | #78716c (warm gray-500) 或 #7c6fae (muted lavender) | handoff 状态边框 |
| warning | #b0895a (muted amber) | 预警条、warning badge |
| near-limit | #c4784a (muted rust) | near_limit 预警 |
| limited | #b4534a (muted terracotta) | limited 告警 |
| info | #6b7280 (gray-500) | 信息提示 |

> **关键决策：** 不用亮蓝色（#3b82f6）作为 running 色，不用亮绿色（#22c55e）作为 completed 色，不用亮紫色（#9333ea）作为 handoff 色。所有功能色都从 warm gray 向目标色相偏移 10-20%，保持低饱和度。

**状态色映射表：**

| 状态 | 边框色 | 背景色 | 文字色 | 动画 |
|------|--------|--------|--------|------|
| idle / pending | border-default | surface-bg | text-secondary | 无 |
| assigned | border-strong | surface-bg | text-secondary | 无 |
| running | running | #f5f5f4 (warm gray-100) | text-primary | 呼吸阴影（见 7.2） |
| waiting | warning | #faf6f0 (muted amber-50) | text-primary | 无 |
| handoff | handoff | #f3f1f8 (muted lavender-50) | text-primary | 边框颜色渐变循环 |
| completed | completed | #f2f5f2 (sage-50) | text-primary | 无 |
| failed | failed | #faf3f2 (terracotta-50) | text-primary | 微抖动（单次） |

### 6.2 排版系统

| 层级 | 字号 | 字重 | 用途 |
|------|------|------|------|
| Display | 18px | 600 | Agent Station 名称、Goal 标题 |
| Heading | 14px | 600 | Task 标题、Panel 标题 |
| Body | 13px | 400 | 正文、日志摘要 |
| Caption | 12px | 400 | 元数据（Token、时间、统计） |
| Micro | 11px | 500 | 标签、Badge 文字、状态灯旁文字 |

> 全系统只使用一个无衬线字体栈。MVP 阶段用系统默认无衬线即可（-apple-system, BlinkMacSystemFont, "Segoe UI"）。不需要引入外部字体。

### 6.3 圆角与形状系统

| 元素 | 圆角 | 理由 |
|------|------|------|
| 页面级 Panel | 0 | 面板贴边，形成干净的框架 |
| AgentStationCard | 12px | 主要容器，温和的圆角 |
| TaskCard | 8px | 嵌套卡片，圆角略小以形成层级 |
| Badge / Tag | 999px (pill) | 标签语义，圆润友好 |
| Button | 8px | 与卡片一致，形成体系 |
| Input / Textarea | 8px | 与按钮一致 |
| Status Dot | 999px | 圆形状态灯 |
| Progress Bar | 999px | 与 pill 标签呼应 |

> **形状一致性：** 整个页面只用两套圆角 —— 8px（卡片、按钮、输入框）和 999px（标签、状态灯、进度条）。不出现 4px、16px、24px 等其他圆角值。

### 6.4 阴影系统

| 场景 | 阴影 | 理由 |
|------|------|------|
| 默认卡片 | 无 | 用边框和背景色区分层级，不用阴影 |
| running TaskCard | `0 0 0 1px running-color` + `0 0 12px rgba(0,0,0,0.04)` | 微弱的内发光感，由边框 + 极淡阴影模拟 |
| 悬浮卡片（hover） | `0 2px 8px rgba(0,0,0,0.06)` | 极淡的上浮感 |
| 选中卡片 | `0 0 0 2px running-color` | 聚焦环 |
| 浮层（RoutingResultCard） | `0 8px 32px rgba(0,0,0,0.08)` | 明显上浮，与背景分离 |
| 模态框 backdrop | `rgba(0,0,0,0.2)` | 轻量遮罩 |

> **无弥散阴影：** 不使用大范围的弥散阴影（如 `0 20px 60px`），保持界面的 "平面感" 和 "清晰度"。阴影只用 tint 到背景色的极淡灰色。

---

## 7. 状态与交互设计

### 7.1 状态流转的联动规则

Workspace 的核心设计挑战是：一个后端状态变化，需要在前端多个组件上同步反映。以下是关键联动矩阵：

| 源状态变化 | 受影响的组件 | 视觉表达 |
|-----------|------------|---------|
| Goal: idle -> planning | TopStatusBar, GoalInputPanel | 状态标签变 planning 色，输入框显示 planning 动画 |
| Goal: planning -> running | TopStatusBar, TaskTree | 状态标签变 running 色，TaskTree 节点从 pending 变为 assigned |
| Task: pending -> assigned | TaskTree, AgentStationCard, TaskCard | TaskTree 图标变 assigned；AgentStationCard 边框变 assigned 色；TaskCard 出现 |
| Task: assigned -> running | TaskTree, TaskCard, WorkerBadge | TaskTree 图标变 running；TaskCard 边框变 running 色 + 呼吸动画；WorkerBadge 状态灯变 running |
| Task: running -> completed | TaskTree, TaskCard, WorkerBadge | TaskTree 图标变 completed；TaskCard 边框变 completed 色；WorkerBadge 状态灯变 done |
| Task: running -> handoff | TaskTree, TaskCard, HandoffStatusIndicator | TaskTree 图标变 handoff；TaskCard 边框变 handoff 色 + 边框循环动画；HandoffStatusIndicator 出现 |
| Task: handoff -> running | TaskCard, WorkerBadge, HandoffStatusIndicator | TaskCard 边框变 running；WorkerBadge 模型名切换（带过渡动画）；HandoffStatusIndicator 显示 completed 后 3s 消失 |
| Task: running -> failed | TaskTree, TaskCard, WorkerBadge, ErrorBanner, ExecutionLogPanel | TaskTree 图标变 failed；TaskCard 边框变 failed 色 + 单次抖动；WorkerBadge 状态灯变 failed + 闪烁；ErrorBanner 弹出；ExecutionLogPanel 自动展开 |
| Quota: normal -> warning | RiskBadge, QuotaAlertBanner | RiskBadge 颜色变 warning；QuotaAlertBanner 弹出黄色预警条 |
| Quota: warning -> limited | RiskBadge, QuotaAlertBanner, TaskCard | RiskBadge 颜色变 limited；QuotaAlertBanner 变红色告警条；TaskCard 显示 Handoff 建议 |
| Model Router 决策 | RoutingResultCard | RoutingResultCard 在对应 AgentStationCard 附近弹出 |
| 新日志产生 | ExecutionLogPanel | 新日志行高亮 2s 后恢复正常；如果是 error 类型，自动展开面板 |

### 7.2 动画规范

**呼吸动画（running 状态）：**
```
box-shadow: 0 0 0 0px rgba(running-color, 0.15)
  -> 0 0 0 4px rgba(running-color, 0.05)
  -> 0 0 0 0px rgba(running-color, 0.15)
duration: 2.5s, ease: ease-in-out, iteration: infinite
```
> 非常克制：只有 4px 的扩散范围，透明度从 0.15 降到 0.05。用户能在 peripheral vision 中感知到 "有东西在运行"，但不会吸引主动注意力。

**边框颜色循环（handoff 状态）：**
```
border-color: rgba(handoff-color, 0.4)
  -> rgba(handoff-color, 1.0)
  -> rgba(handoff-color, 0.4)
duration: 1.5s, ease: linear, iteration: infinite
```

**单次抖动（failed 状态）：**
```
transform: translateX(0) -> translateX(-4px) -> translateX(4px) -> translateX(-2px) -> translateX(0)
duration: 0.3s, ease: ease-out, iteration: 1
```
> 只做一次，不循环。循环抖动会让人焦虑。

**WorkerBadge 模型切换：**
```
opacity: 1 -> 0 (150ms) -> 模型名更新 -> opacity: 0 -> 1 (150ms)
```
> 淡入淡出，不是滑动。滑动会产生 "位置变化" 的错觉，而这里只是 "替换内容"。

**新日志高亮：**
```
background-color: rgba(running-color, 0.06)
  -> transparent
duration: 2s, ease: ease-out, delay: 0
```
> 2s 后自动消退，不干扰用户阅读后续日志。

**面板展开/收起：**
```
height: 40px -> 280px (ExecutionLogPanel)
width: 48px -> 360px (RightPanel)
duration: 250ms, ease: cubic-bezier(0.16, 1, 0.3, 1)
```
> 使用 ease-out-cubic，开始快结束慢，给人 "顺滑展开" 的感觉。

**所有状态切换的通用过渡：**
```
border-color, background-color, box-shadow, color: 250ms ease
transform, opacity: 200ms ease
```

### 7.3 交互模式

**轮询与实时更新：**
- MVP-A 阶段使用 2s 轮询。
- 前端做增量对比（shallowEqual），只更新变化的组件。
- 状态变化时触发动画，而非整页重绘。

**选中机制：**
- 点击 TaskCard -> TaskDetailPanel 展开/更新，TaskCard 显示选中边框（2px focus ring）。
- 点击 AgentStationCard -> TaskDetailPanel 显示 Agent 详情。
- 点击 TaskTree 中的节点 -> 中间区域滚动到对应 TaskCard 并高亮。
- 点击 ExecutionLogPanel 中的 Task/Agent ID -> 高亮对应组件。

**浮层行为（RoutingResultCard）：**
- 弹出位置：对应 AgentStationCard 内部或附近，不遮挡其他 Agent。
- 自动收起：5s 无操作后淡出（用户 hover 时重置计时器）。
- 手动关闭：点击 X 按钮立即消失。

**错误响应：**
- error 日志产生时，ExecutionLogPanel 从收起状态自动展开（250ms 动画）。
- Error Banner 从顶部滑入，提供操作建议（Retry / Handoff / 查看日志）。
- 用户点击 "忽略" 后，Banner 滑出，面板保持展开状态。

---

## 8. 反 AI 味的具体设计决策

以下决策直接服务于 "避免 AI 味太重" 的目标：

### 8.1 颜色：拒绝 "AI 紫" 和 "科技蓝"

- **不用任何紫色作为主色。** handoff 状态用 muted lavender（#7c6fae 的去饱和版）而非鲜艳的 purple。
- **不用亮蓝色作为 running 色。** running 状态用 warm gray-600（#57534e）或极低饱和的 indigo，而不是 #3b82f6。
- **不用渐变。** 所有背景都是纯色。不用任何 gradient（包括所谓的 "柔和渐变"）。
- **不用发光效果（glow）。** 呼吸动画用 box-shadow 模拟，但扩散范围不超过 4px，透明度不超过 0.15。

### 8.2 图标：拒绝机器人 emoji

- **不用 "🤖"、"🧠"、"✨" 等 emoji。** 全部使用图标库（Phosphor / Radix）中的线条图标。
- **模型图标用抽象几何形状。** 不用机器人的具象图标。例如：模型用 `Cube` 或 `Hexagon`，Agent 用 `UserCircle` 或 `Briefcase`。
- **状态图标用简洁的符号：**
  - pending: `Pause` 或 `Circle`
  - running: `Play` 或 `Spinner`（线条旋转，不是实心 spinner）
  - completed: `Check`
  - failed: `X`
  - handoff: `ArrowsLeftRight`

### 8.3 语言：拒绝 AI 营销话术

- **不用 "AI Agent"、"AI Powered"、"Smart"、"Intelligent" 等词汇。** 界面中只出现 "Agent"、"Model"、"Worker"、"Task" 等功能性词汇。
- **按钮标签用动词短语：** "Start"、"Handoff"、"Retry"、"Accept"、"Override"。不用 "Let AI do it"、"Smart Retry"。
- **空状态用功能性描述：** "No active tasks" 而非 "Your AI is waiting"。

### 8.4 布局：拒绝 "AI Dashboard" 模式

- **不用深色模式作为默认。** 浅色暖灰是默认，深色只在系统偏好时切换。
- **不用三栏等宽布局。** 左 280 / 中 flex / 右 360 的非对称比例避免 "dashboard 感"。
- **不用数据表格展示 Agent 列表。** Agent 用卡片网格，每个卡片有明确的视觉边界和内容层级。
- **不用 KPI 数字大屏。** Token、Handoff、Duration 等统计数字用小字放在 TopStatusBar 中，不是巨大的 display numbers。

---

## 9. 空状态与加载状态

### 9.1 空状态（Empty States）

| 场景 | 空状态设计 |
|------|-----------|
| 无 Goal | GoalInputPanel 显示占位提示 "Describe what you want to build..."，Start 按钮禁用 |
| 无 Task | TaskTree 显示 "Tasks will appear after Planner finishes" |
| Agent 空闲 | AgentStationCard 的 TaskCard Slot 显示 "No active task"（小字，去强调） |
| 无日志 | ExecutionLogPanel 展开后显示 "Logs will appear when execution starts" |
| TaskDetailPanel 未选中 | 显示 "Select a task or agent to view details" |

### 9.2 加载状态（Loading States）

| 场景 | 加载设计 |
|------|---------|
| Goal planning | GoalInputPanel 中显示简洁的 indeterminate progress bar（2px 高度，running 色），按钮变为 "Planning..." 禁用态 |
| TaskCard 等待输出 | Output Row 显示闪烁的 cursor（`_`）或 "Generating..." |
| Handoff Summary 生成 | HandoffStatusIndicator 中显示 "Generating summary..." + 极细的 indeterminate progress bar |
| 日志加载 | LogList 顶部显示 2px indeterminate progress bar |
| 面板数据加载 | 使用 skeleton placeholder，形状匹配最终内容（不是通用的 spinner） |

---

## 10. 与 PRD 的对照检查

| PRD 要求 | 设计方案覆盖 | 备注 |
|---------|------------|------|
| 顶部状态栏 | 5.1, 7.1 | 56px 固定高度，包含 Goal 状态、进度、统计 |
| 左侧 Goal 输入 | 5.1, 4.1 | 280px 固定面板，包含输入框 + TaskTree |
| 中间 Agent 工位/任务卡片 | 5.1, 4.1 | 弹性宽度，AgentStationCard 网格 |
| 右侧任务详情 | 5.1, 4.1 | 360px 可收起面板，Tab 切换 |
| 底部执行日志 | 5.1, 4.1 | 40px/280px 可展开面板 |
| TaskCard 5 种状态动画 | 6.1, 7.2 | pending/running/handoff/completed/failed 全部有颜色和动画 |
| WorkerBadge 状态灯 | 5.2 | 8px 状态灯 + 颜色 + 动画 |
| RiskBadge 6 种状态 | 6.1 | 去饱和的功能色 |
| HandoffStatusIndicator | 5.2 | 进度条 + 状态图标 + 动画 |
| RoutingResultCard | 5.2 | 浮层，置信度条 + 评分拆解 |
| Quota 预警条 | 5.1 | 顶部条件渲染 Banner |
| 状态联动矩阵 | 7.1 | 完整联动规则 |
| 响应式策略 | 4.3 | 三档断点 |

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
>
> 相关文档：
> - `docs/prd/agent-workspace-prd.md` — 产品需求来源
> - `docs/tasks/agent-workspace-tasks.md` — 开发任务拆解
