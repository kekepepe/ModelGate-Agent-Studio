# Agent Workspace 技术型 PRD

> 所属产品：ModelGate Agent Studio
>
> 所属阶段：MVP-A / MVP-B 核心页面
>
> 文档定位：Agent Workspace 的产品与技术需求说明，作为前端组件、状态管理、后端接口和数据结构的实现依据。
>
> **本版重点：基于 Model Router、Handoff Manager、Quota Manager、Logs/Observability 等模块的完整状态定义，重写 Workspace 的状态可视化设计，确保用户能在一个页面中"看到"整个协作系统的运行状态。**

---

## 1. 功能背景

ModelGate Agent Studio 是一个多模型 Agent 协作平台。用户输入一个 Goal 后，系统通过 Planner Agent 拆解成多个 Task，并将 Task 分配给不同 Agent Station。每个 Agent Station 由特定模型驱动的 Worker 执行。

Agent Workspace 是平台的核心工作区，也是用户与多 Agent 协作系统交互的主界面。它的核心价值不是输入输出，而是**状态可视化**：

```text
用户输入 Goal
  ↓
Planner 拆解 Task                    ← Workspace 显示 Goal 状态 planning
  ↓
Model Router 选择模型                ← Workspace 显示 RoutingResultCard
  ↓
Runtime 调用模型 API                 ← Workspace 显示 model_call 日志
  ↓
Agent 执行 Step                      ← Workspace 显示 agent_step 日志
  ↓
Tool 执行                            ← Workspace 显示 tool_call 日志
  ↓
Quota Manager 检测额度               ← Workspace 显示 Risk Badge
  ↓
Handoff Manager 触发交接             ← Workspace 显示 HandoffStatusIndicator
  ↓
Summarizer 压缩上下文                ← Workspace 显示 Handoff 对比
  ↓
Supervisor 审核                      ← Workspace 显示 supervisor_review 日志
  ↓
Goal 完成                            ← Workspace 显示 Final Summary
```

Workspace 不是普通聊天界面，也不是简单的模型列表。它的核心表达是：

> **在一个页面里，把 Goal、Task、Agent、Worker、Model、Handoff、Quota、Log 的完整状态变化，全部可视化出来。**

---

## 2. 用户问题

### 2.1 主要用户

- 多模型重度使用的开发者
- 同时使用多个 AI Coding Plan 或 API 的开发者
- 需要长时间推进复杂任务的独立开发者 / AI 产品经理 / 研究者

### 2.2 用户痛点

#### 痛点一：多 Agent 协作不可见

用户同时使用多个模型时，无法直观看到：

- 当前有哪些 Agent 在工作，处于什么状态。
- 每个 Agent 负责什么任务，执行到哪一步。
- 当前是哪个 Worker（哪个模型）正在哪个工位上执行。
- 任务之间是如何流转的，依赖关系是什么。

#### 痛点二：状态变化不可感知

系统内部发生了很多状态变化，但用户看不到：

- Model Router 为什么选择这个模型？置信度是多少？有没有风险？
- Quota Manager 检测到额度不足，但用户直到报错才知道。
- Handoff 正在进行中，用户不知道交接到了哪一步。
- Agent 执行了多个 Step，用户只能看到最终结果。
- Task 从 pending → assigned → running → waiting → handoff → completed，用户无法感知中间状态。

#### 痛点三：任务中断后上下文丢失

当一个模型因为额度、错误、质量不足等原因无法继续时：

- 用户需要手动复制上下文。
- 新模型需要重新理解任务。
- 已完成的步骤容易遗漏。
- 约束和决策容易被忽略。

用户需要一个能看到 Handoff 过程、能验证交接摘要是否完整的界面。

#### 痛点四：执行过程不可追踪

Agent 执行过程中：

- 模型调用了多少次，每次用了多少 token。
- 输出了什么内容，遇到了什么错误。
- 为什么选择了这个模型，备用模型是谁。
- Handoff 发生在哪一步，前后上下文对比如何。

没有结构化日志，用户无法判断系统是否按预期工作。

### 2.3 核心问题

Agent Workspace 要回答的问题是：

> **用户如何在一个页面里，实时看到 Goal → Task → Agent → Worker → Model → Router → Quota → Handoff → Logs 的全链路状态变化？**

---

## 3. 产品目标

### 3.1 核心目标

1. **Goal 状态可视化**：Goal 从 idle → planning → running → handoff → completed/failed 的完整状态流转可见。
2. **Task 状态可视化**：每个 Task 的 pending → assigned → running → waiting → handoff → completed/failed 状态在卡片上直观展示。
3. **Agent Station 状态可视化**：每个 Agent Station 的 idle → queued → running → waiting → reviewing → handoff → blocked → error → done 状态通过颜色、图标、动画表达。
4. **Worker 状态可视化**：WorkerBadge 实时展示当前绑定的模型、额度状态、执行状态。
5. **Model Router 决策可视化**：RoutingResultCard 展示推荐模型、置信度、风险标记、评分拆解。
6. **Quota 状态可视化**：Risk Badge 在所有涉及模型的地方展示额度状态（normal/warning/near_limit/limited/cooldown/unknown）。
7. **Handoff 状态可视化**：HandoffStatusIndicator 展示交接的完整状态机（requested → generating_summary → ready → accepted → completed/failed）。
8. **Logs 实时可视化**：ExecutionLogPanel 实时展示 model_call、agent_step、tool_call、task_status_change、quota_status_change、handoff_created/completed、error、supervisor_review 等日志。
9. **任务依赖可视化**：Task Tree 展示 Task 之间的父子关系和依赖关系。
10. **Token 消耗可视化**：Token Usage Summary 展示各 Agent、各 Model 的 token 消耗统计。

### 3.2 非目标

当前阶段不追求：

- 通用聊天对话界面。
- 把 Agent 等同于模型选择器。
- 复杂像素办公室动画系统。
- 拖拽式工作流编辑器。
- 多人实时协作编辑。
- 完全自动执行无需用户确认。

### 3.3 成功判断

Agent Workspace 成功的标志：

> 用户输入 Goal 后，可以在 Workspace 中**实时看到** Planner 拆解 Task、Model Router 选择模型、Coder 编写、Reviewer 审查、Handoff 交接、Quota 预警、Summarizer 总结、Supervisor 验收的全过程，每个状态变化都有对应的视觉表达。

---

## 4. 状态可视化设计

### 4.1 状态可视化原则

Workspace 的状态可视化遵循以下原则：

1. **颜色编码**：每种状态有固定的颜色，全系统一致。
2. **图标强化**：状态配合图标，提升识别速度。
3. **动画过渡**：状态变化时有平滑过渡动画（300ms）。
4. **层级清晰**：全局状态（Goal）→ 任务状态（Task）→ 工位状态（Agent）→ 实例状态（Worker）→ 模型状态（Quota），层层递进。
5. **联动可见**：一个模块的状态变化，在相关组件上同步反映。

### 4.2 全局状态栏（Top Status Bar）

**布局**：

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Agent Workspace                                              [设置] [帮助] │
├──────────────────────────────────────────────────────────────────────────────┤
│ Goal: 实现用户认证系统                                    [运行中 ▶] [停止] │
│ ┌──────────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐            │
│ │ 🎯 planning  │→ │ ▶ running│→ │ ⏸ handoff│→ │ ✓ completed│              │
│ └──────────────┘  └────────┘  └────────┘  └────────┘  └────────┘            │
│ 进度: 3/5 Tasks  │  Token: 12.5k  │  Handoff: 1  │  耗时: 8m32s             │
└──────────────────────────────────────────────────────────────────────────────┘
```

**元素说明**：

| 元素 | 状态 | 颜色 | 说明 |
|------|------|------|------|
| Goal 状态标签 | idle | 灰色 | 未启动 |
| | planning | 紫色 | Planner 正在拆解 |
| | running | 蓝色 | Task 正在执行 |
| | handoff | 橙色 | 存在进行中的 Handoff |
| | completed | 绿色 | 所有 Task 完成 |
| | failed | 红色 | 任务失败 |
| 进度 | - | 蓝色进度条 | 已完成 Task / 总 Task |
| Token | - | 数字 | 当前 Goal 累计 token 消耗 |
| Handoff | - | 数字 | 当前 Goal 累计 Handoff 次数 |
| 耗时 | - | 数字 | Goal 从开始到现在的耗时 |

### 4.3 Task 状态可视化

#### 4.3.1 TaskCard 状态样式

TaskCard 是状态可视化的核心组件。每个 TaskCard 的边框、背景、图标、进度条都随状态变化。

**状态样式表**：

| 状态 | 边框 | 背景 | 图标 | 动画 |
|------|------|------|------|------|
| pending | 灰色虚线 `border-dashed border-gray-300` | 白色 | ⏸ 暂停 | 无 |
| assigned | 灰色实线 `border-gray-400` | 白色 | 📋 待办 | 无 |
| running | 蓝色实线 `border-blue-500` + 阴影 | `bg-blue-50` | ▶ 播放 | 边框呼吸动画 |
| waiting | 黄色实线 `border-yellow-500` | `bg-yellow-50` | ⏳ 等待 | 无 |
| handoff | 紫色实线 `border-purple-500` + 阴影 | `bg-purple-50` | 🔄 交接 | 边框旋转动画 |
| completed | 绿色实线 `border-green-500` | `bg-green-50` | ✓ 完成 | 无 |
| failed | 红色实线 `border-red-500` + 阴影 | `bg-red-50` | ✗ 失败 | 抖动动画 |

**呼吸动画**（running 状态）：

```css
@keyframes breathe {
  0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.3); }
  50% { box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1); }
}
.task-card.running {
  animation: breathe 2s ease-in-out infinite;
}
```

**旋转动画**（handoff 状态）：

```css
@keyframes rotate-border {
  0% { border-color: rgba(147, 51, 234, 0.3); }
  50% { border-color: rgba(147, 51, 234, 1); }
  100% { border-color: rgba(147, 51, 234, 0.3); }
}
.task-card.handoff {
  animation: rotate-border 1.5s linear infinite;
}
```

#### 4.3.2 TaskCard 完整展示

```
┌──────────────────────────────────────────────┐
│ [▶] Task #2: 实现登录组件                    │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                              │
│ 状态: running (Step 3/5: 生成代码骨架)       │
│ Agent: Coder Station                         │
│ Worker: 🤖 gpt-4o                            │
│                                              │
│ [RiskBadge: 🟢 normal] [ModelScore: 0.95]   │
│                                              │
│ 进度: ████████████████████░░░░  60%         │
│                                              │
│ 最新输出:                                    │
│ ┌────────────────────────────────────────┐   │
│ │ 正在生成 React 组件...                  │   │
│ │ ```tsx                                 │   │
│ │ import React, { useState } from ...    │   │
│ └────────────────────────────────────────┘   │
│                                              │
│ Token: 3.2k  │  耗时: 2m15s  │  Step: 3/5  │
│                                              │
│ [HandoffStatusIndicator: 无]                │
└──────────────────────────────────────────────┘
```

