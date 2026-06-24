# Workspace 页面 PRD

> 🎯 **v0.1 最核心的页面。所有核心功能都在这个页面完成。**

---

## 一、页面整体布局

取消固定右侧详情面板。

Workspace主结构：

```
┌──────────────────────────────────────────────────────────────┐
│ Top Bar：项目 / Goal / Run 状态 / 视图切换 / 模型额度      │
├───────────────┬──────────────────────────────────────────┤
│  左侧控制区   │  中间 Workspace 主视图                 │
│  Goal 输入      │  Card Flow View / Pixel Office View     │
│  Run Config   │                                         │
│  Task Tree      │                                         │
├───────────────┴──────────────────────────────────────────┤
│ Bottom Console：执行日志 / 模型调用 / 工具调用 / 错误信息   │
└──────────────────────────────────────────────────────────────┘
```

---

## 二、各区域详细说明

### 1. Top Bar（P0）

#### 功能清单

显示内容：

- 当前项目名称
- 当前 Goal 标题
- 当前运行状态
- 正在工作的 Agent 数量
- 模型额度概览
- 当前视图切换按钮
- Pause / Resume / Stop
- Export Summary

示例：

```
ModelGate Agent Studio
Goal: 设计 Workspace 双视图
Running · 3 Agents Active · 1 Handoff
[Card Flow] [Pixel Office]
```

#### 按钮

```
Run / Pause / Resume / Stop / Export
```

---

### 2. 左侧控制区（P0）

左侧控制区在两个视图中保持一致。

#### 2.1 Goal 输入

```
Goal
帮我设计 Workspace 双视图页面

[运行 ▼
```

#### 2.2 Run Config

```
Run Config
- Agent Team Mode: ON
- Auto Handoff: ON
- Auto Model Switch: ON
- Tool Call: Ask First
- Run Depth: Standard
```

#### 2.3 Task Tree

```
Task Tree
- Task #1 分析需求
- Task #2 设计卡片视图
- Task #3 设计像素视图
- Task #4 设计状态系统
- Task #5 Supervisor 审查
```

#### 点击 Task Tree 中的任务时：

- 在 Card Flow View 中，高亮对应 Agent Card 和 Task Edge
- 在 Pixel Office View 中，高亮对应工位和 Worker

---

### 3. 中间主视图（P0）

中间区域根据用户选择展示：Card Flow View 或 Pixel Office View。

这是 Workspace 的主视觉区域。

---

## 三、Card Flow View（默认视图）

### 3.1 定位

Card Flow View 是 Workspace 的默认视图。

它的目标是：让用户最快看懂任务进度到哪里了。

它比像素视图更适合：快速判断任务状态、查看任务依赖、看 Agent 调度逻辑、看卡片之间的任务流转、看哪个 Agent 正在工作、看哪个 Agent 已完成或出错。

### 3.2 View Toolbar

```
[Fit View] [Show Completed] [Auto Layout] [Edges On]
```

### 3.3 Agent Card 生成规则

Card Flow View 中：一个卡片 = 一个 Agent Session。

当系统第一次调用某个 Agent 时，页面生成一个新的 Agent Card。

例如：
```
Router Agent 被调用 → 出现 Router Card
Planner Agent 被调用 → 出现 Planner Card
Coder Agent 被调用 → 出现 Coder Card
Reviewer Agent 被调用 → 出现 Reviewer Card
```

如果某个 Agent 已经完成当前任务：
- 卡片不直接消失
- 卡片缩略到 Completed Agents 区域
- 用户仍然可以点击查看历史输出

如果某个 Agent 再次被调用，MVP 策略：复用原卡片。

### 3.4 Agent Card 内容

每张 Agent Card 显示：

```
┌──────────────────────────┐
│ Coder Agent        ●     │  ← Agent 名称 + 状态灯
│ Model: DeepSeek Coder    │  ← 当前模型
│ Task #3 实现组件          │  ← 当前任务
│ Progress: 65%            │  ← 任务进度
│ Latest: 正在生成 Card...  │  ← 最近一句输出
│ Tokens: 3.2k             │  ← Token 使用
│ Handoff: Enabled           │  ← Handoff 状态
└──────────────────────────┘
```

### 3.5 Agent Card 状态

Agent Card 状态包括：

```
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

```
灰色：idle / queued
蓝色：running
黄色：waiting / quota warning
紫色：handoff
红色：error / blocked
绿色：done
```

状态可以通过两种方式表达：卡片左上角状态灯、卡片边框颜色。

例如：
```
蓝色边框 = 当前执行中
绿色边框 = 已完成
紫色边框 = 正在交接
红色边框 = 出错
```

### 3.6 卡片之间的连线

卡片之间的连线表示任务流转关系。

连线含义：

```
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

