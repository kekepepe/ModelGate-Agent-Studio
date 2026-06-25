# Logs / Observability UI 设计规范

> 版本：v1.0
> 更新日期：2026-06-25
> 关联文档：
> - `docs/prd/logs-observability-prd.md`
> - `docs/stories/logs-observability-stories.md`
> - `docs/tasks/logs-observability-tasks.md`
> - `docs/design/agent-workspace-frontend-design.md`

---

## 1. 设计概述

### 1.1 Design Read

Reading this as: developer observability tool for technical users debugging multi-agent execution, with a structured-data / devtool language, leaning toward high-density table + timeline layouts with warm neutral surfaces.

### 1.2 三拨盘

| 拨盘 | 值 | 理由 |
|------|-----|------|
| DESIGN_VARIANCE | 4 | 以对称表格布局为主，时间线视图允许适度非对称；开发者工具优先可预测性 |
| MOTION_INTENSITY | 3 | 仅保留功能性动画：新日志高亮、抽屉滑入、状态脉冲；不引入装饰性动效 |
| VISUAL_DENSITY | 8 | 日志查看器属于高密度数据工具，需要紧凑行高、多列信息、最小留白 |

### 1.3 核心设计原则

1. **结构化数据优先**：日志是结构化执行档案，不是聊天记录。每行日志必须以表格形式呈现可扫描字段（时间、类型、状态、Agent、Model、摘要）。
2. **一眼定位异常**：错误行必须在列表中立即跳出（红色背景行 + 状态图标），不需要用户逐行阅读。
3. **时间即主线**：Task Timeline 必须让用户在 5 秒内理解"谁先做了什么、何时失败、何时交接"。
4. **筛选即查询**：筛选栏是开发者的工作台，必须支持快速组合条件并实时反馈结果数量。
5. **上下文不丢失**：从日志列表 → 详情抽屉 → Task 时间线 → Handoff 对比，任意节点都能跳转回相关实体。

---

## 2. 信息架构

### 2.1 页面路由

| 路由 | 视图 | 说明 |
|------|------|------|
| `/logs` | LogStreamView（默认） | 日志列表 + 筛选 + 详情抽屉 |
| `/logs?task=xxx` | TaskTimelineView | 指定 Task 的时间线视图 |
| `/logs?tab=errors` | ErrorPanelView | 错误集中展示 |
| `/logs?tab=tokens` | TokenUsageView | Token 统计（P1） |

### 2.2 LogsPage 组件树

```
LogsPage
├── PageHeader
│   ├── Title "Execution Logs"
│   └── ExportButton
├── FilterBar (sticky, z-10)
│   ├── EntityFilterGroup
│   │   ├── GoalDropdown
│   │   ├── TaskDropdown
│   │   ├── AgentDropdown
│   │   └── ModelDropdown
│   ├── EventFilterGroup
│   │   ├── EventTypeDropdown (multi)
│   │   ├── StatusDropdown (multi)
│   │   └── TimeRangePicker
│   └── SearchInput
├── QuickFilterTags
│   └── Tag[]
├── ViewSwitcher
│   └── Tab[]: [日志流] [时间线] [错误] [Token]
├── ViewContent
│   ├── LogStreamView
│   │   └── LogListTable
│   │       ├── TableHeader (7 columns)
│   │       └── LogRow[]
│   │           └── Click → LogDetailDrawer
│   ├── TaskTimelineView
│   │   ├── TimelineHeader
│   │   ├── TimelineGraph
│   │   │   └── TimelineNode[]
│   │   └── TimelineSummaryBar
│   ├── ErrorPanelView
│   │   ├── ErrorStatsCards
│   │   └── ErrorLogList
│   └── TokenUsageView (P1)
│       ├── AgentTokenChart
│       ├── ModelTokenChart
│       └── SummaryStats
├── LogDetailDrawer (520px, 右侧滑出)
│   ├── DrawerHeader
│   ├── MetadataGrid
│   ├── TokenUsageSection
│   ├── ContentSection
│   ├── ErrorSection
│   └── MetadataSection
└── PaginationBar
```

### 2.3 视图切换逻辑