### 4.4 Agent Station 状态可视化

#### 4.4.1 Agent Station Card 状态样式

| 状态 | 边框 | 背景 | 图标 | 说明 |
|------|------|------|------|------|
| idle | 灰色 | 白色 | ⏸ | 空闲 |
| queued | 灰色 | `bg-gray-50` | 📋 | 有任务排队 |
| running | 蓝色 | `bg-blue-50` | ▶ | 正在执行 |
| waiting | 黄色 | `bg-yellow-50` | ⏳ | 等待依赖 |
| reviewing | 青色 | `bg-cyan-50` | 👁 | 审查中 |
| handoff | 紫色 | `bg-purple-50` | 🔄 | 交接中 |
| blocked | 红色 | `bg-red-50` | 🚫 | 被阻塞 |
| error | 红色 | `bg-red-50` | ⚠ | 出错 |
| done | 绿色 | `bg-green-50` | ✓ | 当前任务完成 |

#### 4.4.2 Agent Station Card 完整展示

```
┌──────────────────────────────────────────────┐
│ 📝 Coder Station                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                              │
│ [WorkerBadge]                                │
│ ┌────────────────────────────────────────┐   │
│ │ 🤖 gpt-4o                              │   │
│ │ ● running                              │   │
│ │ [RiskBadge: 🟢 normal]                 │   │
│ │ [RoutingResultBadge: 置信度 0.95]      │   │
│ └────────────────────────────────────────┘   │
│                                              │
│ 当前任务:                                    │
│ [TaskCard: 实现登录组件] running            │
│                                              │
│ 历史任务: 12  完成: 11  失败: 1             │
│                                              │
│ [查看配置] [手动 Handoff]                   │
└──────────────────────────────────────────────┘
```

### 4.5 Worker 状态可视化

#### 4.5.1 WorkerBadge 组件

WorkerBadge 展示当前绑定到 Agent Station 的 Worker（模型实例）的完整状态。

```
┌──────────────────────────────────────────────┐
│ 🤖 gpt-4o                                    │
│ ● running                                    │
│                                              │
│ [RiskBadge: 🟢 normal]                       │
│ [RoutingResultBadge: 置信度 0.95]            │
│                                              │
│ Token: 3.2k / 1M  (使用率: 0.3%)            │
│ 调用次数: 15  延迟: 2.1s                    │
└──────────────────────────────────────────────┘
```

**状态灯颜色**：

| Worker 状态 | 颜色 | 说明 |
|-------------|------|------|
| idle | 灰色 | 未绑定任务 |
| running | 蓝色（呼吸） | 正在执行 |
| handoff_required | 紫色 | 需要交接 |
| completed | 绿色 | 完成 |
| failed | 红色 | 失败 |

#### 4.5.2 Risk Badge（额度风险徽章）

Risk Badge 嵌入在 WorkerBadge 中，展示当前模型的 QuotaStatus。

引用 Quota Manager PRD 的 Risk Badge 定义：

| QuotaStatus | 颜色 | 图标 | 文本 |
|-------------|------|------|------|
| NORMAL | 绿色 | ✓ | 正常 |
| WARNING | 黄色 | ⚠ | 注意 |
| NEAR_LIMIT | 橙色 | 🔴 | 接近上限 |
| LIMITED | 红色 | ✕ | 已受限 |
| COOLDOWN | 蓝色 | ⏱ | 冷却中 |
| UNKNOWN | 灰色 | ? | 未知 |

**交互**：

- 鼠标悬停 → Tooltip 展示：使用率、剩余额度、最近错误。
- 点击 → 跳转到 Quota Overview 页面。

### 4.6 Model Router 决策可视化

#### 4.6.1 RoutingResultCard

当 Model Router 做出路由决策时，Workspace 展示 RoutingResultCard：

```
┌──────────────────────────────────────────────┐
│ 🧭 Model Router 决策                         │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                              │
│ 推荐模型: gpt-4o                             │
│ 置信度: ████████████████████░░░░  0.95      │
│                                              │
│ 评分拆解:                                    │
│ ┌────────────────────────────────────────┐   │
│ │ capability_match  ████████████  0.25   │   │
│ │ role_match        ██████████    0.20   │   │
│ │ context_fit       ████████      0.15   │   │
│ │ cost_fit          ████████      0.15   │   │
│ │ speed_fit         █████         0.10   │   │
│ │ quota_health      █████         0.10   │   │
│ │ historical_perf   ███           0.05   │   │
│ └────────────────────────────────────────┘   │
│                                              │
│ 路由理由: "代码生成任务，GPT-4o 能力匹配度最高"│
│                                              │
│ [RiskFlagBanner]                             │
│ ⚠️ 风险标记: near_quota_limit               │
│                                              │
│ 备用模型: claude-3-5, deepseek-chat          │
│                                              │
│ [接受] [切换模型] [查看详情]                 │
└──────────────────────────────────────────────┘
```

**交互**：

- 用户可点击 [切换模型] 手动覆盖路由决策。
- 点击 [查看详情] 展开完整评分矩阵。
- RiskFlagBanner 引用 Model Router PRD 的 risk_flags 定义。

### 4.7 Handoff 状态可视化

#### 4.7.1 HandoffStatusIndicator

HandoffStatusIndicator 是状态可视化的重点组件，展示 Handoff 的完整状态机。

**状态样式**：

| Handoff 状态 | 颜色 | 图标 | 动画 | 说明 |
|--------------|------|------|------|------|
| requested | 黄色 | 🔄 | 旋转 | 交接请求中 |
| generating_summary | 紫色 | ✍ | 脉冲 | 正在生成摘要 |
| ready | 紫色 | 📋 | 无 | 摘要已生成，等待接受 |
| accepted | 蓝色 | ▶ | 无 | 已接受，加载中 |
| completed | 绿色 | ✓ | 无 | 交接完成 |
| failed | 红色 | ✗ | 抖动 | 交接失败 |

#### 4.7.2 Handoff 流程可视化

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Handoff #1: 额度耗尽交接                                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Coder #1 (claude-3-5)          Coder #2 (gpt-4o)                           │
│  ┌──────────────────────┐      ┌──────────────────────┐                     │
│  │ ● running            │  🔄  │ ○ idle               │                     │
│  │ [RiskBadge: 🔴 limited]│→→→│ [RiskBadge: 🟢 normal]│                     │
│  └──────────────────────┘      └──────────────────────┘                     │
│         │                              ↑                                     │
│         │  1. requested                │ 4. accepted                         │
│         │  2. generating_summary       │                                     │
│         │  3. ready ───────────────────┘                                     │
│         │  5. completed                                                        │
│         ↓                                                                    │
│  ┌──────────────────────┐                                                    │
│  │ Handoff Summary      │                                                    │
│  │ 已完成: 骨架生成      │                                                    │
│  │ 待办: 样式美化        │                                                    │
│  │ Token: 2,500 → 1,800  │                                                    │
│  │ [上下文完整度: 85%]   │                                                    │
│  └──────────────────────┘                                                    │
│                                                                              │
│ 进度: [requested] → [generating_summary] → [ready] → [accepted] → [completed]│
│                                                                              │
│ [查看摘要] [查看对比] [取消交接]                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### 4.7.3 Handoff 前后对比视图

点击 [查看对比] 打开 Handoff 对比抽屉：

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Handoff 前后对比                                              [×]          │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ 从: Coder #1 (claude-3-5)          到: Coder #2 (gpt-4o)                    │
│ 原因: 额度耗尽                      时间: 2026-06-25 10:05:00               │
├──────────────────────────────┬───────────────────────────────────────────────┤
│ Handoff 前上下文             │ Handoff 后上下文                              │
├──────────────────────────────┼───────────────────────────────────────────────┤
│ 已完成任务:                  │ 接收到的任务:                                 │
│ - 生成登录组件骨架           │ - 继续完善登录组件                            │
│ - 实现表单验证逻辑           │ - 添加密码强度检查                            │
│                              │                                               │
│ 待办:                        │ 已知约束:                                     │
│ - 添加密码强度检查           │ - 使用 React Hook Form                        │
│ - 样式美化                   │ - 支持邮箱验证                                │
│                              │                                               │
│ Token 数: 2,500              │ Token 数: 1,800                               │
│ [上下文完整度: 100%]         │ [上下文完整度: 85%]                           │
├──────────────────────────────┴───────────────────────────────────────────────┤
│ ⚠️ 上下文损失: 400 tokens（表单验证的具体规则细节部分丢失）                   │
│                                                                              │
│ [导出对比] [标记为正常]                                                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4.8 Quota 状态可视化

#### 4.8.1 模型额度预警条