```
灰色虚线：计划中的任务流
蓝色实线：正在执行的任务流
绿色实线：已完成的任务流
黄色虚线：等待或阻塞
紫色动画线：正在 Handoff
红色断裂线：出错或失败
```

连线样式：

```
虚线：尚未执行
实线：已经发生
流动动画线：正在发生
断裂线：失败
```

### 3.7 Card Flow View 中的 Handoff 表达

当 Handoff 发生时：

1. 原 Agent Card 变成紫色状态
2. 原 Agent Card 下方出现 "Generating Handoff Summary"
3. 两个 Agent Card 之间出现紫色动态连线
4. 中间出现一个小型 Handoff Summary Card
5. 接手 Agent Card 状态变成 "Loading Context"
6. 接手完成后，紫色线变成绿色线

示意：

```
┌──────────────┐      Handoff Summary       ┌──────────────┐
│ Claude Coder │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ▶ │ GPT Coder    │
│ Quota Low    │        紫色动态线          │ Loading...   │
└──────────────┘                            └──────────────┘
```

点击 Handoff Summary Card 时，打开中心 Modal。

### 3.8 Completed Agents 缩略区

当 Agent 完成任务后，卡片可以缩略到主视图底部。

推荐放在主视图底部：

```
Completed Agents:
[Router ✓] [Planner ✓] [Research ✓] [Summarizer ✓]
```

点击缩略卡片后：

- 打开 Agent Detail Modal
- 可以查看历史输出、模型调用、工具调用和 Handoff 记录

这样可以避免页面越来越拥挤。

### 3.9 点击交互：Agent Detail Modal

点击 Agent Card：

打开 Agent Detail Modal，背景虚化，其他 Agent 暂时不可点击，右上角 X 关闭，点击遮罩关闭，Esc 关闭。

Agent Detail Modal 分为 5 个 Tab：

```
Overview
Task
Context
Tools
History
```

Overview 内容：

```
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

```
当前任务标题
任务描述
完成标准
依赖任务
已完成步骤
未完成步骤
```

Context 内容：

```
Goal
相关 Task
读取的 Memory
读取的 Project Context
Handoff Summary
```

Tools 内容：

```
允许使用的工具
已调用工具
工具调用结果
是否需要用户批准
```

History 内容：

```
历史执行记录
模型调用记录
错误记录
Handoff 记录
最终输出
```

---

## 四、Pixel Office View（像素办公室视图）

### 4.1 定位

Pixel Office View 是 Workspace 的沉浸式视图。

它的目标是：让用户直观看到多个 AI 像团队一样在办公室协作。

它比 Card Flow View 更适合表达：Agent 工位、模型 Worker 入场、任务交接、额度不足、当前工作状态、多 Agent 协作氛围、产品差异化视觉记忆点。

### 4.2 基础概念

在像素视图里：

```
工位 = Agent
像素小人 = Worker / 当前模型
任务文件夹 = Task
交接文件夹 = Handoff Summary
门口 = 新 Worker 进入的位置
任务板 = Task Tree
Supervisor 区域 = 最终验收区
```

非常重要：

```
Agent 不是模型。
Agent 是工位。
模型是进入工位工作的 Worker。
```

例如：

```
Coder Station 是固定工位。
DeepSeek Worker 从门口进入，走到 Coder Station 开始工作。
如果后续换成 GPT Coder，则 GPT Worker 进入并接手 Coder Station。
```

### 4.3 场景布局

建议办公室场景包含：

```
左下角：Entrance 大门
左侧：Task Board 任务板
中间：Planner / Coder / Research 工位
右侧：Reviewer / Summarizer 工位
右上角：Supervisor 工位
底部：Handoff Desk / Console
```

示意：

```
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

### 4.4 工位规则

工位是固定的。

MVP 阶段建议固定工位：

```
Planner
Research
Coder
Reviewer
Summarizer
Supervisor
```

Router 作为隐藏系统角色，显示在左侧日志或任务板中。

### 4.5 Worker 入场规则

当某个模型被调用并绑定到 Agent 上时：

```
1. Worker 从办公室大门出现
2. Worker 头顶显示模型名称
3. Worker 沿路径走到对应工位
4. 到达工位后坐下或站在工位前
5. 工位状态灯变成工作中
6. 工位上方出现当前 Task 小标签
```

Worker 标签：

```
Claude
GPT
DeepSeek
Kimi
GLM
MiniMax
```

### 4.6 工位状态表达

