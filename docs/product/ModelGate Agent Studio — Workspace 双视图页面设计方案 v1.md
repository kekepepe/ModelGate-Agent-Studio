# ModelGate Agent Studio — Workspace 双视图页面设计方案 v1

## 1. Workspace 核心定位

Workspace 是 ModelGate Agent Studio 的核心工作区。

它不是普通聊天页面，也不是单纯的后台管理页面，而是一个可以让用户看到：

* 当前 Goal 是什么
* Goal 被拆成了哪些 Task
* 哪些 Agent 正在工作
* 每个 Agent 由哪个模型驱动
* 任务流转到哪里了
* 哪些 Agent 已完成、等待、出错或交接
* 模型额度是否影响任务推进
* Handoff 是否发生
* 最终结果如何被 Supervisor 审查

Workspace 采用双视图设计：

1. **Card Flow View：卡片任务流视图**
2. **Pixel Office View：像素办公室视图**

默认进入 Workspace 时，展示  **Card Flow View** 。用户可以通过顶部按钮一键切换到  **Pixel Office View** 。

---

## 2. 双视图设计原则

两个视图的展示方式不同，但底层数据必须一致。

也就是说：

```text
不是两套任务系统
不是两套 Agent 系统
不是两套运行逻辑
而是一套 Workspace State + 两套 Renderer
```

底层共享：

```text
Goal
Task Tree
Agent Sessions
Worker Sessions
Model Binding
Task Edges
Handoff Events
Execution Logs
Quota Status
Memory Usage
Skill Usage
```

视图不同：

```text
Card Flow View：
更偏效率、清晰、任务流、状态判断。

Pixel Office View：
更偏沉浸、识别度、Agent 工位、动画表达。
```

---

## 3. Workspace 页面整体结构

取消固定右侧详情面板。

Workspace 主结构：

```text
┌──────────────────────────────────────────────────────────────┐
│ Top Bar：项目 / Goal / Run 状态 / 视图切换 / 模型额度          │
├───────────────┬──────────────────────────────────────────────┤
│ 左侧控制区     │ 中间 Workspace 主视图                         │
│ Goal 输入      │ Card Flow View / Pixel Office View             │
│ 任务树         │                                              │
│ 运行配置       │                                              │
├───────────────┴──────────────────────────────────────────────┤
│ Bottom Console：执行日志 / 模型调用 / 工具调用 / 错误信息       │
└──────────────────────────────────────────────────────────────┘
```

页面区域说明：

### 3.1 Top Bar

显示：

* 当前项目名称
* 当前 Goal 标题
* 当前运行状态
* 正在工作的 Agent 数量
* 模型额度概览
* 当前视图切换按钮
* Pause / Resume / Stop
* Export Summary

示例：

```text
ModelGate Agent Studio
Goal: 设计 Workspace 双视图
Running · 3 Agents Active · 1 Handoff
[Card Flow] [Pixel Office]
```

### 3.2 左侧控制区

左侧控制区在两个视图中保持一致。

包含：

1. Goal Input
2. Run Config
3. Task Tree

结构：

```text
Goal
帮我设计 Workspace 双视图页面

Run Config
- Agent Team Mode: ON
- Auto Handoff: ON
- Auto Model Switch: ON
- Tool Call: Ask First
- Run Depth: Standard

Task Tree
- Task #1 分析需求
- Task #2 设计卡片视图
- Task #3 设计像素视图
- Task #4 设计状态系统
- Task #5 Supervisor 审查
```

点击 Task Tree 中的任务时：

* 在 Card Flow View 中，高亮对应 Agent Card 和 Task Edge
* 在 Pixel Office View 中，高亮对应工位和 Worker

### 3.3 中间主视图

中间区域根据用户选择展示：

```text
Card Flow View
或
Pixel Office View
```

这是 Workspace 的主视觉区域。

### 3.4 Bottom Console

底部日志区域两个视图共用。

默认收起，只露出简短运行状态。

默认状态：

```text
Running · 12 Model Calls · 4 Tool Calls · 1 Handoff · 0 Errors
```

展开后显示：

* Event Log
* Model Calls
* Tool Calls
* Token Usage
* Retrieved Memory
* Handoff Records
* Error Logs

出错时自动展开。

---

# 4. Card Flow View：卡片任务流视图

## 4.1 定位

Card Flow View 是 Workspace 的默认视图。