当任何模型的 quota_status 变为 WARNING 或 NEAR_LIMIT 时，Workspace 顶部显示预警条：

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ⚠️ 额度预警: claude-3-5 使用率 78% (WARNING)，建议关注或准备 Handoff        │
│ [查看额度] [立即 Handoff] [忽略]                                           │
└──────────────────────────────────────────────────────────────────────────────┘
```

当 quota_status 变为 LIMITED 或 COOLDOWN 时：

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 🔴 额度告警: gpt-4 已受限 (LIMITED)，任务已自动 Handoff 至 claude-3-5      │
│ [查看额度] [查看 Handoff] [确认]                                           │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### 4.8.2 TaskCard 上的额度状态

每个使用模型的 TaskCard 上，在 WorkerBadge 旁显示 RiskBadge：

```
TaskCard
├── 状态: running
├── Agent: Coder Station
├── Worker: 🤖 gpt-4o [RiskBadge: 🟢 normal]
└── Token: 3.2k
```

### 4.9 Logs 实时可视化

#### 4.9.1 ExecutionLogPanel 状态表达

ExecutionLogPanel 的每条日志都有对应的状态图标和颜色：

引用 Logs PRD 的日志类型定义：

| 日志类型 | 图标 | 颜色 | 状态表达 |
|----------|------|------|----------|
| model_call (completed) | ✓ | 绿色 | 模型调用成功 |
| model_call (failed) | ✗ | 红色 | 模型调用失败 |
| agent_step (completed) | ✓ | 蓝色 | Step 完成 |
| agent_step (failed) | ✗ | 红色 | Step 失败 |
| tool_call (completed) | ✓ | 青色 | 工具执行成功 |
| tool_call (failed) | ✗ | 红色 | 工具执行失败 |
| task_status_change | → | 灰色 | 状态流转 |
| quota_status_change | ⚡ | 黄色/橙色/红色 | 额度变化 |
| handoff_created | 🔄 | 紫色 | 交接创建 |
| handoff_completed | ✓ | 绿色 | 交接完成 |
| error | ⚠ | 红色 | 错误 |
| supervisor_review (approved) | ✓ | 绿色 | 审核通过 |
| supervisor_review (rejected) | ✗ | 红色 | 审核拒绝 |
| supervisor_review (needs_revision) | 📝 | 黄色 | 需要修改 |

#### 4.9.2 日志实时滚动

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Execution Log                                               [筛选 ▼] [展开] │
├──────────────────────────────────────────────────────────────────────────────┤
│ 10:07 ✓ task_status_change: running → completed (Task #3)                  │
│ 10:06 ✓ supervisor_review: Reviewer 审核通过 (Task #3)                      │
│ 10:05 🔄 handoff_created: Coder #1 → Coder #2 (原因: 额度耗尽)             │
│ 10:04 ⚡ quota_status_change: normal → LIMITED (gpt-4)                     │
│ 10:03 ✗ model_call: 429 rate limit (claude-3-5)                            │
│ 10:02 ✓ tool_call: 文件写入成功 (Task #2)                                  │
│ 10:01 ✓ model_call: gpt-4o 调用成功 (Task #2, 2.3k tokens)                 │
│ 10:00 ✓ agent_step: Planner 拆解完成 (5 个 Task)                           │
├──────────────────────────────────────────────────────────────────────────────┤
│ 运行中 · 12 次模型调用 · 5 个 Task · 1 次 Handoff · 1 个错误              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4.10 错误状态可视化

#### 4.10.1 Error Banner

当 error 日志产生时，Workspace 显示 Error Banner：

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ⚠️ 错误: Coder Agent 模型调用失败 (429 rate limit)                          │
│ 任务: 实现登录组件 (Task #2)                                                │
│ 建议: 系统已自动触发 Handoff 至备用模型 gpt-4o                               │
│ [查看详情] [重试] [Handoff] [忽略]                                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### 4.10.2 TaskCard 错误状态

```
┌──────────────────────────────────────────────┐
│ [✗] Task #2: 实现登录组件                    │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                              │
│ 状态: failed                                 │
│ 错误: 429 rate limit (claude-3-5)           │
│                                              │
│ ⚠️ 额度状态: LIMITED                         │
│                                              │
│ [重试] [Handoff 至备用模型] [查看日志]       │
└──────────────────────────────────────────────┘
```

---

## 5. 核心用户流程

### 5.1 标准任务流程（带状态可视化）

```text
1. 用户进入 Agent Workspace 页面。
   → Top Status Bar 显示 Goal: idle

2. 用户在左侧 GoalInputPanel 输入 Goal。
   → 输入框激活，「开始」按钮可用。

3. 用户点击「开始」。
   → Top Status Bar: idle → planning
   → GoalInputPanel 显示 planning 动画。

4. Planner Agent Station 被激活，WorkerBadge 显示模型名和状态灯。
   → AgentStationBoard 中 Planner Card 边框变蓝，WorkerBadge 显示 ▶ running。
   → RoutingResultCard 弹出："Planner 路由决策：claude-3-5，置信度 0.92"。

5. Planner 拆解完成，生成 5 个 Task。
   → Task Tree 自动展开，5 个 Task 显示为 pending（灰色虚线）。
   → Top Status Bar: planning → running。

6. 第一个 Task 分配给 Coder Agent Station。
   → Task #1 状态: pending → assigned（灰色实线）。
   → Coder Card 边框变蓝，WorkerBadge 显示 ▶ running。
   → RoutingResultCard 弹出："Coder 路由决策：gpt-4o，置信度 0.95"。

7. Coder 开始执行，输出中间结果。
   → Task #1 状态: assigned → running（蓝色呼吸动画）。
   → TaskCard 显示最新输出片段。
   → ExecutionLogPanel 追加 model_call 和 agent_step 日志。
   → Token 计数实时更新。

8. Coder 完成，Task 流转给 Reviewer。
   → Task #1 状态: running → completed（绿色）。
   → Coder Card 边框变绿，WorkerBadge 显示 ✓ done。
   → Task #2 状态: pending → assigned → running。
   → Reviewer Card 边框变蓝。

9. Reviewer 完成审查，通过。
   → Task #2 状态: running → completed（绿色）。
   → supervisor_review 日志显示 ✓ approved。

10. 所有 Task 完成，Supervisor 进入 reviewing。
    → Top Status Bar: running → reviewing。
    → Supervisor Card 边框变青色。

11. Supervisor 生成 Final Summary。
    → Top Status Bar: reviewing → completed（绿色）。
    → GoalInputPanel 显示 Final Summary。
    → ExecutionLogPanel 展示完整执行过程。
```

### 5.2 Handoff 流程（带状态可视化）

```text
1. Coder Agent 正在执行 Task #2，状态 running（蓝色呼吸）。

2. Quota Manager 检测到 claude-3-5 额度 warning → near_limit → LIMITED。
   → WorkerBadge 上的 RiskBadge: 🟢 → ⚠ → 🔴 → ✕。
   → Quota 预警条弹出："🔴 额度告警: claude-3-5 已受限"。
   → quota_status_change 日志写入。

3. 系统自动触发 Handoff。
   → Task #2 状态: running → handoff（紫色旋转动画）。
   → HandoffStatusIndicator 显示：🔄 requested。
   → handoff_created 日志写入。

4. Handoff Manager 生成 Handoff Summary。
   → HandoffStatusIndicator: requested → generating_summary（✍ 脉冲）。
   → 生成完成后 → ready（📋）。

5. Model Router 选择备用模型 gpt-4o。
   → RoutingResultCard 弹出："备用模型: gpt-4o，置信度 0.88"。

6. 接手 Agent（Coder #2）加载 Handoff Summary。
   → HandoffStatusIndicator: ready → accepted（▶）。
   → Coder #2 Card 边框变蓝，WorkerBadge 显示 ▶ running。
   → 原 Coder #1 Card 边框变灰，WorkerBadge 显示 ⏸ idle。

7. 接手 Worker 继续执行 Task #2。
   → Task #2 状态: handoff → running（蓝色呼吸）。
   → HandoffStatusIndicator: accepted → completed（✓）。
   → handoff_completed 日志写入。

8. Task #2 完成。
   → Task #2 状态: running → completed（绿色）。
   → HandoffStatusIndicator 消失。
```

### 5.3 错误处理流程（带状态可视化）

```text
1. Coder Agent 调用模型 API，返回 500 错误。
   → model_call 日志显示 ✗ failed。
   → error 日志写入。

2. Error Banner 弹出："⚠️ 错误: 模型调用失败 (500)"。
   → ExecutionLogPanel 自动展开，切换到 Error Logs。

3. Task #2 状态: running → failed（红色抖动）。
   → TaskCard 变红，显示错误信息和 [重试] [Handoff] 按钮。

4. 用户点击 [重试]。
   → Task #2 状态: failed → running（蓝色呼吸）。
   → Error Banner 消失。

5. 如果重试仍失败：
   → Task #2 状态: running → failed。
   → 系统提示："建议 Handoff 至备用模型"。
   → RoutingResultCard 弹出备用模型推荐。
```

---

## 6. 页面信息架构

### 6.1 信息架构图

```text
Agent Workspace
├── Top Status Bar（顶部状态栏）
│   ├── Goal 状态标签
│   ├── 进度条
│   ├── Token 计数
│   ├── Handoff 计数
│   ├── 耗时
│   └── Quota 预警条
│
├── GoalInputPanel（左侧）
│   ├── GoalInputForm
│   ├── RunConfigPanel
│   ├── TaskTree（带状态图标）
│   └── Final Summary（完成后）
│
├── AgentStationBoard（中间主视图）
│   ├── AgentStationCard（每个 Agent 一个）
│   │   ├── WorkerBadge（含 RiskBadge + RoutingResultBadge）
│   │   ├── TaskCard（当前任务，含 HandoffStatusIndicator）
│   │   └── 历史任务统计
│   ├── RoutingResultCard（路由决策浮层）
│   └── Handoff 对比视图
│
├── TaskDetailPanel（右侧 / 可展开）
│   ├── Overview Tab
│   ├── Task Tab
│   ├── Context Tab
│   ├── Logs Tab
│   ├── Handoff Tab
│   └── Quota Tab
│
└── ExecutionLogPanel（底部）
    ├── Event Log（含状态图标和颜色）
    ├── Model Calls
    ├── Handoff Records
    ├── Error Logs
    └── Token Usage Summary
