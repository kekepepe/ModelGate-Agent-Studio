# Visualization & Statistics UI Spec

> 模块：P2-2 Visualization & Statistics
> 日期：2026-07-02

## 1. 总体风格

沿用 ModelGate 现有低饱和、非深色、Claude-inspired 风格：

- 页面背景：`stone-50`
- 卡片背景：`white`
- 边框：`stone-200`
- 主文本：`stone-800`
- 次要文本：`stone-500`
- 强调色：`lavender` / `brick` / `green` / `amber`

图表不使用高饱和配色，优先使用 stone/lavender/brick/green/amber 的柔和色。

## 2. Dashboard 页面结构

路径：`/dashboard`

```text
Dashboard
系统运行统计与资源趋势

[Active Goals] [Completed Today] [Tokens Today] [Model Calls] [Tool Calls] [Handoffs]

┌───────────────────────────────┐ ┌───────────────────────────────┐
│ Token Usage Trend             │ │ Model Usage Distribution       │
│ line chart                    │ │ pie chart                      │
└───────────────────────────────┘ └───────────────────────────────┘

┌───────────────────────────────┐ ┌───────────────────────────────┐
│ Agent Performance             │ │ Tool Usage                     │
│ bar chart                     │ │ bar chart                      │
└───────────────────────────────┘ └───────────────────────────────┘

┌───────────────────────────────┐ ┌───────────────────────────────┐
│ Quota Trend                   │ │ Recent Goals                   │
│ area chart                    │ │ compact list                   │
└───────────────────────────────┘ └───────────────────────────────┘
```

## 3. 摘要卡片

每张卡片结构：

```text
┌────────────────────┐
│ Label              │
│ 12,340             │
│ short helper text  │
└────────────────────┘
```

### 指标

- Active Goals
- Completed Today
- Tokens Today
- Model Calls
- Tool Calls
- Handoffs

### 状态

- loading：骨架块
- empty：数值显示 0
- error：页面顶部显示错误提示，卡片不显示假数据

## 4. 图表组件规范

### 4.1 TokenUsageChart

- 类型：折线图
- X：日期
- Y：Token 数
- 辅助线：model_calls、tool_calls 可作为 secondary visual（MVP 可只显示 Token）
- 空状态：`暂无 Token 趋势数据`

### 4.2 ModelUsagePieChart

- 类型：饼图
- 数据：`model_usage[].tokens_used`
- Tooltip：展示模型名、Token、调用次数
- 空状态：`暂无模型使用数据`

### 4.3 AgentPerformanceChart

- 类型：柱状图
- X：Agent 名称
- Y：成功率百分比
- Tooltip：展示完成/失败/平均 Token/平均耗时
- 空状态：`暂无 Agent 执行数据`

### 4.4 QuotaTrendChart

- 类型：面积图
- X：日期
- Y：Quota usage percent
- 用于 Dashboard 和 QuotaOverviewPage
- 空状态：`暂无 Quota 趋势数据`

### 4.5 ToolUsageChart

- 类型：柱状图
- X：工具名
- Y：调用次数
- Tooltip：展示调用次数、成功率
- 空状态：`暂无工具调用数据`

## 5. Recent Goals 列表

```text
Recent Goals
- Build runtime demo       done       07-02 10:30
- Add tool registry        running    07-02 09:10
```

- status badge 使用现有状态配色。
- 点击跳转 Workspace 或相关页面可后续扩展，MVP 不要求。

## 6. QuotaOverviewPage 嵌入

在现有 Quota Overview 页面底部或统计卡片后增加：

```text
Quota Trend
[area chart: last 7 days quota usage]
```

要求：

- 不破坏原有 Quota 列表和状态卡片。
- Dashboard API 失败时仅显示趋势区域错误，不影响 Quota 主内容。

## 7. 响应式布局

- `lg` 以上：两列图表网格。
- `md`：两列摘要卡片，单列图表。
- `sm`：单列所有内容。
- 图表统一使用 `ResponsiveContainer`。

## 8. 交互与动效

- MVP 不做复杂动画。
- 卡片 hover 仅轻微 border/text 变化。
- 图表 tooltip 使用 Recharts 默认交互并保持简洁。