它的目标是：

```text
让用户最快看懂任务进度到哪里了。
```

它比像素视图更适合：

* 快速判断任务状态
* 查看任务依赖
* 看 Agent 调度逻辑
* 看卡片之间的任务流转
* 看哪个 Agent 正在工作
* 看哪个 Agent 已完成或出错

---

## 4.2 Card Flow View 基础布局

示意结构：

```text
┌─────────────────────────────────────────────────────┐
│ View Toolbar                                         │
│ [Fit View] [Show Completed] [Auto Layout] [Edges On] │
├─────────────────────────────────────────────────────┤
│                                                     │
│   ┌─────────────┐       ┌─────────────┐             │
│   │ Planner     │──────▶│ Coder       │             │
│   │ Claude      │       │ DeepSeek    │             │
│   │ Running     │       │ Waiting     │             │
│   └─────────────┘       └─────────────┘             │
│          │                         │                │
│          ▼                         ▼                │
│   ┌─────────────┐       ┌─────────────┐             │
│   │ Research    │──────▶│ Reviewer    │             │
│   │ Kimi        │       │ GPT         │             │
│   │ Done        │       │ Queued      │             │
│   └─────────────┘       └─────────────┘             │
│                                                     │
│   Completed Agents: [Summarizer ✓] [Router ✓]       │
└─────────────────────────────────────────────────────┘
```

---

## 4.3 Agent Card 生成规则

Card Flow View 中：

```text
一个卡片 = 一个 Agent Session
```

当系统第一次调用某个 Agent 时，页面生成一个新的 Agent Card。

例如：

```text
Router Agent 被调用 → 出现 Router Card
Planner Agent 被调用 → 出现 Planner Card
Coder Agent 被调用 → 出现 Coder Card
Reviewer Agent 被调用 → 出现 Reviewer Card
```

如果某个 Agent 已经完成当前任务：

* 卡片不直接消失
* 卡片缩略到 Completed Agents 区域
* 用户仍然可以点击查看历史输出

如果某个 Agent 再次被调用，有两种策略：

### 策略 A：复用原卡片

适合 MVP。

```text
同一个 Agent 再次工作时，展开原卡片并更新状态。
```

### 策略 B：创建新的 Session Card

适合后期。

```text
Coder Agent 第一次执行 → Coder Session #1
Coder Agent 第二次执行 → Coder Session #2
```

MVP 推荐策略 A，避免页面卡片过多。

---

## 4.4 Agent Card 内容

每张 Agent Card 显示：

```text
Agent 名称
当前模型
状态灯
当前任务
任务进度
最近一句输出
Token 使用
Handoff 状态
```

示例：

```text
┌──────────────────────────┐
│ Coder Agent        ●     │
│ Model: DeepSeek Coder    │
│ Task #3 实现组件          │
│ Progress: 65%            │
│ Latest: 正在生成 Card...  │
│ Tokens: 3.2k             │
│ Handoff: Enabled         │
└──────────────────────────┘
```

---

## 4.5 Agent Card 状态

Agent Card 状态包括：

```text
idle        空闲
queued      排队中
running     执行中
waiting     等待中
reviewing   审查中
handoff     交接中
blocked     阻塞
error       出错
done        完成
```

状态颜色：

```text
灰色：idle / queued
蓝色：running
黄色：waiting / quota warning
紫色：handoff
红色：error / blocked
绿色：done
```

状态可以通过两种方式表达：

1. 卡片左上角状态灯
2. 卡片边框颜色

例如：

```text
蓝色边框 = 当前执行中
绿色边框 = 已完成
紫色边框 = 正在交接
红色边框 = 出错
```

---

## 4.6 卡片之间的连线

卡片之间的连线表示任务流转关系。

连线含义：

```text
Planner → Coder
表示 Planner 完成规划后，任务交给 Coder。

Coder → Reviewer
表示 Coder 完成实现后，任务交给 Reviewer。

Reviewer → Coder
表示 Reviewer 发现问题，任务返回 Coder 修改。

Coder → Summarizer
表示需要生成交接摘要或阶段总结。
```

连线颜色：

```text
灰色虚线：计划中的任务流
蓝色实线：正在执行的任务流
绿色实线：已完成的任务流
黄色虚线：等待或阻塞
紫色动画线：正在 Handoff
红色断裂线：出错或失败
```

连线样式：