- **默认进入**：LogStreamView（日志列表）。
- **点击 Task 列的 [时间线] 链接**：平滑切换为 TaskTimelineView，URL 更新为 `/logs?task=xxx`，显示"返回列表"按钮。
- **点击快速筛选 [仅错误]**：保持 LogStreamView，但自动激活 ErrorPanel Tab 或高亮错误统计。
- **点击 Handoff 日志的 [对比] 按钮**：在 Drawer 内或 Modal 中打开 HandoffCompareView（左右分栏对比）。

---

## 3. 设计系统

### 3.1 颜色系统

沿用全局 Stone 中性色，扩展 10 种事件类型专用低饱和度色板。

#### 3.1.1 中性色（与全局一致）

| Token | 色值 | 用途 |
|-------|------|------|
| surface | #fafaf9 (Stone-50) | 页面主背景 |
| surface-elevated | #ffffff | 抽屉、卡片、下拉面板 |
| surface-hover | #f5f5f4 (Stone-100) | 表格行悬停 |
| border | #e7e5e4 (Stone-200) | 分割线、表头下边框 |
| border-strong | #d6d3d1 (Stone-300) | 抽屉边框、卡片边框 |
| text-primary | #1c1917 (Stone-900) | 主标题、表格正文 |
| text-secondary | #78716c (Stone-500) | 次要信息、占位符 |
| text-muted | #a8a29e (Stone-400) | 时间戳、禁用态 |

#### 3.1.2 事件类型色板（全部低饱和）

每种事件类型使用 `bg-{color}-50` + `text-{color}-800` + `border-{color}-200` 三元组。

| 事件类型 | 背景 | 文字 | 边框 | 节点圆点 |
|----------|------|------|------|----------|
| model_call | #e0e7ff (Indigo-50) | #3730a3 (Indigo-800) | #c7d2fe | #4f46e5 |
| agent_step | #f0fdfa (Teal-50) | #115e59 (Teal-800) | #99f6e4 | #0d9488 |
| tool_call | #fefce8 (Yellow-50) | #854d0e (Yellow-800) | #fef08a | #ca8a04 |
| task_status_change | #f5f5f4 (Stone-100) | #44403c (Stone-700) | #d6d3d1 | #78716c |
| quota_status_change | #fff7ed (Orange-50) | #9a3412 (Orange-800) | #fed7aa | #ea580c |
| handoff_* | #ede9fe (Violet-50) | #5b4ba4 (Violet-Custom) | #ddd6fe | #7c3aed |
| error | #fff1f2 (Rose-50) | #9f1239 (Rose-800) | #fecdd3 | #e11d48 |
| supervisor_review | #faf5ff (Purple-50) | #6b21a8 (Purple-800) | #e9d5ff | #9333ea |
| memory_write_candidate | #f0fdf4 (Emerald-50) | #166534 (Emerald-800) | #bbf7d0 | #16a34a |

> 注意：handoff 系列沿用 Handoff Manager 的 lavender 色值（#ede9fe / #5b4ba4），确保跨模块一致性。全局禁用高饱和 #9333ea 作为默认紫色。

#### 3.1.3 状态语义色

| 状态 | 图标 | 颜色 |
|------|------|------|
| success / completed / approved / accepted | CheckCircle | #15803d (Green-700) |
| failed / error / rejected / timeout | XCircle | #be123c (Rose-700) |
| started / running / pending | Dot (脉冲) | #2563eb (Blue-600) |
| transition / created / detected / skipped | Dot / ArrowRight | #78716c (Stone-500) |
| needs_revision | AlertCircle | #b45309 (Amber-700) |

#### 3.1.4 行级高亮色

| 场景 | 背景色 | 文字色 |
|------|--------|--------|
| 错误日志行 | #fff1f2 (Rose-50) | #9f1239 |
| 新日志高亮（2s 内） | #fefce8 (Yellow-50) | 继承 |
| Handoff 日志行 | #ede9fe (Violet-50) | #5b4ba4 |

### 3.2 字体规范