```

### 6.2 状态联动矩阵

| 源模块 | 状态变化 | Workspace 联动组件 | 视觉表达 |
|--------|----------|-------------------|----------|
| Task Service | Task 状态变化 | TaskCard、TaskTree、Top Status Bar | 边框颜色、图标、动画 |
| Agent Runtime | Agent 状态变化 | AgentStationCard、WorkerBadge | 边框颜色、状态灯 |
| Model Router | 路由决策 | RoutingResultCard、WorkerBadge | 弹出卡片、置信度条 |
| Quota Manager | Quota 状态变化 | RiskBadge、Quota 预警条、TaskCard | 徽章颜色、顶部预警条 |
| Handoff Manager | Handoff 状态变化 | HandoffStatusIndicator、TaskCard、AgentStationCard | 旋转动画、进度条 |
| Logs Service | 新日志产生 | ExecutionLogPanel | 实时追加、自动滚动 |
| Supervisor | 审核结果 | TaskCard、ExecutionLogPanel | 审核标记、日志图标 |
| Goal Service | Goal 状态变化 | Top Status Bar、GoalInputPanel | 状态标签、进度条 |

---

## 7. 页面布局说明

### 7.1 整体布局

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Top Status Bar                                                               │
│ Goal: 实现用户认证系统 [planning ▶]  进度: 1/5  Token: 2.3k  耗时: 3m12s    │
├───────────────┬────────────────────────┬─────────────────────────────────────┤
│               │                        │                                     │
│ GoalInputPanel│   AgentStationBoard    │  TaskDetailPanel                    │
│   (左侧)      │     (中间主视图)        │   (右侧详情)                        │
│               │                        │                                     │
│ - Goal 输入   │  - Agent Station 网格   │  - Overview Tab                     │
│ - Run Config  │  - TaskCard 流         │  - Task Tab                         │
│ - Task Tree   │  - WorkerBadge         │  - Context Tab                      │
│               │  - HandoffIndicator    │  - Logs Tab                         │
│               │  - RoutingResultCard   │  - Handoff Tab                      │
│               │                        │  - Quota Tab                        │
│               │                        │                                     │
├───────────────┴────────────────────────┴─────────────────────────────────────┤
│ ExecutionLogPanel（底部，可收起/展开）                                        │
│ - Event Log / Model Calls / Handoff Records / Error Logs / Token Summary     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 布局原则

1. **顶部状态栏**：全局状态一眼可见，Goal 进度、Token、耗时、预警信息。
2. **中间为主**：AgentStationBoard 占据最大视觉区域，是用户观察协作过程的核心。
3. **左侧控制**：GoalInputPanel 固定左侧，提供输入和配置，Task Tree 实时反映任务状态。
4. **右侧详情**：TaskDetailPanel 默认收起或显示当前选中对象的轻量信息，点击后展开完整详情（含 Quota Tab 和 Handoff Tab）。
5. **底部日志**：ExecutionLogPanel 默认收起，只露出状态摘要条；出错时自动展开。
6. **状态优先**：任何状态变化都优先在对应组件上表达，不依赖用户主动查看日志。

### 7.3 响应式策略

- **宽屏（≥1440px）**：三栏布局，左右侧面板固定宽度，中间自适应。
- **中屏（1024-1439px）**：左右侧面板可折叠为图标栏，点击展开。
- **窄屏（<1024px）**：单栏布局，左右侧面板变为底部 Tab 或抽屉。

---

## 8. 核心组件设计

### 8.1 TopStatusBar

**职责**：展示 Goal 全局状态、进度、统计和预警。

**Props**：

```typescript
interface TopStatusBarProps {
  goal: Goal | null;
  tasks: Task[];
  handoffs: HandoffRecord[];
  quotaAlerts: QuotaAlert[];
  totalTokens: number;
  elapsedTimeMs: number;
  onStop: () => void;
  onViewQuota: () => void;
}

interface QuotaAlert {
  model_id: string;
  model_name: string;
  quota_status: QuotaStatus;
  usage_percent: number;
}
```

**状态标签样式**：

| GoalStatus | 标签样式 | 背景色 | 文字 |
|------------|----------|--------|------|
| idle | 灰色圆角标签 | `bg-gray-100 text-gray-600` | ⏸ idle |
| planning | 紫色圆角标签 + 脉冲 | `bg-purple-100 text-purple-700` | ✨ planning |
| running | 蓝色圆角标签 + 呼吸 | `bg-blue-100 text-blue-700` | ▶ running |
| handoff | 橙色圆角标签 + 旋转 | `bg-orange-100 text-orange-700` | 🔄 handoff |
| completed | 绿色圆角标签 | `bg-green-100 text-green-700` | ✓ completed |
| failed | 红色圆角标签 + 抖动 | `bg-red-100 text-red-700` | ✗ failed |

**预警条**：

- WARNING：黄色背景，⚠ 图标，可关闭。
- NEAR_LIMIT：橙色背景，🔴 图标，不可关闭。
- LIMITED/COOLDOWN：红色背景，✗ 图标，不可关闭，含操作按钮。

---

### 8.2 GoalInputPanel

**职责**：Goal 输入、运行配置、Task Tree 展示、Final Summary。

**Props**：

```typescript
interface GoalInputPanelProps {
  goal: Goal | null;
  tasks: Task[];
  onGoalSubmit: (input: GoalInput) => void;
  onGoalStart: () => void;
  onTaskSelect: (taskId: string) => void;
  selectedTaskId?: string;
  isRunning: boolean;
}
```

**TaskTree 状态图标**：

```
Task Tree
├── 🎯 Goal: 实现用户认证系统 [running]
│   ├── ⏸ Task #1: 设计数据库 [pending]
│   ├── ▶ Task #2: 实现登录组件 [running]
│   │   └── 🔄 Handoff #1: 额度耗尽交接 [completed]
│   ├── ⏳ Task #3: 实现注册组件 [waiting]
│   ├── ✓ Task #4: 编写测试 [completed]
│   └── 📋 Task #5: 文档编写 [assigned]
```

**状态图标映射**：

| TaskStatus | 图标 | 颜色 |
|------------|------|------|
| pending | ⏸ | 灰色 |
| assigned | 📋 | 灰色 |
| running | ▶ | 蓝色 |
| waiting | ⏳ | 黄色 |
| handoff | 🔄 | 紫色 |
| completed | ✓ | 绿色 |
| failed | ✗ | 红色 |

**行为**：

1. 用户输入 Goal 后，「开始」按钮可用。
2. 点击开始后，Goal 提交到后端，`onGoalSubmit` 触发。
3. Task Tree 在 Planner 拆解完成后自动更新，带状态图标。
4. 点击 Task Tree 中的 Task，`onTaskSelect` 触发，中间区域高亮对应 TaskCard。
5. Handoff 事件在 Task Tree 中以子节点展示。

---

### 8.3 AgentStationBoard

**职责**：展示所有 Agent Station、TaskCard、WorkerBadge、HandoffStatusIndicator 和 RoutingResultCard 的主视图区域。

**Props**：

```typescript
interface AgentStationBoardProps {
  goal: Goal | null;
  tasks: Task[];
  agents: AgentStation[];
  workers: WorkerSession[];
  models: Model[];
  handoffs: HandoffRecord[];
  routingResults: RoutingResult[];
  selectedEntityId?: string;
  onTaskSelect: (taskId: string) => void;
  onAgentSelect: (agentId: string) => void;
  onHandoffSelect: (handoffId: string) => void;
  onGenerateHandoff: (taskId: string) => void;
}
```

**布局**：

MVP 阶段使用卡片网格布局（Card Flow View），每个 Agent Station 对应一个卡片区域。

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Agent Station Board                                                          │
├─────────────────────────────┬─────────────────────────────┬──────────────────┤
│ 📝 Planner Station          │ 💻 Coder Station            │ 👁 Reviewer      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━  │ ━━━━━━━━━━━━━━━  │
│ [WorkerBadge]               │ [WorkerBadge]               │ [WorkerBadge]    │
│ 🤖 claude-3-5               │ 🤖 gpt-4o                   │ 🤖 gpt-4o-mini   │
│ ● done                      │ ● running                   │ ● idle           │
│ [🟢 normal]                 │ [🟢 normal]                 │ [🟢 normal]      │
│                             │                             │                  │
│ [TaskCard]                  │ [TaskCard]                  │ [TaskCard]       │
│ ✓ 拆解任务                  │ ▶ 实现登录组件              │ ⏸ 等待           │
│ completed                   │ running                     │ pending          │
│                             │ [🔄 HandoffIndicator]       │                  │
│ 历史: 1 完成                │ 历史: 12 完成 1 失败        │ 历史: 8 完成     │
├─────────────────────────────┴─────────────────────────────┴──────────────────┤
│ 📝 Summarizer Station       │ 🛡 Supervisor Station                         │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ [WorkerBadge]               │ [WorkerBadge]                                │
│ 🤖 kimi-k2                  │ 🤖 claude-3-5                                │
│ ● idle                      │ ● reviewing                                  │
│ [⚠️ unknown]                │ [🟢 normal]                                  │
│                             │                                              │
│ [TaskCard]                  │ [TaskCard]                                   │
│ ⏸ 等待                     │ 👁 最终审核                                   │
│ pending                     │ reviewing                                    │
│                             │                                              │
│ 历史: 3 完成                │ 历史: 5 完成                                 │
└─────────────────────────────┴────────────────────────────────────────────────┘
```

**行为**：

1. 根据 `tasks` 和 `agents` 渲染 Agent Station 卡片。
2. 每个 Agent Station 卡片显示当前 WorkerBadge（含 RiskBadge）。
3. 当前 Agent 对应的 TaskCard 显示在卡片内，含状态样式和 HandoffStatusIndicator。
4. Task 流转时，TaskCard 从一个 Agent Station 移动到下一个（或重新渲染，带过渡动画）。
5. Handoff 发生时，显示 HandoffStatusIndicator 和 Handoff 对比视图。
6. Model Router 做出决策时，弹出 RoutingResultCard。
7. 点击 TaskCard 触发 `onTaskSelect`。
8. 点击 Agent Station 触发 `onAgentSelect`。

---

### 8.4 TaskCard

**职责**：展示单个 Task 的状态、进度、输出、Worker、Quota 和 Handoff 状态。

**Props**：

```typescript
interface TaskCardProps {
  task: Task;
  agent: AgentStation;
  worker?: WorkerSession;
  model?: Model;
  handoff?: HandoffRecord;
  quotaRecord?: QuotaRecord;
  routingResult?: RoutingResult;
  status: TaskStatus;
  isSelected: boolean;
  onClick: () => void;
  onGenerateHandoff?: () => void;
  onRetry?: () => void;
}
```

**状态样式表**（同 4.3.1）：