```text
虚线：尚未执行
实线：已经发生
流动动画线：正在发生
断裂线：失败
```

---

## 4.7 Card Flow View 中的 Handoff 表达

当 Handoff 发生时：

```text
1. 原 Agent Card 变成紫色状态
2. 原 Agent Card 下方出现 “Generating Handoff Summary”
3. 两个 Agent Card 之间出现紫色动态连线
4. 中间出现一个小型 Handoff Summary Card
5. 接手 Agent Card 状态变成 “Loading Context”
6. 接手完成后，紫色线变成绿色线
```

示意：

```text
┌──────────────┐      Handoff Summary       ┌──────────────┐
│ Claude Coder │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ▶ │ GPT Coder    │
│ Quota Low    │        紫色动态线          │ Loading...   │
└──────────────┘                            └──────────────┘
```

点击 Handoff Summary Card 时，打开中心 Modal。

---

## 4.8 Completed Agents 缩略区

当 Agent 完成任务后，卡片可以缩略到主视图底部或右下角。

推荐放在主视图底部：

```text
Completed Agents:
[Router ✓] [Planner ✓] [Research ✓] [Summarizer ✓]
```

点击缩略卡片后：

* 打开 Agent Detail Modal
* 可以查看历史输出、模型调用、工具调用和 Handoff 记录

这样可以避免页面越来越拥挤。

---

## 4.9 Card Flow View 点击交互

点击 Agent Card：

```text
打开 Agent Detail Modal
背景虚化
其他 Agent 暂时不可点击
右上角 X 关闭
点击遮罩关闭
Esc 关闭
```

Agent Detail Modal 分为 5 个 Tab：

```text
Overview
Task
Context
Tools
History
```

Overview 内容：

```text
Agent 名称
Agent 职责
当前模型
为什么选择这个模型
当前任务
当前状态
最近输出
Token 使用
Quota 状态
下一步动作
```

Task 内容：

```text
当前任务标题
任务描述
完成标准
依赖任务
已完成步骤
未完成步骤
```

Context 内容：

```text
Goal
相关 Task
读取的 Memory
读取的 Project Context
Handoff Summary
```

Tools 内容：

```text
允许使用的工具
已调用工具
工具调用结果
是否需要用户批准
```

History 内容：

```text
历史执行记录
模型调用记录
错误记录
Handoff 记录
最终输出
```

---

# 5. Pixel Office View：像素办公室视图

## 5.1 定位

Pixel Office View 是 Workspace 的沉浸式视图。

它的目标是：

```text
让用户直观看到多个 AI 像团队一样在办公室协作。
```

它比 Card Flow View 更适合表达：

* Agent 工位
* 模型 Worker 入场
* 任务交接
* 额度不足
* 当前工作状态
* 多 Agent 协作氛围
* 产品差异化视觉记忆点

---

## 5.2 Pixel Office View 基础概念

在像素视图里：

```text
工位 = Agent
像素小人 = Worker / 当前模型
任务文件夹 = Task
交接文件夹 = Handoff Summary
门口 = 新 Worker 进入的位置
任务板 = Task Tree
Supervisor 区域 = 最终验收区
```

非常重要：

```text
Agent 不是模型。
Agent 是工位。
模型是进入工位工作的 Worker。
```

例如：

```text
Coder Station 是固定工位。
DeepSeek Worker 从门口进入，走到 Coder Station 开始工作。
如果后续换成 GPT Coder，则 GPT Worker 进入并接手 Coder Station。
```

---

## 5.3 Pixel Office View 场景布局

建议办公室场景包含：

```text
左下角：Entrance 大门
左侧：Task Board 任务板
中间：Planner / Coder / Research 工位
右侧：Reviewer / Summarizer 工位
右上角：Supervisor 工位
底部：Handoff Desk / Console
```

示意：

```text
┌─────────────────────────────────────────────────────┐
│                    Supervisor Desk                  │
│                         🧑‍💼                         │
│                                                     │
│   Task Board        Planner Desk     Research Desk   │
│   ┌────────┐          🧑‍💻              🧑‍🔬          │
│   │Tasks   │                                         │
│   └────────┘       Coder Desk       Reviewer Desk    │
│                       🧑‍💻              🧑‍⚖️          │
│                                                     │
│ Entrance 🚪        Handoff Desk      Summarizer Desk │
│                                      🧑‍💼             │
└─────────────────────────────────────────────────────┘
```