| 用途 | 字体 | 大小 | 字重 | 行高 | 字间距 |
|------|------|------|------|------|--------|
| 页面标题 | Geist | 20px | 600 | 1.3 | -0.01em |
| 筛选标签 | Geist | 13px | 500 | 1.4 | 0 |
| 表头文字 | Geist | 12px | 500 | 1.4 | 0.02em |
| 表格正文 | Geist | 13px | 400 | 1.5 | 0 |
| 时间戳 / Token 数 / 代码 | Geist Mono | 12px | 400 | 1.4 | 0 |
| 摘要文字 | Geist | 13px | 400 | 1.5 | 0 |
| 抽屉标题 | Geist | 16px | 600 | 1.3 | -0.01em |
| 元数据标签 | Geist | 11px | 500 | 1.4 | 0.04em |

### 3.3 间距与尺寸

| 元素 | 尺寸 |
|------|------|
| FilterBar 高度 | 48px |
| FilterBar padding | 12px 20px |
| QuickFilterTags padding | 8px 20px |
| 表格行高 | 40px |
| 表格 cell padding | 8px 12px |
| 表头行高 | 36px |
| 抽屉宽度 | 520px |
| 抽屉 padding | 20px |
| Timeline 节点圆点 | 10px |
| Timeline 连线宽度 | 1px |
| Timeline 节点间距 | 24px |
| 圆角（表格/抽屉/卡片） | 8px |
| 圆角（标签/按钮） | 4px |
| 圆角（ pills / tab） | 999px |

---

## 4. 组件规范

### 4.1 FilterBar（筛选栏）

**布局**：横向排列，不换行。当空间不足时，最右侧搜索框收缩，下拉框显示为紧凑模式（只显示标签 + 选中数量徽章）。

**结构**：
```
[Goal ▼ 全部] [Task ▼ 全部] [Agent ▼ 全部] [Model ▼ 全部]
[类型 ▼ 全部] [状态 ▼ 全部] [时间 ▼ 全部]         [🔍 搜索日志...]
```

**样式**：
- 每个筛选器是一个 dropdown trigger，高度 32px，padding 6px 10px。
- 默认状态：bg-white, border #e7e5e4, text #78716c。
- 有选中值时：右侧显示数字徽章（bg-stone-800 text-white, 圆角 999px, 12px 字号）。
- 搜索框：width 240px，左侧搜索图标（MagnifyingGlass），placeholder "搜索 input / output / error..."
- Sticky 定位：top 0，z-index 10，下方带 1px border-bottom #e7e5e4。

**交互**：
- 下拉面板：圆角 8px，阴影 `0 4px 24px rgba(0,0,0,0.08)`，最大高度 320px，内部可滚动。
- 类型/状态下拉支持多选（Checkbox 列表）。
- 时间下拉：预设选项（最近 15 分钟 / 1 小时 / 24 小时 / 7 天 / 自定义）。
- 所有筛选变更立即触发 API 请求，表格进入 loading 状态（骨架屏）。

### 4.2 QuickFilterTags（快速筛选标签）

**布局**：FilterBar 下方横向排列，gap 8px。

**预设标签**：
| 标签 | 激活态样式 |
|------|-----------|
| 全部 | bg-stone-800 text-white |
| 仅错误 | 默认: bg-white border; 激活: bg-rose-50 text-rose-800 border-rose-200 |
| 仅模型调用 | 默认: bg-white border; 激活: bg-indigo-50 text-indigo-800 border-indigo-200 |
| 仅 Handoff | 默认: bg-white border; 激活: bg-violet-50 text-violet-800 border-violet-200 |
| 仅工具调用 | 默认: bg-white border; 激活: bg-yellow-50 text-yellow-800 border-yellow-200 |
| 仅审核 | 默认: bg-white border; 激活: bg-purple-50 text-purple-800 border-purple-200 |
| 最近 1 小时 | 默认: bg-white border; 激活: bg-stone-100 text-stone-800 |
| 当前 Goal | 默认: bg-white border; 激活: bg-stone-100 text-stone-800 |

**样式**：height 28px，padding 4px 12px，圆角 999px，border 1px #e7e5e4，字号 12px。

**交互**：点击立即切换，当前激活标签不可关闭。与 FilterBar 联动：点击快速标签时，FilterBar 中对应条件同步更新。

### 4.3 LogListTable（日志列表表格）

**列定义**：