| 状态 | 边框 | 背景 | 图标 | 动画 |
|------|------|------|------|------|
| pending | 灰色虚线 | 白色 | ⏸ | 无 |
| assigned | 灰色实线 | 白色 | 📋 | 无 |
| running | 蓝色实线 + 阴影 | `bg-blue-50` | ▶ | 呼吸动画 |
| waiting | 黄色实线 | `bg-yellow-50` | ⏳ | 无 |
| handoff | 紫色实线 + 阴影 | `bg-purple-50` | 🔄 | 旋转动画 |
| completed | 绿色实线 | `bg-green-50` | ✓ | 无 |
| failed | 红色实线 + 阴影 | `bg-red-50` | ✗ | 抖动动画 |

**完整展示**：

```
┌──────────────────────────────────────────────────────────────┐
│ [▶] Task #2: 实现登录组件                                    │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                              │
│ 状态: running (Step 3/5: 生成代码骨架)                       │
│ Agent: Coder Station                                         │
│ Worker: 🤖 gpt-4o  [RiskBadge: 🟢 normal]                    │
│ [RoutingResultBadge: 置信度 0.95]                            │
│                                                              │
│ 进度: ████████████████████░░░░  60%                         │
│                                                              │
│ 最新输出:                                                    │
│ ┌────────────────────────────────────────────────────────┐   │
│ │ 正在生成 React 组件...                                  │   │
│ │ ```tsx                                                 │   │
│ │ import React, { useState } from ...                    │   │
│ └────────────────────────────────────────────────────────┘   │
│                                                              │
│ Token: 3.2k  │  耗时: 2m15s  │  Step: 3/5                  │
│                                                              │
│ [HandoffStatusIndicator]                                     │
│ 🔄 Handoff in progress: requested → generating_summary      │
│                                                              │
│ [重试] [Handoff] [查看详情]                                 │
└──────────────────────────────────────────────────────────────┘
```

**行为**：

1. 根据 `status` 渲染对应颜色、边框、图标和动画。
2. 显示当前绑定的 Agent、Worker 模型名和 RiskBadge。
3. `running` 状态展示最新输出片段（截断），进度条实时更新。
4. `handoff` 状态展示 HandoffStatusIndicator，含状态进度条。
5. `failed` 状态展示错误提示和 [重试] / [Handoff] 按钮。
6. 点击打开 TaskDetailPanel。

---

### 8.5 WorkerBadge

**职责**：展示当前绑定到 Agent Station 的 Worker（模型实例）的完整状态，含 RiskBadge 和 RoutingResultBadge。

**Props**：

```typescript
interface WorkerBadgeProps {
  worker?: WorkerSession;
  model?: Model;
  quotaRecord?: QuotaRecord;
  routingResult?: RoutingResult;
  agentName: string;
  status: AgentStatus;
}
```

**状态灯**：

| Worker 状态 | 颜色 | 动画 | 说明 |
|-------------|------|------|------|
| idle | `bg-gray-400` | 无 | 未绑定任务 |
| running | `bg-blue-500` | 呼吸 | 正在执行 |
| handoff_required | `bg-purple-500` | 脉冲 | 需要交接 |
| completed | `bg-green-500` | 无 | 完成 |
| failed | `bg-red-500` | 闪烁 | 失败 |

**完整展示**：

```
┌──────────────────────────────────────────────┐
│ 🤖 gpt-4o                                    │
│ ● running                                    │
│                                              │
│ [RiskBadge: 🟢 normal]                       │
│ [RoutingResultBadge: 置信度 0.95]            │
│                                              │
│ Token: 3.2k / 1M  (使用率: 0.3%)            │
│ 调用次数: 15  延迟: 2.1s                    │
│                                              │
│ [查看额度] [切换模型]                       │
└──────────────────────────────────────────────┘
```

**行为**：

1. 展示模型名称和图标。
2. 展示状态灯（颜色 + 动画）。
3. 展示 RiskBadge（引用 Quota Manager PRD）。
4. 展示 RoutingResultBadge（引用 Model Router PRD）。
5. 展示 Token 消耗和额度使用率。
6. Worker 切换时（Handoff 后），Badge 更新为新模型，带过渡动画。

---

### 8.6 RoutingResultCard

**职责**：展示 Model Router 的路由决策结果。

**Props**：

```typescript
interface RoutingResultCardProps {
  routingResult: RoutingResult;
  onAccept: () => void;
  onOverride: (modelId: string) => void;
  onDismiss: () => void;
}

// 引用 Model Router PRD
interface RoutingResult {
  selected_model_id: string;
  selected_model_name: string;
  backup_model_ids: string[];
  routing_reason: string;
  confidence: number;
  risk_flags: string[];
  score_breakdown: {
    capability_match: number;
    role_match: number;
    context_fit: number;
    cost_fit: number;
    speed_fit: number;
    quota_health: number;
  };
}
```

**展示**：

```
┌──────────────────────────────────────────────────────────────┐
│ 🧭 Model Router 决策                              [×]      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ 推荐模型: gpt-4o                                             │
│ 置信度: ████████████████████░░░░  0.95                      │
│                                                              │
│ 评分拆解:                                                    │
│ ┌────────────────────────────────────────────────────────┐   │
│ │ capability_match  ████████████  0.25                   │   │
│ │ role_match        ██████████    0.20                   │   │
│ │ context_fit       ████████      0.15                   │   │
│ │ cost_fit          ████████      0.15                   │   │
│ │ speed_fit         █████         0.10                   │   │
│ │ quota_health      █████         0.10                   │   │
│ │ historical_perf   ███           0.05                   │   │
│ └────────────────────────────────────────────────────────┘   │
│                                                              │
│ 路由理由: "代码生成任务，GPT-4o 能力匹配度最高"              │
│                                                              │
│ [RiskFlagBanner]                                             │
│ ⚠️ 风险标记: near_quota_limit                               │
│                                                              │
│ 备用模型: claude-3-5, deepseek-chat                         │
│                                                              │
│ [接受] [切换模型] [查看详情]                                │
└──────────────────────────────────────────────────────────────┘
```

**RiskFlagBanner**：

| risk_flag | 颜色 | 图标 | 说明 |
|-----------|------|------|------|
| near_quota_limit | 橙色 | ⚠ | 推荐模型接近额度上限 |
| quota_unknown | 灰色 | ? | 无法判断额度状态 |
| backup_model_quota_low | 黄色 | ⚠ | 备用模型也不安全 |
| all_models_limited | 红色 | ✗ | 无可用的模型 |

**行为**：

1. 模型路由时自动弹出。
2. 用户可点击 [接受] 使用推荐模型。
3. 用户可点击 [切换模型] 手动选择备用模型。
4. 5 秒后自动收起（用户未操作时）。

---

### 8.7 HandoffStatusIndicator

**职责**：在 TaskCard 或 Agent Station 中展示 Handoff 的完整状态机。

**Props**：

```typescript
interface HandoffStatusIndicatorProps {
  handoff: HandoffRecord;
  fromAgent: AgentStation;
  toAgent: AgentStation;
  fromQuotaRecord?: QuotaRecord;
  toQuotaRecord?: QuotaRecord;
  onClick: () => void;
  onViewCompare: () => void;
  onCancel: () => void;
}
```

**状态样式**（同 4.7.1）：

| Handoff 状态 | 颜色 | 图标 | 动画 | 说明 |
|--------------|------|------|------|------|
| requested | 黄色 | 🔄 | 旋转 | 交接请求中 |
| generating_summary | 紫色 | ✍ | 脉冲 | 正在生成摘要 |
| ready | 紫色 | 📋 | 无 | 摘要已生成 |
| accepted | 蓝色 | ▶ | 无 | 已接受 |
| completed | 绿色 | ✓ | 无 | 交接完成 |
| failed | 红色 | ✗ | 抖动 | 交接失败 |

**状态进度条**：

```
Handoff 进度:
[requested] → [generating_summary] → [ready] → [accepted] → [completed]
   ✓            ✓                     ✓           ○            ○
```

**展示内容**：

```
┌──────────────────────────────────────────────────────────────┐
│ 🔄 Handoff in progress                                       │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                              │
│ 从: Coder #1 (claude-3-5)  [RiskBadge: 🔴 limited]          │
│ 到: Coder #2 (gpt-4o)      [RiskBadge: 🟢 normal]           │
│                                                              │
│ 原因: quota_exceeded                                         │
│                                                              │
│ 进度:                                                        │
│ [✓ requested] → [✍ generating_summary] → [○ ready]        │
│                                                              │
│ [查看摘要] [查看对比] [取消交接]                            │
└──────────────────────────────────────────────────────────────┘
```

**行为**：

1. Handoff 发生时，在相关 TaskCard 上显示 Indicator。
2. 状态变化时，进度条和图标同步更新。
3. 点击 [查看摘要] 打开 Handoff Summary。
4. 点击 [查看对比] 打开 Handoff 对比抽屉。
5. Handoff 完成后，Indicator 变为完成标记，3 秒后消失。

---

### 8.8 TaskDetailPanel

**职责**：展示选中 Task、Agent、Handoff 或 Quota 的详细信息。

**Props**：

```typescript
interface TaskDetailPanelProps {
  entityType: 'task' | 'agent' | 'handoff' | 'goal' | 'quota';
  entityId?: string;
  task?: Task;
  agent?: AgentStation;
  worker?: WorkerSession;
  model?: Model;
  handoff?: HandoffRecord;
  quotaRecord?: QuotaRecord;
  routingResult?: RoutingResult;
  goal?: Goal;
  logs: ExecutionLog[];
  onClose: () => void;
  onRetryTask?: (taskId: string) => void;
  onGenerateHandoff?: (taskId: string) => void;
}
```

**Tab 结构**：

```
TaskDetailPanel
├── Overview Tab
│   ├── 基本信息（名称、状态、优先级）
│   ├── 状态时间线（状态变化历史）
│   ├── 分配信息（Agent、Worker、模型）
│   └── 统计信息（Token、耗时、重试次数）
├── Task Tab
│   ├── 任务描述
│   ├── 完成标准
│   ├── 依赖任务
│   └── 输出内容
├── Context Tab
│   ├── Goal 原文
│   ├── 相关 Task
│   └── Handoff Summary（如果有）
├── Logs Tab
│   └── 该 Task/Agent 的执行日志（带状态图标）
├── Handoff Tab（仅当存在 Handoff 时）
│   ├── 交接原因
│   ├── 交接摘要
│   ├── 前后对比
│   └── 接手结果
├── Quota Tab（仅当涉及模型时）
│   ├── 额度状态
│   ├── 使用率
│   ├── 使用趋势
│   └── 状态变化历史
└── Router Tab（仅当存在路由决策时）
    ├── 推荐模型
    ├── 评分拆解
    ├── 风险标记
    └── 备用模型