---

## 5.4 工位规则

工位是固定的。

MVP 阶段建议固定 6 个工位：

```text
Router Station
Planner Station
Research Station
Coder Station
Reviewer Station
Summarizer Station
Supervisor Station
```

也可以把 Router 和 Planner 合并显示，避免场景过满。

推荐 MVP 场景：

```text
Planner
Research
Coder
Reviewer
Summarizer
Supervisor
```

Router 作为隐藏系统角色，显示在左侧日志或任务板中。

---

## 5.5 Worker 入场规则

当某个模型被调用并绑定到 Agent 上时：

```text
1. Worker 从办公室大门出现
2. Worker 头顶显示模型名称
3. Worker 沿路径走到对应工位
4. 到达工位后坐下或站在工位前
5. 工位状态灯变成工作中
6. 工位上方出现当前 Task 小标签
```

示例：

```text
DeepSeek Worker 进入
↓
走到 Coder Station
↓
Coder Station 状态变蓝
↓
显示 Task #3: 实现组件
```

Worker 标签：

```text
Claude
GPT
DeepSeek
Kimi
GLM
MiniMax
```

---

## 5.6 Pixel Office View 中的状态表达

工位状态通过三种方式表达：

1. 工位状态灯
2. Worker 动作
3. 工位上方浮动标签

状态示例：

```text
idle：
工位空着，状态灯灰色。

running：
Worker 正在工位工作，状态灯蓝色。

waiting：
Worker 停住或看向任务板，状态灯黄色。

handoff：
Worker 拿起文件夹，状态灯紫色。

error：
工位上出现警告标识，状态灯红色。

done：
工位显示绿色 check，Worker 放下任务文件。
```

---

## 5.7 Pixel Office View 中的任务表达

任务用文件夹或任务卡表达。

规则：

```text
Task File = 当前任务
Handoff Folder = 交接摘要
Review Sheet = 审查结果
Final Report = 最终输出
```

例如：

```text
Planner 完成任务拆解后，把 Task File 放到 Task Board。
Coder 接到任务时，Task File 移动到 Coder Desk。
Reviewer 审查时，Review Sheet 移动到 Reviewer Desk。
Supervisor 验收时，Final Report 移动到 Supervisor Desk。
```

MVP 不需要复杂动画，可以先做轻量移动：

```text
任务标签从一个工位淡出，在另一个工位淡入。
```

后期再做真实路径动画。

---

## 5.8 Pixel Office View 中的 Handoff 动画

Handoff 是像素视图最重要的动画。

交接流程：

```text
1. 当前 Worker 状态变为 quota warning 或 blocked
2. 工位状态灯变成紫色
3. Worker 生成一个 Handoff Folder
4. Handoff Folder 显示 “Summary Ready”
5. 新 Worker 从门口进入
6. 旧 Worker 将 Handoff Folder 交给新 Worker
7. 新 Worker 走到目标工位
8. 目标工位显示 “Loading Context”
9. 新 Worker 开始继续工作
```

视觉表达：

```text
旧 Worker：Claude
新 Worker：GPT
交接物：Handoff Folder
交接路径：Claude Desk → GPT Desk
状态颜色：紫色
```

Handoff 完成后：

```text
旧工位显示 Done / Handed Off
新工位显示 Running
Bottom Console 记录 Handoff
Handoff 页面保存交接记录
```

---

## 5.9 点击工位后的内嵌详情框

点击像素工位时，不打开中心 Modal，而是在像素办公室内部出现内嵌式详情框。

交互规则：

```text
1. 点击工位
2. 详情框出现在工位附近
3. 不虚化整个页面
4. 其他像素区域仍然可见
5. 点击 X 关闭
6. 点击空白区域关闭
7. 点击另一个工位时，详情框切换到另一个工位
```

详情框内容控制在轻量级：

```text
Station: Coder
Worker: DeepSeek
Task: 实现 Agent Card
Status: Running
Next: Send to Reviewer
```

底部可以放快捷按钮：

```text
View Full Detail
View Logs
Generate Handoff
Pause
```

点击 View Full Detail 后，再打开完整 Agent Detail Modal。

---

## 5.10 点击 Worker 和点击工位的区别

可以设计成：

```text
点击工位：
查看 Agent Station 状态。

点击 Worker：
查看当前模型 Worker 状态。

点击任务文件夹：
查看当前 Task 状态。
```