| 列 | 宽度 | 对齐 | 内容 |
|----|------|------|------|
| 时间 | 100px | 左对齐 | HH:MM:SS（Geist Mono） |
| 类型 | 130px | 左对齐 | EventTypeTag（图标 + 文字） |
| 状态 | 90px | 左对齐 | StatusIndicator（图标） |
| Agent | 130px | 左对齐 | Agent 名或 "-" |
| Model | 110px | 左对齐 | Model ID 或 "-" |
| Task | 140px | 左对齐 | Task 名（截断）+ [时间线] 链接 |
| 摘要 | flex-1 | 左对齐 | input/output 摘要前 60 字符 |

**表头样式**：
- height 36px，bg #f5f5f4，text #78716c，字号 12px，font-weight 500。
- 列标题使用 `text-transform: uppercase`，letter-spacing 0.04em（但不用 eyebrow 模式，仅表头）。
- 底部边框 1px solid #e7e5e4。

**行样式**：
- height 40px，padding 8px 12px，border-bottom 1px solid #f5f5f4。
- 悬停：bg #f5f5f4，鼠标指针变为 pointer。
- 错误行：bg #fff1f2，文字 #9f1239（优先级高于悬停色）。
- 新日志行（2 秒内到达）：bg #fefce8，2s 后平滑过渡到正常背景。