```

**行为**：

1. 点击 TaskCard 或 Agent Station 时，面板展开并展示对应详情。
2. 未选中任何对象时，展示 Goal 概览或空状态提示。
3. Task failed 时，显示 Retry 和 Generate Handoff 按钮。
4. Handoff 存在时，自动高亮 Handoff Tab。
5. Quota 异常时，自动高亮 Quota Tab。

---

### 8.9 ExecutionLogPanel

**职责**：展示 Goal 执行全过程的日志、模型调用、Handoff、Quota 变化和错误。

**Props**：

```typescript
interface ExecutionLogPanelProps {
  logs: ExecutionLog[];
  goalId?: string;
  selectedTaskId?: string;
  selectedAgentId?: string;
  onTaskClick?: (taskId: string) => void;
  onAgentClick?: (agentId: string) => void;
  onHandoffClick?: (handoffId: string) => void;
  onErrorClick?: (logId: string) => void;
}
```

**Tab 结构**：

```
ExecutionLogPanel
├── Event Log（综合事件，带状态图标和颜色）
│   └── model_call / agent_step / tool_call / task_status_change /
│       quota_status_change / handoff_created / handoff_completed /
│       error / supervisor_review / memory_write_candidate
├── Model Calls（模型调用详情，含 token 和延迟）
├── Handoff Records（交接记录，含前后对比入口）
├── Quota Changes（额度状态变化历史）
├── Error Logs（错误日志，红色高亮）
└── Token Summary（Token 使用统计）
```

**日志行样式**：

```
时间    图标  类型              状态      Agent    Model    Task    摘要
─────────────────────────────────────────────────────────────────────────
10:07   ✓   task_status       completed -        -        Task#3  运行→完成
10:06   ✓   supervisor_review approved  Reviewer -        Task#3  审核通过
10:05   🔄  handoff_created   created   Coder→   claude→  Task#2  额度耗尽
        │                       │       Coder    gpt-4o
10:04   ⚡  quota_status      transition -       gpt-4    -       normal→LIMITED
10:03   ✗   model_call        failed    Coder    claude   Task#2  429错误
10:02   ✓   tool_call         completed Coder    -        Task#2  文件写入
10:01   ✓   model_call        completed Coder    gpt-4o   Task#2  2.3k tokens
10:00   ✓   agent_step        completed Planner  claude   -       拆解完成
```

**默认状态**：

收起时只展示摘要条：

```
Running · 12 Model Calls · 5 Tasks · 1 Handoff · 1 Quota Alert · 0 Errors [展开 ▲]
```

**行为**：

1. 实时追加新日志（WebSocket/SSE 或轮询），新日志高亮 2 秒后恢复正常。
2. 出错时自动展开并切换到 Error Logs Tab。
3. Handoff 事件以紫色标签展示，点击打开 Handoff 对比。
4. Quota 变化以闪电图标展示，点击打开 Quota Detail。
5. 点击日志中的 Task ID 或 Agent ID，高亮对应 TaskCard 或 Agent Station。
6. 支持关键词搜索和类型筛选。

---

### 8.10 RiskBadge（额度风险徽章）

引用 Quota Manager PRD 的 Risk Badge 定义。

**展示**：

```
┌──────────────┐
│ [🟢 normal]  │
│ [⚠️ warning] │
│ [🔴 near_limit]│
│ [✗ limited]  │
│ [⏱ cooldown] │
│ [? unknown]  │
└──────────────┘
```

**位置**：

- WorkerBadge 中（模型实例旁）。
- TaskCard 中（Worker 信息旁）。
- TaskDetailPanel 的 Quota Tab 中。
- Top Status Bar 的 Quota 预警条中。

---

## 9. 前端状态设计

### 9.1 状态定义

以下状态分别属于不同实体，共同构成 Workspace 的完整状态机。

#### 9.1.1 Goal 状态

```typescript
type GoalStatus =
  | 'idle'        // 刚创建，未启动
  | 'planning'    // Planner 正在拆解 Task
  | 'running'     // Task 正在执行
  | 'waiting'     // 等待用户输入或外部条件
  | 'handoff'     // 存在进行中的 Handoff
  | 'reviewing'   // Supervisor 正在审核
  | 'completed'   // 所有 Task 完成，Supervisor 已汇总
  | 'failed';     // 任务失败，无法继续
```

#### 9.1.2 Task 状态

```typescript
type TaskStatus =
  | 'pending'      // 等待分配
  | 'assigned'     // 已分配给 Agent，未开始
  | 'running'      // 正在执行
  | 'waiting'      // 等待依赖完成
  | 'handoff'      // 正在交接
  | 'completed'    // 完成
  | 'failed';      // 失败
```

#### 9.1.3 Agent Station 状态

```typescript
type AgentStatus =
  | 'idle'         // 空闲，无当前任务
  | 'queued'       // 有任务排队
  | 'running'      // 正在执行任务
  | 'waiting'      // 等待依赖或输入
  | 'reviewing'    // 审查中（Reviewer / Supervisor）
  | 'handoff'      // 正在交接
  | 'blocked'      // 被阻塞
  | 'error'        // 出错
  | 'done';        // 当前任务完成
```

#### 9.1.4 Worker Session 状态

```typescript
type WorkerStatus =
  | 'idle'              // 未绑定任务
  | 'running'           // 正在执行
  | 'handoff_required'  // 需要交接
  | 'completed'         // 完成
  | 'failed';           // 失败
```

#### 9.1.5 Handoff 状态

引用 Handoff Manager PRD：

```typescript
type HandoffStatus =
  | 'requested'          // 交接请求已创建
  | 'generating_summary' // 正在生成交接摘要
  | 'ready'              // 摘要已生成，等待接受
  | 'accepted'           // 接手 Agent 已接受
  | 'completed'          // 交接完成，新 Worker 开始执行
  | 'failed';            // 交接失败
```

#### 9.1.6 Quota 状态

引用 Quota Manager PRD：

```typescript
type QuotaStatus =
  | 'normal'      // 正常
  | 'warning'     // 注意
  | 'near_limit'  // 接近限制
  | 'limited'     // 已受限
  | 'cooldown'    // 冷却中
  | 'unknown';    // 未知
```

### 9.2 状态流转图

#### Goal 状态流转

```text
idle
↓ 用户点击开始
planning
↓ Planner 拆解完成
running
↓ 所有 Task 完成
reviewing
↓ Supervisor 审核完成
completed

running → handoff → running
running → waiting → running
running → failed
planning → failed
```

#### Task 状态流转

```text
pending
↓ 分配给 Agent
assigned
↓ Agent 开始执行
running
↓ 完成
completed

running → waiting（等待依赖）
waiting → running（依赖完成）
running → handoff → running
running → failed
handoff → failed
```

#### Agent Station 状态流转

```text
idle
↓ 收到 Task
running
↓ Task 完成
done
↓ 无新 Task
idle

running → handoff（触发交接）
handoff → idle（原 Agent 释放）
handoff → running（接手 Agent）
running → error → blocked
blocked → running（Retry）
```

#### Handoff 状态流转

```text
requested
↓ 开始生成摘要
generating_summary
↓ 摘要生成完成
ready
↓ 接手 Agent 接受
accepted
↓ 新 Worker 开始执行
completed

ready → failed（无人接受/超时）
generating_summary → failed（摘要生成失败）
```

### 9.3 前端状态管理

推荐使用集中式状态管理（如 Zustand、Redux Toolkit 或 Vue Pinia），核心 State 结构：

```typescript
interface WorkspaceState {
  // 核心实体
  goal: Goal | null;
  tasks: Task[];
  agents: AgentStation[];
  workers: WorkerSession[];
  models: Model[];
  handoffs: HandoffRecord[];
  quotaRecords: QuotaRecord[];
  routingResults: RoutingResult[];
  logs: ExecutionLog[];

  // UI 状态
  selectedEntity: {
    type: 'task' | 'agent' | 'handoff' | 'goal' | 'quota' | null;
    id: string | null;
  };
  isRunning: boolean;
  viewMode: 'card-flow' | 'pixel-office';
  error: string | null;