工位状态通过三种方式表达：工位状态灯、Worker 动作、工位上方浮动标签。

状态示例：

```
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

### 4.7 任务表达

任务用文件夹或任务卡表达。

规则：

```
Task File = 当前任务
Handoff Folder = 交接摘要
Review Sheet = 审查结果
Final Report = 最终输出
```

例如：

```
Planner 完成任务拆解后，把 Task File 放到 Task Board。
Coder 接到任务时，Task File 移动到 Coder Desk。
Reviewer 审查时，Review Sheet 移动到 Reviewer Desk。
Supervisor 验收时，Final Report 移动到 Supervisor Desk。
```

MVP 不需要复杂动画，可以先做轻量移动：任务标签从一个工位淡出，在另一个工位淡入。

### 4.8 Pixel Office View 中的 Handoff 动画

Handoff 是像素视图最重要的动画。

交接流程：

```
1. 当前 Worker 状态变为 quota warning 或 blocked
2. 工位状态灯变成紫色
3. Worker 生成一个 Handoff Folder
4. Handoff Folder 显示 "Summary Ready"
5. 新 Worker 从门口进入
6. 旧 Worker 将 Handoff Folder 交给新 Worker
7. 新 Worker 走到目标工位
8. 目标工位显示 "Loading Context"
9. 新 Worker 开始继续工作
```

视觉表达：

```
旧 Worker：Claude
新 Worker：GPT
交接物：Handoff Folder
交接路径：Claude Desk → GPT Desk
状态颜色：紫色
```

Handoff 完成后：

```
旧工位显示 Done / Handed Off
新工位显示 Running
Bottom Console 记录 Handoff
Handoff 页面保存交接记录
```

### 4.9 点击工位后的内嵌详情框

点击像素工位时，不打开中心 Modal，而是在像素办公室内部出现内嵌式详情框。

交互规则：

```
1. 点击工位
2. 详情框出现在工位附近
3. 不虚化整个页面
4. 其他像素区域仍然可见
5. 点击 X 关闭
6. 点击空白区域关闭
7. 点击另一个工位时，详情框切换到另一个工位
```

详情框内容控制在轻量级：

```
Station: Coder
Worker: DeepSeek
Task: 实现 Agent Card
Status: Running
Next: Send to Reviewer
```

底部可以放快捷按钮：

```
View Full Detail
View Logs
Generate Handoff
Pause
```

点击 View Full Detail 后，再打开完整 Agent Detail Modal。

### 4.10 点击 Worker 和点击工位的区别

MVP 可以先简化：点击工位或 Worker 都打开同一个 Station Popover。

---

## 五、双视图切换逻辑

### 5.1 默认视图

Workspace 默认进入 Card Flow View。

原因：加载快、信息清晰、更适合任务判断、更适合开发 MVP、用户一眼能看进度。

Pixel Office View 作为右上角按钮切换。

按钮示例：

```
[Card Flow] [Pixel Office]
```

### 5.2 切换到 Pixel Office View

用户点击 Pixel Office 按钮后：

```
1. 当前任务不中断
2. Agent 运行不中断
3. 只切换前端展示层
4. 页面显示 Pixel Office Loading
5. 系统将当前 Workspace State 映射到像素场景
6. 渲染工位、Worker、任务文件和状态灯
7. 切换完成后进入 Pixel Office View
```

加载提示：

```
Preparing Pixel Office...
正在同步 Agent 状态
正在加载工位
正在放置 Worker
```

### 5.3 切换回 Card Flow View

Pixel Office View 切回 Card Flow View 应该更快。

逻辑：

```
1. 读取同一份 Workspace State
2. 重新渲染 Agent Cards
3. 恢复卡片连线
4. 保留当前任务状态
```

不需要重新跑任务。

### 5.4 视图切换时的状态同步

必须保证：

```
Card Flow View 中正在 running 的 Agent
切换到 Pixel Office View 后仍然显示 running。

Card Flow View 中已完成的 Agent
切换到 Pixel Office View 后显示 done 或历史标记。