**摘要列**：
- 单行截断，max-width 100%，text-overflow ellipsis。
- 如果是代码输出，保留 ```language 标记的前 10 个字符，后面接 "..."

**Task 列的 [时间线] 链接**：
- 位于 Task 名右侧，字号 11px，text #5b4ba4，hover underline。
- 点击切换到 TaskTimelineView。

### 4.4 EventTypeTag（事件类型标签）

**样式**：
- height 22px，padding 2px 8px，圆角 4px，字号 11px，font-weight 500。
- 图标在左，文字在右，gap 4px。
- 图标大小 12px。

**图标映射**（Phosphor Icons，strokeWidth 1.5）：

| 事件类型 | 图标名 | 备选 |
|----------|--------|------|
| model_call | Brain | Cpu |
| agent_step | Robot | Gear |
| tool_call | Wrench | Toolbox |
| task_status_change | ListChecks | ClipboardText |
| quota_status_change | Gauge | Coins |
| handoff_created / completed | ArrowsLeftRight | Swap |
| error | WarningOctagon | Prohibit |
| supervisor_review | Eye | Detective |
| memory_write_candidate | BookBookmark | Sparkle |

### 4.5 StatusIndicator（状态指示器）

**样式**：
- 图标大小 14px，颜色按 3.1.3 节。
- running / pending 状态使用脉冲动画（见 7.1 节）。
- 其余状态为静态图标。

### 4.6 LogDetailDrawer（日志详情抽屉）

**布局**：右侧滑出，width 520px，bg-white，border-left 1px #e7e5e4。

**结构**：
```
┌──────────────────────────────────────────┐
│ [类型标签] [状态图标] 日志详情        [×] │  ← Header, 48px
├──────────────────────────────────────────┤
│ 元数据                                   │  ← MetadataGrid, 2列
│ Goal: xxx           Task: xxx            │
│ Agent: xxx          Model: xxx           │
│ Worker: xxx         Time: xxx            │
├──────────────────────────────────────────┤
│ Token 消耗（model_call / agent_step 时） │  ← TokenUsageSection
│ Input: 1,500    Output: 800    Latency   │
├──────────────────────────────────────────┤
│ 输入                                     │  ← ContentSection
│ ┌────────────────────────────────────┐   │
│ │ 代码块 / 文本，可折叠，带复制按钮  │   │
│ └────────────────────────────────────┘   │
├──────────────────────────────────────────┤
│ 输出                                     │  ← ContentSection
│ ┌────────────────────────────────────┐   │
│ │ 同上                               │   │
│ └────────────────────────────────────┘   │
├──────────────────────────────────────────┤
│ 错误信息（error 时显示）                 │  ← ErrorSection
│ ┌────────────────────────────────────┐   │
│ │ bg-rose-50 区块，显示完整错误      │   │
│ └────────────────────────────────────┘   │
├──────────────────────────────────────────┤
│ 元数据                                   │  ← MetadataSection
│ routing_reason: xxx                      │
│ confidence: 0.95                         │
└──────────────────────────────────────────┘
```

**Header**：
- height 48px，padding 0 16px，border-bottom 1px #e7e5e4。
- 左侧：EventTypeTag（大号，22px 高）+ StatusIndicator + 标题 "日志详情"。
- 右侧：关闭按钮（X，20px）。

**MetadataGrid**：
- 2 列 CSS Grid，gap 12px，padding 16px。
- 每个字段：label（11px，#78716c，uppercase tracking-wide）+ value（13px，#1c1917）。
- 可点击的值（Goal/Task/Agent/Model）使用 text #5b4ba4，hover underline。

**TokenUsageSection**：
- padding 16px，bg #fafaf9，border-top/bottom 1px #f5f5f4。
- 3 列横向排列：Input tokens / Output tokens / Total tokens，每列大数字（Geist Mono, 18px, #1c1917）+ 小标签（11px, #78716c）。
- model_call 额外显示 latency_ms（Geist Mono, "2,500 ms"）。

**ContentSection（输入/输出）**：
- padding 16px，border-bottom 1px #f5f5f4。
- 标题行："输入" / "输出"（13px, 600）+ 折叠/展开按钮 + 复制按钮（右对齐）。
- 内容区：
  - 纯文本：直接显示，max-height 200px，overflow auto。
  - 代码块：背景 #f5f5f4，圆角 4px，padding 12px，font Geist Mono 12px。顶部显示语言标签（如 "tsx"）。
  - 复制按钮：位于代码块右上角，hover 显示，点击后反馈"已复制"。

**ErrorSection**：
- padding 16px，bg #fff1f2，border 1px solid #fecdd3，圆角 4px。
- 字段：error_type（标签）+ error_code（等宽）+ error_message（正文）。
- 开发模式下显示 stack_trace（折叠，默认收起）。

**MetadataSection**：
- padding 16px， KV 列表形式，每个 key 11px #78716c，value 13px #1c1917。
- 复杂对象（如 routing_info）以缩进 JSON 样式展示。

**底部操作区**（仅 error 和 handoff 类型）：
- error：显示 [快速修复] 按钮（Retry / Handoff 选项下拉）。
- handoff：显示 [查看前后对比] 按钮，打开对比视图。

### 4.7 TaskTimelineView（Task 时间线视图）

**进入方式**：从 LogStreamView 点击某 Task 的 [时间线] 链接，或点击 Timeline Tab 后选择 Task。

**布局**：
```
┌──────────────────────────────────────────┐
│ ← 返回列表    Task：生成登录组件         │
│               Goal：实现用户认证系统 [→] │  ← TimelineHeader
├──────────────────────────────────────────┤
│                                          │
│  10:00  ──●──  task_status_change       │
│           │     pending → running       │
│           │                              │
│  10:01  ──●──  agent_step               │
│           │     Planner 拆解任务        │
│           │     └─ 输出：3 个子任务      │
│           │                              │
│  10:02  ──●──  model_call               │
│           │     Coder 调用 claude-3-5   │
│           │     └─ 429 rate limit ⚠️    │
│           │                              │
│  10:03  ──●──  handoff_created          │
│           │     Coder #1 → Coder #2     │
│           │     └─ [查看对比]            │
│           │                              │
│  ...                                     │
│                                          │
├──────────────────────────────────────────┤
│  总耗时：7min | 总 token：3,500 | ...   │  ← TimelineSummaryBar
└──────────────────────────────────────────┘
```

**TimelineHeader**：
- height 56px，padding 0 20px，border-bottom 1px #e7e5e4。
- 左侧：返回按钮（CaretLeft + "返回列表"）+ 分隔线。
- 中间：Task 名（16px, 600）+ Goal 名（13px, #78716c，可点击跳转）。

**TimelineGraph**：
- padding 24px 20px 100px（底部留出 SummaryBar 空间）。
- 垂直布局，每个节点一个横向 flex 行：
  - 左侧时间列：width 64px，text-align right，Geist Mono 12px #78716c。
  - 中轴列：width 24px，居中。节点圆点 10px，连线 1px solid #e7e5e4。
  - 右侧内容列：flex-1。
- **节点圆点样式**：
  - 颜色按事件类型（见 3.1.2）。
  - 错误节点：圆点外圈加 2px #fecdd3 边框。
  - Handoff 节点：圆点稍大（12px），可点击 hover 放大到 14px。
- **节点内容**：
  - 第一行：EventTypeTag + StatusIndicator + Agent/Model 名。
  - 第二行（可选）：摘要文本，13px #78716c，左边距与标签对齐。
  - 可展开：点击节点展开完整 LogDetailDrawer 中的摘要信息。
- **连线**：从上一节点圆点底部到当前节点圆点顶部，1px solid #e7e5e4。首节点无上方连线，末节点无下方连线。

**TimelineSummaryBar**：
- fixed 底部（在 ViewContent 内，非全局 fixed），height 48px，bg-white，border-top 1px #e7e5e4，padding 0 20px。
- 横向 flex，gap 24px，居中对齐。
- 每个统计项：label（11px #78716c）+ value（Geist Mono 14px #1c1917）。
- 统计项：总耗时 / 总 token / 模型调用次数 / Handoff 次数 / 错误次数。

### 4.8 HandoffCompareView（Handoff 对比视图）

**触发**：在 Timeline 或 Drawer 中点击 [查看对比]。

**布局**：Modal 或 Drawer 内嵌，标题"Handoff 前后对比"。

```
┌──────────────────────────────────────────┐
│ 从：Coder #1 (claude-3-5)                │
│ → 到：Coder #2 (gpt-4o)                  │
│ 原因：额度耗尽          时间：10:05      │
├──────────────────────┬───────────────────┤
│ Handoff 前上下文     │ Handoff 后上下文  │
├──────────────────────┼───────────────────┤
│ 已完成任务：         │ 接收到的任务：    │
│ - xxx                │ - xxx             │
│                      │                   │
│ Token：2,500         │ Token：1,800      │
│ [完整度：95%]        │ [完整度：85%]     │
├──────────────────────┴───────────────────┤
│ ⚠️ 上下文损失：400 tokens (16%)          │
│ 丢失细节：表单验证规则...                │
└──────────────────────────────────────────┘
```

- 左右分栏，各 50%，中间 1px 分隔线。
- 底部汇总区域：bg-amber-50，border 1px amber-200，圆角 4px。
- context_loss 用红色强调（#be123c）。

### 4.9 ErrorPanelView（错误面板视图）

**进入方式**：点击 [错误] Tab，或点击快速筛选 [仅错误]。

**ErrorStatsCards**：
- 顶部横向排列 4 张卡片，gap 12px。
- 每张卡片：bg-white，border 1px #e7e5e4，圆角 8px，padding 12px 16px。
- 内容：label（11px #78716c）+ value（Geist Mono 20px #1c1917）。
- 卡片：总计错误 / API 错误 / 工具错误 / 超时。
- API 错误值用 text-rose-700，工具错误用 text-amber-700，超时用 text-orange-700。

**ErrorLogList**：
- 与 LogListTable 同结构，但隐藏"类型"列（已知的 error）。
- 每行增加操作列：[查看] [修复]。
- [修复] 按钮：height 24px，bg-white border，hover bg-stone-50，点击弹出下拉：Retry / Handoff / Ignore。

### 4.10 TokenUsageView（Token 统计视图，P1）

**柱状图样式**：
- 不使用图表库，用纯 div 实现。
- 每行结构：`[名称] [████████░░░░░░░░] [数字] [(百分比)]`
- 条形：height 12px，圆角 999px，bg #e7e5e4（轨道），内部填充色按 Agent/Model 分配（复用事件类型色板中的 Indigo/Teal/Amber 等）。
- 填充动画：页面进入时从 width 0% 过渡到目标宽度，800ms ease-out。

**SummaryStats**：
- 底部一行 3 个大数字：总 token / 总调用 / 平均延迟。
- 数字：Geist Mono 28px 600 #1c1917。

---

## 5. 交互规范

### 5.1 实时日志追加

- **机制**：前端轮询 `GET /logs`（2 秒间隔），或使用 SSE 推送。
- **新日志插入**：按时间倒序，新日志插入列表顶部。
- **高亮动画**：新行背景色从 `#fefce8` 过渡到 `transparent`，持续 2s。过渡期间如果该行是错误，优先使用错误背景色（#fff1f2），2s 后仍保持错误色。
- **计数器更新**：FilterBar 右侧显示当前列表总数（"共 150 条"），新日志到达时数字以 150ms 动画跳动。
- **自动滚动**：如果用户当前滚动位置在顶部（scrollTop < 50px），自动保持顶部展示最新日志；如果用户已向下滚动，保持当前视口位置，顶部显示"有 N 条新日志"提示条，点击后滚动到顶部。