  // 实时状态
  quotaAlerts: QuotaAlert[];
  activeHandoffs: HandoffRecord[];
  latestRoutingResult: RoutingResult | null;
  latestError: ErrorLog | null;
}
```

状态更新原则：

1. 后端推送或轮询获取增量更新。
2. 前端只更新变化的部分，不全局重新渲染。
3. Task、Agent、Worker、Handoff、Quota 状态变化时，对应组件自动响应。
4. 选中状态（selectedEntity）变化时，TaskDetailPanel 更新。
5. Quota 状态变化时，RiskBadge 和 Quota 预警条同步更新。
6. Handoff 状态变化时，HandoffStatusIndicator 和 TaskCard 同步更新。

---

## 10. 后端接口设计

### 10.1 Workspace 聚合接口

```http
GET /workspace/:goalId/state
```

响应：

```json
{
  "success": true,
  "data": {
    "goal": { ... },
    "tasks": [ ... ],
    "agents": [ ... ],
    "workers": [ ... ],
    "models": [ ... ],
    "handoffs": [ ... ],
    "quotaRecords": [ ... ],
    "routingResults": [ ... ],
    "logs": [ ... ]
  }
}
```

### 10.2 实时更新接口

MVP-A 使用轮询：

```http
GET /workspace/:goalId/state?since=:timestamp
```

返回自 `since` 时间戳以来的增量更新。

MVP-B 使用 WebSocket / SSE：

```
ws://localhost:8000/ws/workspace
```

推送消息类型：

- `task_status_updated` — Task 状态变化
- `agent_status_updated` — Agent 状态变化
- `worker_status_updated` — Worker 状态变化
- `handoff_status_updated` — Handoff 状态变化
- `quota_status_updated` — Quota 状态变化
- `routing_result_available` — 路由决策可用
- `new_log` — 新日志产生
- `goal_progress_updated` — Goal 进度更新
- `error_occurred` — 错误发生

### 10.3 其他接口

| 接口 | 说明 | 来源 |
|------|------|------|
| `POST /goals` | 创建 Goal | Goal Service |
| `POST /goals/:goalId/start` | 启动 Goal | Goal Service |
| `GET /goals/:goalId` | 获取 Goal 详情 | Goal Service |
| `GET /goals/:goalId/tasks` | 获取 Task 列表 | Task Service |
| `GET /tasks/:taskId` | 获取 Task 详情 | Task Service |
| `POST /tasks/:taskId/run` | 重跑 Task | Task Service |
| `GET /agents` | 获取 Agent 列表 | Agent Registry |
| `GET /agents/:agentId` | 获取 Agent 详情 | Agent Registry |
| `POST /tasks/:taskId/handoff` | 触发 Handoff | Handoff Manager |
| `GET /handoffs` | 获取 Handoff 列表 | Handoff Manager |
| `GET /handoffs/:handoffId` | 获取 Handoff 详情 | Handoff Manager |
| `GET /quota/models/:modelId/status` | 获取额度状态 | Quota Manager |
| `GET /quota/overview` | 获取额度概览 | Quota Manager |
| `GET /logs` | 获取日志 | Logs Service |
| `GET /logs/task/:taskId/timeline` | 获取 Task 时间线 | Logs Service |
| `POST /router/select-model` | 模型路由 | Model Router |

---

## 11. 数据对象设计

### 11.1 Workspace 渲染专用类型

```typescript
// 核心 Workspace 状态
interface WorkspaceState {
  goal: Goal | null;
  tasks: Task[];
  agents: AgentStation[];
  workers: WorkerSession[];
  models: Model[];
  handoffs: HandoffRecord[];
  quotaRecords: QuotaRecord[];
  routingResults: RoutingResult[];
  logs: ExecutionLog[];
  selectedEntityId?: string;
  selectedEntityType?: 'task' | 'agent' | 'handoff' | 'goal' | 'quota';
}