MVP 可以先简化：

```text
点击工位或 Worker 都打开同一个 Station Popover。
```

后期再拆成不同对象。

---

# 6. 双视图切换逻辑

## 6.1 默认视图

Workspace 默认进入：

```text
Card Flow View
```

原因：

* 加载快
* 信息清晰
* 更适合任务判断
* 更适合开发 MVP
* 用户一眼能看进度

Pixel Office View 作为右上角按钮切换。

按钮示例：

```text
[Card Flow] [Pixel Office]
```

---

## 6.2 切换到 Pixel Office View

用户点击 Pixel Office 按钮后：

```text
1. 当前任务不中断
2. Agent 运行不中断
3. 只切换前端展示层
4. 页面显示 Pixel Office Loading
5. 系统将当前 Workspace State 映射到像素场景
6. 渲染工位、Worker、任务文件和状态灯
7. 切换完成后进入 Pixel Office View
```

加载提示：

```text
Preparing Pixel Office...
正在同步 Agent 状态
正在加载工位
正在放置 Worker
```

这一步可以需要 1–2 秒，因为像素视图的场景、资源和动画可能比卡片视图更重。

---

## 6.3 切换回 Card Flow View

Pixel Office View 切回 Card Flow View 应该更快。

逻辑：

```text
1. 读取同一份 Workspace State
2. 重新渲染 Agent Cards
3. 恢复卡片连线
4. 保留当前任务状态
```

不需要重新跑任务。

---

## 6.4 视图切换时的状态同步

必须保证：

```text
Card Flow View 中正在 running 的 Agent
切换到 Pixel Office View 后仍然显示 running。

Card Flow View 中已完成的 Agent
切换到 Pixel Office View 后显示 done 或历史标记。

Card Flow View 中正在 Handoff 的连线
切换到 Pixel Office View 后显示 Handoff Folder 动画。
```

也就是说：

```text
视图切换 = 渲染层变化
任务运行 = 不受影响
```

---

# 7. 底层前端逻辑建议

## 7.1 总体架构

建议前端分成三层：

```text
Workspace Store
↓
View Adapter
↓
Renderer
```

### Workspace Store

保存真实业务状态。

```text
goal
tasks
agents
workers
edges
handoffs
logs
quota
selectedEntity
currentView
```

### View Adapter

把业务数据转换成某个视图需要的数据。

```text
CardFlowAdapter
PixelOfficeAdapter
```

### Renderer

负责具体展示。

```text
CardFlowRenderer
PixelOfficeRenderer
```

---

## 7.2 为什么不能做成两套底层逻辑

卡片视图和像素视图的展示逻辑可以不同，但底层业务逻辑不能完全分开。

如果完全分开，会产生问题：

```text
一个视图显示 Agent 已完成
另一个视图显示 Agent 还在工作

一个视图显示 Handoff 已完成
另一个视图没有同步

一个视图里的 Task 顺序变了
另一个视图仍然是旧数据
```

所以推荐：

```text
底层状态共用
展示层分开
动画状态独立
```

也就是：

```text
共享：任务、Agent、Worker、日志、Handoff、Quota
独立：布局、动画、视觉效果、Popover 位置
```

---

## 7.3 状态数据结构示例

```ts
type WorkspaceView = 'card-flow' | 'pixel-office';

type AgentStatus =
  | 'idle'
  | 'queued'
  | 'running'
  | 'waiting'
  | 'handoff'
  | 'reviewing'
  | 'error'
  | 'done';

type WorkspaceState = {
  goal: Goal;
  tasks: Task[];
  agents: AgentSession[];
  workers: WorkerSession[];
  edges: TaskEdge[];
  handoffs: HandoffRecord[];
  logs: ExecutionLog[];
  quota: QuotaStatus[];
  currentView: WorkspaceView;
  selectedEntity?: SelectedEntity;
};
```

---

## 7.4 Card Flow 数据

```ts
type CardFlowNode = {
  id: string;
  agentId: string;
  title: string;
  modelName: string;
  status: AgentStatus;
  taskTitle: string;
  progress: number;
  collapsed: boolean;
};

type CardFlowEdge = {
  id: string;
  from: string;
  to: string;
  status: 'planned' | 'active' | 'done' | 'handoff' | 'error';
};
```

---

## 7.5 Pixel Office 数据