### 5.2 错误自动展开

- **触发条件**：新到达的日志 `event_status` 为 `error` 或 `failed`。
- **行为序列**：
  1. 如果 ExecutionLogPanel（Workspace 内）处于收起状态，自动展开（height 0 → 目标高度，500ms ease-out）。
  2. 如果 LogsPage 当前不在 ErrorPanelView，顶部出现红色 AlertBanner："检测到新错误：[摘要] [查看] [忽略]"。
  3. 错误日志行在列表中置顶高亮（如果筛选条件允许）。

### 5.3 筛选联动

- **FilterBar ↔ QuickFilterTags**：
  - 点击 QuickFilterTag 时，FilterBar 中对应条件自动更新，且该 Tag 显示为激活态。
  - 在 FilterBar 中手动选择条件时，对应的 QuickFilterTag 自动激活（如果完全匹配）。
  - 当多个条件组合无法匹配任何 QuickFilterTag 时，只有 [全部] 处于非激活态，无 Tag 高亮。

- **结果计数**：每次筛选后，FilterBar 右侧显示 "共 N 条"，N 从后端 total 字段获取。

### 5.4 视图切换

- **LogStream → TaskTimeline**：
  - 点击 [时间线] 链接，当前视图淡出（150ms），Timeline 视图淡入（200ms），URL 更新。
  - Timeline 节点 stagger 进入（每个节点 delay 50ms，从下往上）。
  - 返回列表时反向动画。