// Goal
interface Goal {
  id: string;
  title: string;
  description: string;
  status: GoalStatus;
  progress: number;
  priority: 'low' | 'medium' | 'high';
  total_tasks: number;
  completed_tasks: number;
  handoff_count: number;
  total_tokens_used: number;
  final_summary?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

// Task
interface Task {
  id: string;
  goal_id: string;
  parent_task_id?: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: 'low' | 'medium' | 'high';
  assigned_agent_id?: string;
  assigned_worker_id?: string;
  dependencies: string[];
  output?: string;
  completion_criteria?: string;
  tokens_used: number;
  duration_ms: number;
  handoff_count: number;
  step_number?: number;
  total_steps?: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

// Agent Station
interface AgentStation {
  id: string;
  name: string;
  role: 'planner' | 'coder' | 'reviewer' | 'research' | 'summarizer' | 'supervisor';
  description: string;
  status: AgentStatus;
  current_task_id?: string;
  default_model_id: string;
  backup_model_ids: string[];
  system_prompt: string;
  max_steps_per_task: number;
  allow_handoff: boolean;
  total_tasks_completed: number;
  total_tasks_failed: number;
}

// Worker Session
interface WorkerSession {
  id: string;
  agent_id: string;
  model_id: string;
  goal_id: string;
  task_id: string;
  inherited_from_handoff_id?: string;
  status: WorkerStatus;
  current_context?: string;
  final_output?: string;
  error_message?: string;
  input_tokens_used: number;
  output_tokens_used: number;
  total_tokens_used: number;
  started_at: string;
  completed_at?: string;
}

// Model
interface Model {
  id: string;
  provider: string;
  model_name: string;
  display_name: string;
  capability_tags: string[];
  max_context_tokens: number;
  cost_level: number;
  speed_level: number;
  is_enabled: boolean;
}

// Handoff Record（引用 Handoff Manager PRD）
interface HandoffRecord {
  id: string;
  goal_id: string;
  task_id: string;
  from_agent_id: string;
  from_model_id: string;
  to_agent_id: string;
  to_model_id: string;
  reason: string;
  reason_description?: string;
  handoff_summary: {
    original_goal: string;
    current_task: string;
    completed_work: string[];
    unfinished_work: string[];
    important_constraints: string[];
    key_decisions: string[];
    errors_and_risks: string[];
    next_suggested_steps: string[];
    context_needed: string[];
  };
  status: HandoffStatus;
  result_after_handoff?: 'success' | 'failed' | 'partial';
  tokens_before_handoff: number;
  tokens_after_handoff: number;
  created_at: string;
  accepted_at?: string;
  completed_at?: string;
}

// Quota Record（引用 Quota Manager PRD）
interface QuotaRecord {
  quota_record_id: string;
  provider: string;
  model_id: string;
  model_name: string;
  request_count: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  last_used_at: string;
  estimated_remaining: number;
  quota_status: QuotaStatus;
  limit_error_count: number;
  cooldown_until?: string;
  handoff_triggered_count: number;
  updated_at: string;
  usage_percent: number;
  quota_mode: 'known' | 'estimated' | 'unknown';
  token_limit?: number;
}

// Routing Result（引用 Model Router PRD）
interface RoutingResult {
  selected_model_id: string;
  selected_model_name: string;
  backup_model_ids: string[];
  routing_reason: string;
  confidence: number;
  risk_flags: string[];
  score_breakdown: {
    capability_match: number;
    role_match: number;
    context_fit: number;
    cost_fit: number;
    speed_fit: number;
    quota_health: number;
  };
}

// Execution Log（引用 Logs PRD）
interface ExecutionLog {
  log_id: string;
  goal_id?: string;
  task_id?: string;
  agent_id?: string;
  worker_id?: string;
  model_id?: string;
  event_type: string;
  event_status: string;
  input_summary?: string;
  output_summary?: string;
  token_usage?: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
  quota_status?: string;
  handoff_status?: string;
  tool_name?: string;
  error_message?: string;
  created_at: string;
  metadata?: Record<string, any>;
}
```

### 11.2 组件间数据流

```text
WorkspaceState
├── TopStatusBar ← goal, tasks, handoffs, quotaAlerts, totalTokens
├── GoalInputPanel ← goal, tasks, isRunning
│   └── TaskTree ← tasks（含状态图标）
├── AgentStationBoard ← tasks, agents, workers, models, handoffs, quotaRecords, routingResults
│   ├── AgentStationCard ← agent, worker, model, quotaRecord
│   │   ├── WorkerBadge ← worker, model, quotaRecord, routingResult
│   │   │   └── RiskBadge ← quotaRecord
│   │   │   └── RoutingResultBadge ← routingResult
│   │   └── TaskCard ← task, agent, worker, model, handoff, quotaRecord
│   │       └── HandoffStatusIndicator ← handoff, fromAgent, toAgent
│   └── RoutingResultCard ← routingResult
├── TaskDetailPanel ← selectedEntity, task, agent, worker, model, handoff, quotaRecord, routingResult, goal, logs
│   ├── Overview Tab
│   ├── Task Tab
│   ├── Context Tab
│   ├── Logs Tab ← logs
│   ├── Handoff Tab ← handoff
│   ├── Quota Tab ← quotaRecord
│   └── Router Tab ← routingResult
└── ExecutionLogPanel ← logs, goalId, selectedTaskId, selectedAgentId
    ├── Event Log
    ├── Model Calls
    ├── Handoff Records
    ├── Quota Changes
    ├── Error Logs
    └── Token Summary
```

---

## 12. 异常状态

### 12.1 Goal 启动失败

**触发条件**：

- Planner 模型调用失败。
- Goal 描述为空或无效。
- 没有可用的 Agent。

**可视化处理**：

- Top Status Bar: idle → failed（红色标签 + 抖动动画）。
- GoalInputPanel: 显示错误提示，「开始」按钮恢复可用。
- ExecutionLogPanel: 自动展开，展示 error 日志。
- Error Banner: 弹出，说明失败原因。

### 12.2 Task 执行失败

**触发条件**：

- 模型调用失败（429/500/timeout）。
- 输出为空或格式错误。
- 达到 max_steps_per_task 限制。

**可视化处理**：

- TaskCard: running → failed（红色边框 + 抖动动画）。
- AgentStationCard: running → error（红色边框）。
- WorkerBadge: running → failed（红色状态灯 + 闪烁）。
- TaskDetailPanel: 显示 Retry 和 Generate Handoff 按钮。
- ExecutionLogPanel: 自动展开，切换到 Error Logs。
- Error Banner: 弹出，显示错误信息和建议操作。
- 如果错误是额度相关，RiskBadge 同步更新为 LIMITED/COOLDOWN。

### 12.3 Handoff 失败

**触发条件**：

- 接手 Agent 不可用。
- 接手模型额度不足或连接失败。
- Handoff Summary 生成失败。

**可视化处理**：

- HandoffStatusIndicator: accepted → failed（红色 + 抖动）。
- TaskCard: handoff → failed（红色）。
- AgentStationCard: handoff → error（红色）。
- Workspace 提示用户重新选择接手 Agent。
- Error Banner: 弹出，说明 Handoff 失败原因。
- 原 Task 可以 Retry 或重新 Handoff。

### 12.4 模型额度不足

**触发条件**：

- Quota Manager 检测到 token 或请求数达到阈值。

**可视化处理**：

- RiskBadge: normal → warning（黄色）→ near_limit（橙色）→ limited（红色）。
- Quota 预警条: 弹出（黄色/橙色/红色）。
- WorkerBadge: 显示额度警告。
- TaskCard: 显示 HandoffStatusIndicator（建议交接）。
- 如果是 auto_handoff，自动触发 Handoff 流程，HandoffStatusIndicator 出现。
- 如果是 manual，提示用户手动触发 Handoff。

### 12.5 长时间无响应

**触发条件**：

- 模型调用超过超时时间（如 60 秒）。
- Worker 状态长时间停留在 running 无输出。

**可视化处理**：

- WorkerBadge: running → blocked（橙色状态灯）。
- TaskCard: 显示超时提示（"已等待 60 秒..."）。
- ExecutionLogPanel: 记录 timeout 错误。
- 用户可以选择 Retry 或 Handoff。

### 12.6 前端状态与后端不一致

**触发条件**：

- 网络中断导致状态更新丢失。
- 轮询间隔内发生多次状态变化。

**可视化处理**：

- Top Status Bar: 显示 "Syncing..." 提示。
- 前端在重新连接后全量刷新 WorkspaceState。
- 使用 `GET /workspace/:goalId/state` 重新同步。
- 同步完成后，"Syncing..." 消失。

---

## 13. MVP 范围

### 13.1 MVP-A 必须实现

| 功能 | 说明 | 状态可视化 |
|------|------|-----------|
| TopStatusBar | Goal 状态、进度、Token、Handoff 计数、耗时 | GoalStatus 标签 + 进度条 + 数字 |
| GoalInputPanel | Goal 输入、启动按钮、Task Tree | TaskStatus 图标 + 颜色 |
| AgentStationBoard | 卡片网格，展示 Agent Station | AgentStatus 边框 + WorkerBadge |
| TaskCard | Task 状态、Agent、Worker、输出 | TaskStatus 边框/背景/图标/动画 |
| WorkerBadge | Worker 模型名和状态灯 | WorkerStatus 状态灯颜色 |
| RiskBadge | 额度状态徽章 | QuotaStatus 颜色 + 图标 |
| HandoffStatusIndicator | Handoff 状态和进度 | HandoffStatus 颜色 + 图标 + 动画 |
| RoutingResultCard | 路由决策展示 | 置信度条 + 评分拆解 + RiskFlagBanner |
| TaskDetailPanel | Task/Agent/Handoff 详情 | 状态时间线 + Tab 切换 |
| ExecutionLogPanel | 底部日志面板 | 日志类型图标 + 状态颜色 |
| Quota 预警条 | 顶部额度预警 | QuotaStatus 颜色 + 操作按钮 |
| Error Banner | 错误提示 | 红色 + 操作按钮 |
| 状态联动 | 任一模块状态变化，相关组件同步更新 | 全系统联动 |
| Goal → Task → Agent → Worker → Model → Router → Quota → Handoff → Logs 闭环 | 完整流程可跑通 | 全流程状态可见 |
| 轮询状态同步 | 定时刷新 WorkspaceState | 增量更新 |

### 13.2 MVP-B 建议实现

| 功能 | 说明 | 状态可视化 |
|------|------|-----------|
| WebSocket/SSE 实时更新 | 推送状态变化，替代轮询 | 实时更新，无延迟 |
| Handoff 对比视图 | Handoff 前后上下文对比 | 左右对比 + 上下文损失 |
| Quota Tab | TaskDetailPanel 中展示额度详情 | 使用率条 + 状态历史 |
| Router Tab | TaskDetailPanel 中展示路由详情 | 评分矩阵 + 风险标记 |
| Token Usage Summary | 各 Agent/Model 的 token 统计 | 图表 |
| 任务依赖可视化 | Task Tree 中展示依赖关系 | 连线 + 状态图标 |
| 搜索/筛选日志 | ExecutionLogPanel 支持筛选 | 类型图标 + 状态颜色 |
| Pixel Office 静态视图 | 固定工位 + Worker + 状态灯 | 状态灯 + 徽章 |
| 动画优化 | 状态变化过渡动画 | 300ms 过渡 |

---

## 14. 暂缓范围

当前阶段明确不做：

1. **通用聊天对话界面**：不是 ChatGPT clone。
2. **把 Agent 等同于模型选择器**：Agent 是角色工位，模型是 Worker。
3. **复杂像素办公室动画**：MVP 只做静态或极简表达，不做角色行走、复杂场景动画。
4. **拖拽式工作流编辑器**：不做 DAG 编排，Task 流转由后端控制。
5. **多人实时协作**：单用户本地使用。
6. **完全自动执行无确认**：所有 Handoff 和重试需要用户确认或可见。
7. **3D 场景或游戏化交互**：保持专业工具感。
8. **自定义布局系统**：Agent Station 位置固定，不做拖拽重排。
9. **语音输入/输出**：纯文本交互。

---

## 15. 验收标准

### 15.1 功能验收

1. 用户可以在 GoalInputPanel 输入 Goal 并点击开始。
2. Planner 拆解完成后，Task Tree 和 AgentStationBoard 同步更新，TaskStatus 图标正确。
3. AgentStationBoard 中每个 Agent Station 展示当前 WorkerBadge，含状态灯。
4. TaskCard 根据 Task 状态显示正确的颜色、边框、图标和动画。
5. Task 在不同 Agent 之间流转时，TaskCard 位置或归属正确更新，状态变化可见。
6. Model Router 做出决策时，RoutingResultCard 正确弹出，展示置信度和评分拆解。
7. Handoff 发生时，HandoffStatusIndicator 在相关 TaskCard 上可见，状态进度正确。
8. Quota 状态变化时，RiskBadge 同步更新，Quota 预警条正确弹出。
9. 点击 TaskCard 后，TaskDetailPanel 展示完整的 Task 详情（含 Handoff Tab 和 Quota Tab）。
10. ExecutionLogPanel 可以展示 Event、Model Call、Handoff、Quota Change 和 Error 日志，带状态图标。
11. Goal 完成后，Workspace 展示 Final Summary，Top Status Bar 显示 completed。
12. 错误发生时，Error Banner 弹出，TaskCard 变红，ExecutionLogPanel 自动展开。

### 15.2 状态验收

1. Goal 状态可以从 idle → planning → running → reviewing → completed，每个状态在 Top Status Bar 有对应视觉表达。
2. Task 状态可以从 pending → assigned → running → waiting → handoff → completed，每个状态在 TaskCard 有对应颜色、图标、动画。
3. Agent Station 状态可以随 Task 变化：idle → running → handoff → done → idle，每个状态在 AgentStationCard 有对应边框颜色。
4. WorkerBadge 可以随 Handoff 从模型 A 切换到模型 B，RiskBadge 同步更新。
5. HandoffStatusIndicator 可以完整展示 requested → generating_summary → ready → accepted → completed 的状态流转。
6. RiskBadge 可以完整展示 normal → warning → near_limit → limited → cooldown → unknown 的状态变化。
7. RoutingResultCard 可以展示置信度条、评分拆解矩阵和风险标记。
8. Task failed 时，TaskCard 变红，WorkerBadge 状态灯变红闪烁，Error Banner 弹出。

### 15.3 数据验收

1. WorkspaceState 可以聚合 Goal、Task、Agent、Worker、Model、Handoff、Quota、RoutingResult、Log。
2. TaskCard 的 `assigned_agent_id`、`assigned_worker_id` 与后端一致。
3. WorkerBadge 展示的模型名与 `model_id` 对应，RiskBadge 与 QuotaRecord 一致。
4. HandoffStatusIndicator 的 `handoff_id` 与 HandoffRecord 一致。
5. RoutingResultCard 的评分与 Model Router 返回一致。
6. ExecutionLog 的 `task_id`、`agent_id`、`worker_id` 可以关联到对应实体。

### 15.4 Demo 验收

必须能稳定演示以下流程：

```text
1. 用户进入 Agent Workspace。
   → Top Status Bar 显示 idle。

2. 输入 Goal："帮我设计一个前端页面"。
   → 输入框有内容，「开始」按钮可用。

3. 点击开始。
   → Top Status Bar: idle → planning（紫色标签）。
   → GoalInputPanel 显示 planning 动画。

4. Planner Agent Station 激活，WorkerBadge 显示模型名和状态灯。
   → AgentStationBoard 中 Planner Card 边框变蓝，WorkerBadge 显示 ▶ running（蓝色呼吸）。
   → RoutingResultCard 弹出："Planner 路由决策：claude-3-5，置信度 0.92"。

5. Task Tree 生成 3-5 个 Task。
   → Task Tree 中每个 Task 显示对应状态图标（pending: ⏸ 灰色）。
   → Top Status Bar: planning → running（蓝色标签）。

6. AgentStationBoard 出现对应 TaskCard。
   → Coder Agent 的 TaskCard 状态 assigned → running（蓝色呼吸）。
   → Coder WorkerBadge 显示 ▶ running。

7. Coder 输出内容展示在 TaskCard 上。
   → TaskCard 显示最新输出片段，Token 计数实时更新。
   → ExecutionLogPanel 追加 model_call 和 agent_step 日志。

8. Coder 完成，Task 流转给 Reviewer。
   → TaskCard 状态 running → completed（绿色）。
   → Coder WorkerBadge 显示 ✓ done（绿色）。
   → Reviewer TaskCard 状态 pending → running（蓝色呼吸）。

9. 用户手动触发一次 Handoff。
   → TaskCard 状态 running → handoff（紫色旋转）。
   → HandoffStatusIndicator 显示 requested → generating_summary → ready。
   → Handoff 对比视图可打开。

10. 接手 Agent 继续执行，TaskCard 重新变蓝（running）。
    → HandoffStatusIndicator 显示 accepted → completed（绿色）。
    → 原 WorkerBadge 变 idle（灰色），新 WorkerBadge 变 running（蓝色）。

11. Supervisor 完成最终审查，Goal 完成。
    → Top Status Bar: running → reviewing → completed（绿色标签）。
    → GoalInputPanel 显示 Final Summary。

12. ExecutionLogPanel 展示完整执行过程，每条日志有对应图标和颜色。
    → 点击任意日志，可查看详情。

13. 点击任意 TaskCard，TaskDetailPanel 展示详情（含 Handoff Tab 和 Quota Tab）。

14. 整个过程中，任何状态变化都有对应的视觉表达（颜色、图标、动画）。
```

如果上述流程可稳定跑通，且每个状态变化都有对应的视觉表达，Agent Workspace MVP 即视为完成。

---

> 文档版本：v2.0（状态可视化增强版）
>
> 最后更新：2026-06-25
>
> 相关文档：
> - `docs/prd/model-router-prd.md` — Model Router 决策可视化
> - `docs/prd/handoff-manager-prd.md` — Handoff 状态机和对比视图
> - `docs/prd/quota-manager-prd.md` — Quota 状态定义和 Risk Badge
> - `docs/prd/agent-registry-prd.md` — Agent Station 配置
> - `docs/prd/logs-observability-prd.md` — ExecutionLog 类型和图标