Card Flow View 中正在 Handoff 的连线
切换到 Pixel Office View 后显示 Handoff Folder 动画。
```

也就是说：

```
视图切换 = 渲染层变化
任务运行 = 不受影响
```

---

## 六、底部执行日志区（P1）

### 6.1 默认收起状态

默认收起，只露出简短运行状态。

默认状态：

```
Running · 12 Model Calls · 4 Tool Calls · 1 Handoff · 0 Errors
```

### 6.2 展开后显示

展开后显示多个 Tab：

```
Event Log
Model Calls
Tool Calls
Token Usage
Retrieved Memory
Handoff Records
Error Logs
```

出错时自动展开。

---

## 七、额度状态表达

Quota 状态需要出现在三个地方：

### Top Bar

显示整体额度提醒：

```
Claude: Warning
GPT: Normal
DeepSeek: Normal
```

### Agent Card

显示当前模型额度：

```
Model: Claude
Quota: Low
```

### Pixel Office

在 Worker 或工位上方显示：

```
Quota Low
```

表现方式：

```
黄色提示 = 额度偏低
紫色提示 = 正在准备 Handoff
红色提示 = 额度已阻断
```

---

## 八、空状态设计

用户第一次进入 Workspace 时，Card Flow View 显示空状态：

```
Start with a Goal
让多个 AI Agent 围绕同一个目标协作。
```

下面放示例：

```
设计一个前端页面
分析一个代码仓库
生成一份产品文档
修复一个 bug
```

Pixel Office View 空状态：

```
办公室为空。
输入一个 Goal 后，Agent Worker 会从门口进入工位开始工作。
```

---

## 九、加载状态设计

### 9.1 任务运行加载

不要只显示 spinner。应该显示具体动作：

```
Planner 正在拆解任务...
Coder 正在读取上下文...
Reviewer 正在等待 Coder 输出...
Summarizer 正在生成 Handoff Summary...
```

### 9.2 Pixel Office 切换加载

切换时显示：

```
Preparing Pixel Office...
正在同步 Agent 状态
正在加载工位资源
正在放置 Worker
```

需要明确显示：任务仍在后台继续运行。

---

## 十、错误状态设计

当 Agent 出错时：

Card Flow View：

```
Agent Card 变红
连线变红色断裂线
Bottom Console 自动展开
```

Pixel Office View：

```
工位状态灯变红
Worker 停止动作
工位旁出现 warning icon
```

错误详情显示：

```
错误原因
影响任务
建议操作
Retry
Generate Handoff
View Logs
```

---

## 十一、视图切换边界情况

### 11.1 正在 Handoff 时切换视图

Card Flow View 中：紫色动态连线 + Handoff Summary Card

切换到 Pixel Office View 后：显示 Handoff Folder + 旧 Worker 和新 Worker 交接 + 目标工位显示 Loading Context

### 11.2 Agent 已完成后切换视图

Card Flow View 中：Agent Card 缩略到 Completed Agents

Pixel Office View 中：工位显示绿色完成标记 + Worker 淡出离开

### 11.3 同一个 Agent 多次执行

MVP：复用同一个 Agent Card / 复用同一个 Station / 更新当前任务 / 历史记录放入 Modal 的 History Tab

---

## 十二、视觉风格

整体：浅色 + 低饱和 + 类 Claude + 卡片化 + 轻像素元素 + 专业工具感。

Card Flow View：干净 + 清晰 + 信息密度适中。

Pixel Office View：像素风 + 但不要游戏化过度 + 工位清晰 + Worker 小而有识别度。

不要做成：纯游戏界面、复杂 3D 场景、深色赛博风、节点线条过密、动画过多影响阅读。

---

## 十三、MVP 开发顺序

建议按这个顺序实现：

第 1 步：Workspace 基础框架（Top Bar + 左侧控制区 + 中间视图容器 + Bottom Console）

第 2 步：Workspace Store（核心状态管理）

第 3 步：Card Flow View（Agent Card + 状态颜色）

第 4 步：Agent Detail Modal（5 个 Tab）

第 5 步：Card 状态系统 + 连线 + Completed Agents 缩略区

第 6 步：Pixel Office View 静态版（办公室背景 + 固定工位）

第 7 步：Pixel Worker 显示 + Station Popover + 状态灯

第 8 步：Pixel Office 动画版（Worker 入场 + 行走 + 任务文件移动 + Handoff Folder 交接）

第 9 步：双视图同步逻辑

第 10 步：Bottom Console 日志系统

第 11 步：空状态 + 加载状态 + 错误状态

---

## 十四、验收标准

Workspace 页面 v0.1 完成的标志：

```
1. 可以输入 Goal 并点击开始
2. Agent Cards 逐个出现，状态颜色正确
3. 点击 Card 打开 Agent Detail Modal
4. 可以看到 5 个 Tab 的详情内容
5. Completed Agents 缩略到底部
6. 可以切换到 Pixel Office View
7. 像素视图中可以看到工位和 Worker
8. 点击工位打开 Station Popover
9. 可以手动触发 Handoff 并看到交接效果
10. 两个视图状态同步
11. 底部日志滚动更新
```