- **Tab 切换**：
  - Tab 激活态：bg-stone-800 text-white 圆角 999px。
  - Tab 非激活态：bg-transparent text-stone-500 hover text-stone-700。
  - 内容切换：淡入淡出 150ms。

### 5.5 分页

- 底部居中分页器：Previous / [1] [2] [3] ... [10] / Next。
- 当前页：bg-stone-800 text-white，圆角 4px。
- 非当前页：hover bg-stone-100。
- 每页默认 50 条，可选 20 / 50 / 100。

---

## 6. 动画规范

### 6.1 功能性动画

| 动画 | 参数 | 触发 |
|------|------|------|
| 新日志高亮 | background-color: #fefce8 → transparent, 2s ease-out | 新日志插入 |
| Drawer 滑入 | transform: translateX(100%) → 0, 300ms cubic-bezier(0.16, 1, 0.3, 1) | 点击日志行 |
| Drawer 滑出 | transform: translateX(0) → 100%, 200ms ease-in | 点击关闭 |
| Timeline 节点进入 | opacity: 0 → 1, translateY(8px) → 0, 300ms, stagger 50ms | 切换到 Timeline 视图 |
| 错误面板展开 | height: 0 → auto, 500ms ease-out | 检测到错误日志 |
| Token 柱状图填充 | width: 0% → N%, 800ms ease-out | 进入 Token Tab |
| 脉冲（running 状态） | scale: 1 → 1.4 → 1, opacity: 1 → 0.5 → 1, 2s infinite | 事件状态为 running |

### 6.2 Reduced Motion

- 所有动画在 `prefers-reduced-motion: reduce` 下取消。
- 新日志高亮直接变为最终背景色（无过渡）。
- Drawer 无滑入，直接显示。
- Timeline 节点无 stagger，直接渲染。

---

## 7. 响应式规范

### 7.1 断点策略