```ts
type PixelStation = {
  id: string;
  agentId: string;
  stationName: string;
  position: { x: number; y: number };
  status: AgentStatus;
  currentWorkerId?: string;
  currentTaskId?: string;
};

type PixelWorker = {
  id: string;
  modelName: string;
  agentId: string;
  position: { x: number; y: number };
  targetStationId: string;
  animationState:
    | 'entering'
    | 'walking'
    | 'working'
    | 'waiting'
    | 'handoff'
    | 'leaving';
};
```

---

# 8. 两种详情查看方式

## 8.1 Card Flow View 的详情

点击 Agent Card：

```text
打开中心 Agent Detail Modal
背景虚化
其他卡片不可点击
```

Modal 内容偏完整：

```text
Overview
Task
Context
Tools
History
```

适合查看：

```text
这个 Agent 是谁
为什么用了这个模型
当前任务是什么
读了哪些上下文
调用了哪些工具
输出了什么
有没有出错
是否发生 Handoff
```

---

## 8.2 Pixel Office View 的详情

点击工位：

```text
在像素场景中打开 Station Popover
不虚化整个页面
保持办公室可见
```

Popover 内容偏轻：

```text
Station
Worker
Task
Status
Next Step
Quick Actions
```

如果用户需要完整详情，再点击：

```text
View Full Detail
```

打开中心 Modal。

---

# 9. 任务进度表达

Workspace 中任务进度通过三层表达：

## 9.1 左侧 Task Tree

显示整体任务结构：

```text
Task #1 需求分析       Done
Task #2 设计卡片视图   Running
Task #3 设计像素视图   Waiting
Task #4 审查方案       Queued
```

## 9.2 中间主视图

Card Flow View：

```text
通过卡片状态和连线颜色判断进度。
```

Pixel Office View：

```text
通过工位状态、Worker 动作、任务文件位置判断进度。
```

## 9.3 Bottom Console

显示详细执行事件：

```text
Planner created 5 tasks
Coder started Task #2
Reviewer waiting for Coder output
Claude quota warning
Handoff Summary generated
```

---

# 10. 额度状态表达

Quota 状态需要出现在三个地方：

## 10.1 Top Bar

显示整体额度提醒：

```text
Claude: Warning
GPT: Normal
DeepSeek: Normal
```

## 10.2 Agent Card

显示当前模型额度：

```text
Model: Claude
Quota: Low
```

## 10.3 Pixel Office

在 Worker 或工位上方显示：

```text
Quota Low
```

表现方式：

```text
黄色提示 = 额度偏低
紫色提示 = 正在准备 Handoff
红色提示 = 额度已阻断
```

---

# 11. 页面中的按钮设计

## 11.1 Top Bar 按钮

```text
Run
Pause
Resume
Stop
Export
Card Flow / Pixel Office
```

## 11.2 Card Flow Toolbar

```text
Fit View
Auto Layout
Show Completed
Hide Completed
Show Edges
Hide Edges
```

## 11.3 Pixel Office Toolbar

```text
Reset Camera
Show Labels
Hide Labels
Show Task Board
Show Handoff Path
```

MVP 可以只保留：

```text
Reset View
Show Labels
```

## 11.4 Agent Detail Modal 按钮

```text
Pause Agent
Retry
Generate Handoff
View Logs
Open Full Output
```

## 11.5 Station Popover 按钮

```text
View Full Detail
View Logs
Handoff
```

---

# 12. 空状态设计

用户第一次进入 Workspace 时，Card Flow View 显示空状态：

```text
Start with a Goal
让多个 AI Agent 围绕同一个目标协作。
```

下面放示例：

```text
设计一个前端页面
分析一个代码仓库
生成一份产品文档
修复一个 bug
```

Pixel Office View 空状态：

```text
办公室为空。
输入一个 Goal 后，Agent Worker 会从门口进入工位开始工作。
```

---

# 13. 加载状态设计

## 13.1 任务运行加载

不要只显示 spinner。

应该显示具体动作：

```text
Planner 正在拆解任务...
Coder 正在读取上下文...
Reviewer 正在等待 Coder 输出...
Summarizer 正在生成 Handoff Summary...
```

## 13.2 Pixel Office 切换加载

切换时显示：

```text
Preparing Pixel Office...
正在同步 Agent 状态
正在加载工位资源
正在放置 Worker
```

不要让用户以为任务卡住了。

需要明确显示：