| 断点 | 布局调整 |
|------|----------|
| >= 1280px | 完整 7 列表格，Drawer 520px，Timeline 左右充足留白 |
| >= 1024px | 隐藏 Model 列，Drawer 480px |
| >= 768px | 隐藏 Task 列的 [时间线] 链接（点击行进入 Timeline），摘要列截断到 40 字符 |
| < 768px | 表格变为卡片列表：每卡片显示时间、类型图标、状态图标、摘要，点击展开详情卡片（非 Drawer） |

### 7.2 移动端卡片列表

- 每卡片：bg-white，border 1px #e7e5e4，圆角 8px，padding 12px，margin-bottom 8px。
- 卡片内：横向 flex，时间（Geist Mono 11px #78716c）+ EventTypeTag（compact 模式，只显示图标）+ 摘要（13px）。
- 点击卡片 → 展开详情卡片（非右侧 Drawer，而是在列表中展开 accordion 样式）。
- 筛选栏变为顶部一个"筛选"按钮，点击后底部弹出 action sheet 选择筛选条件。

---

## 8. 空状态与异常状态

### 8.1 空状态

| 场景 | 视觉 | 文案 |
|------|------|------|
| 系统无日志 | 页面中央 Large Icon (Scroll / Binoculars) + 标题 + 副文案 | "暂无执行日志" / "开始一个 Goal 后，执行过程将在这里记录" |
| 筛选无结果 | 列表区域内 Icon (MagnifyingGlassSlash) + 文案 + [清除筛选] 按钮 | "未找到匹配的日志" / "尝试调整筛选条件或清除搜索关键词" |
| Task 无时间线 | Timeline 中央 Icon (ClockCounterClockwise) | "该 Task 暂无执行日志" |
| Token 无数据 | Chart 区域占位 | "暂无 token 使用记录" / "执行模型调用后将显示统计" |

### 8.2 加载状态

- **表格加载**：骨架屏（shimmer），5 行，每行 7 列灰色矩形脉冲。
- **Timeline 加载**：中央 Spinner（非全屏，仅在内容区），文字 "加载时间线..."
- **Drawer 加载**：Drawer 内部骨架屏，3 个区块。

### 8.3 错误状态

- **API 加载失败**：表格区域显示红色 Icon (WarningOctagon) + "日志加载失败" + [重试] 按钮。
- **单条详情加载失败**：Drawer 内显示错误提示 + [重试]。

---

## 9. 与全局设计系统的一致性

### 9.1 跨模块复用

| 组件 | 来源模块 | 复用说明 |
|------|----------|----------|
| StatusTag | Quota Manager | 复用状态标签样式逻辑，但 Logs 的状态枚举不同 |
| ParticipantArrow | Handoff Manager | HandoffCompareView 中复用 from→to 箭头可视化 |
| AlertBanner | Agent Workspace | 错误自动展开时的顶部提示复用 AlertBanner 组件 |
| TopStatusBar | Agent Workspace | 如果在 Workspace 内嵌入 Logs Panel，复用全局 TopStatusBar |

### 9.2 颜色锁定

- 全局主中性色锁定为 Stone 系列，不引入新的灰度。
- Handoff 相关视觉元素锁定为 Violet（#ede9fe / #5b4ba4），与 Handoff Manager 保持一致。
- 错误锁定为 Rose 系列，与全局错误态一致。

---

## 10. 验收检查清单

- [ ] 日志列表表格在 1000 条数据下滚动流畅，无卡顿。
- [ ] 错误日志行在列表中一眼可辨（红色背景 + 状态图标）。
- [ ] 新日志追加时顶部高亮 2 秒后平滑消失。
- [ ] 点击日志行 300ms 内 Drawer 滑出，展示完整字段。
- [ ] Task Timeline 中 10 个事件节点在 3 秒内完成 stagger 进入动画。
- [ ] Handoff 对比视图中，token 损失数字突出显示。
- [ ] 筛选栏支持 Goal + Task + Agent + Model + 类型 + 状态 + 时间 + 关键词的任意组合。
- [ ] 快速筛选标签点击后 100ms 内更新列表。
- [ ] Token 柱状图不使用外部图表库，纯 CSS div 实现。
- [ ] 移动端 (< 768px) 表格退化为卡片列表，点击展开详情。
- [ ] 所有动画在 prefers-reduced-motion 下静默失效。