```text
任务仍在后台继续运行
```

---

# 14. 错误状态设计

当 Agent 出错时：

Card Flow View：

```text
Agent Card 变红
连线变红色断裂线
Bottom Console 自动展开
```

Pixel Office View：

```text
工位状态灯变红
Worker 停止动作
工位旁出现 warning icon
```

错误详情显示：

```text
错误原因
影响任务
建议操作
Retry
Generate Handoff
View Logs
```

---

# 15. 视图切换边界情况

## 15.1 正在 Handoff 时切换视图

Card Flow View 中：

```text
紫色动态连线
Handoff Summary Card
```

切换到 Pixel Office View 后：

```text
显示 Handoff Folder
旧 Worker 和新 Worker 交接
目标工位显示 Loading Context
```

## 15.2 Agent 已完成后切换视图

Card Flow View 中：

```text
Agent Card 缩略到 Completed Agents
```

Pixel Office View 中：

```text
工位显示绿色完成标记
Worker 可以坐在工位旁或淡出离开
```

MVP 推荐：

```text
完成后 Worker 淡出，工位保留绿色完成标记。
```

## 15.3 同一个 Agent 多次执行

MVP：

```text
复用同一个 Agent Card
复用同一个 Station
更新当前任务
历史记录放入 Modal 的 History Tab
```

后期：

```text
支持 Session Timeline
显示 Coder Session #1 / #2 / #3
```

---

# 16. 视觉风格

整体风格：

```text
浅色
低饱和
类 Claude
卡片化
轻像素元素
专业工具感
```

Card Flow View：

```text
干净
清晰
信息密度适中
卡片边框表达状态
连线表达任务流
```

Pixel Office View：

```text
像素风
但不要游戏化过度
工位清晰
Worker 小而有识别度
状态提示明确
```

不要做成：

```text
纯游戏界面
复杂 3D 场景
深色赛博风
节点线条过密
动画过多影响阅读
```

---

# 17. MVP 开发顺序

建议按这个顺序实现：

## 第 1 步：Workspace 基础框架

```text
Top Bar
左侧控制区
中间视图容器
Bottom Console
```

## 第 2 步：Workspace Store

```text
Goal
Task
Agent
Worker
Edge
Handoff
Log
Quota
```

## 第 3 步：Card Flow View

```text
Agent Card
Task Edge
Completed Agents
状态颜色
点击 Card 打开 Modal
```

## 第 4 步：Agent Detail Modal

```text
Overview
Task
Context
Tools
History
```

## 第 5 步：Pixel Office View 静态版

```text
办公室背景
固定工位
Worker 显示
状态灯
Station Popover
```

## 第 6 步：Pixel Office 动画版

```text
Worker 从门口进入
Worker 走到工位
任务文件移动
Handoff Folder 交接
完成后淡出
```

## 第 7 步：双视图同步

```text
Card Flow → Pixel Office
Pixel Office → Card Flow
状态同步
选中对象同步
Handoff 同步
错误同步
```

---

# 18. 最终用户体验路径

用户进入 Workspace：

```text
1. 默认看到 Card Flow View
2. 输入 Goal
3. Router / Planner 开始工作
4. Agent Card 一个个出现
5. 任务连线展示流转关系
6. 已完成 Agent 缩略到底部
7. 当前运行 Agent 保持展开
8. 用户点击 Card 查看完整详情
9. 用户点击 Pixel Office 按钮
10. 页面加载像素办公室
11. 当前 Agent Worker 从门口进入或直接同步到工位
12. 用户看到模型 Worker 在不同工位工作
13. Handoff 时看到文件夹交接
14. Supervisor 完成最终审查
15. 系统生成最终结果和可沉淀 Memory / Skill
```

---

# 19. 方案总结

Workspace 最终应设计为：

```text
默认 Card Flow View：
用于效率、状态判断、任务流转、快速管理。

可切换 Pixel Office View：
用于产品识别、可视化协作、工位隐喻、Handoff 动画。

两者共用底层 Workspace State：
保证任务、Agent、模型、Handoff、日志、额度状态完全同步。

展示层分开：
Card Flow 用卡片和连线。
Pixel Office 用工位、Worker、任务文件和交接动画。
```

最终效果是：

```text
用户既能像管理项目一样高效查看 Agent 任务流，
也能像看 AI 团队办公室一样理解多个模型如何协作。
```
