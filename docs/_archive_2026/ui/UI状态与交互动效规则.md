# UI 状态与交互动效规则文档

> 🎨 **本文档定义 UI 状态的表现形式和交互动效规则。**
>
> 前端开发必须严格遵循这些状态定义和交互规范。

---

## 一、状态颜色系统

所有状态必须用统一的颜色系统，贯穿整个产品。

### 1.1 状态色板

```scss
// 核心状态色
$status-idle: #9ca3af;      // 灰色 - 空闲
$status-pending: #fbbf24;   // 黄色 - 等待中
$status-running: #3b82f6;   // 蓝色 - 运行中
$status-handoff: #8b5cf6;   // 紫色 - 交接中
$status-completed: #10b981; // 绿色 - 完成
$status-failed: #ef4444;    // 红色 - 失败

// 辅助色
$bg-dark: #111827;          // 深灰背景
$bg-light: #1f2937;         // 浅灰背景
$border-color: #374151;     // 边框色
$text-primary: #f9fafb;     // 主文字
$text-secondary: #9ca3af;   // 次要文字
```

### 1.2 状态语义映射

Agent Card 完整 9 种状态：

| 状态 | 颜色 | 语义 | 场景 |
|------|------|------|------|
| idle | 灰色 | 空闲、未开始 | Agent 待机、工位空着 |
| queued | 灰色 | 排队中 | 已创建、等待调度 |
| running | 蓝色 | 运行中 | Agent 工作中、模型调用中 |
| waiting | 黄色 | 等待中 | 等待依赖、等待用户确认、额度 warning |
| reviewing | 蓝色 | 审查中 | Supervisor / Reviewer 审查输出 |
| handoff | 紫色 | 交接中 | 任务交接、Handoff 摘要生成中 |
| blocked | 红色 | 阻塞 | 任务无法继续、需要人工干预 |
| error | 红色 | 出错 | 模型调用错误、执行错误 |
| done | 绿色 | 完成 | Task 完成、Goal 完成 |

---

## 二、Task 卡片状态设计

### 2.1 卡片基础样式

```css
.task-card {
  width: 280px;
  min-height: 120px;
  border-radius: 8px;
  border: 1px solid $border-color;
  background: $bg-light;
  padding: 16px;
  transition: all 0.2s ease;
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
```

### 2.2 各状态的视觉表现

```
┌─────────────────────────────────────────┐
│ 状态：pending（灰色）                     │
├─────────────────────────────────────────┤
│                                         │
│  ○ 任务标题                              │
│                                         │
│  任务描述... 两行截断                     │
│                                         │
│  [Agent 图标] 待分配  |  ⏱️ --          │
│                                         │
└─────────────────────────────────────────┘
  边框：灰色虚线
  左上角：灰色空心圆

┌─────────────────────────────────────────┐
│ 状态：running（蓝色）                     │
├─────────────────────────────────────────┤
│                                         │
│  ◉ 任务标题   [运行中动画]               │
│                                         │
│  任务描述... 两行截断                     │
│                                         │
│  [Agent 图标] Coder    |  ⏱️ 2m 30s     │
│           DeepSeek                       │
│                                         │
└─────────────────────────────────────────┘
  边框：蓝色实线
  左上角：蓝色实心圆 + 呼吸动画
  显示：当前 Agent、当前模型、已运行时间

┌─────────────────────────────────────────┐
│ 状态：handoff（紫色）                     │
├─────────────────────────────────────────┤
│                                         │
│  ↻ 任务标题   [交接中...]               │
│                                         │
│  正在生成交接摘要...                      │
│                                         │
│  [Agent 图标] 交接中   |  ⏱️ 5m 12s     │
│                                         │
└─────────────────────────────────────────┘
  边框：紫色实线
  左上角：紫色循环箭头 + 旋转动画
  背景：淡淡的紫色渐变

┌─────────────────────────────────────────┐
│ 状态：completed（绿色）                   │
├─────────────────────────────────────────┤
│                                         │
│  ✓ 任务标题                              │
│                                         │
│  任务描述... 两行截断                     │
│                                         │
│  [Agent 图标] Coder    |  ⏱️ 3m 45s     │
│                                         │
└─────────────────────────────────────────┘
  边框：绿色实线
  左上角：绿色对勾
  卡片可以轻微折叠（高度降低 20%）

┌─────────────────────────────────────────┐
│ 状态：failed（红色）                      │
├─────────────────────────────────────────┤
│                                         │
│  ✕ 任务标题                              │
│                                         │
│  任务描述... 两行截断                     │
│                                         │
│  [Agent 图标] 失败     |  ⏱️ 1m 20s     │
│  [重试] [交接] [详情]                     │
│                                         │
└─────────────────────────────────────────┘
  边框：红色实线
  左上角：红色叉号
  底部显示操作按钮：重试、交接、查看详情
```

### 2.3 卡片状态切换动画

```css
/* 状态变化时的闪烁效果 */
@keyframes statusChange {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.task-card.status-changing {
  animation: statusChange 0.3s ease 2;
}

/* running 状态的呼吸效果 */
@keyframes breathing {
  0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(59, 130, 246, 0); }
}

.task-card.status-running {
  animation: breathing 2s ease-in-out infinite;
}

/* handoff 状态的旋转效果 */
@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.handoff-icon {
  animation: rotating 1.5s linear infinite;
}
```

---

## 三、Agent 工位（像素视图）设计

### 3.1 工位基础布局

```
              ┌─────────────────────┐
              │   🔴 🟡 🟢 状态灯    │
              │                     │
              │      🤖 🤖 🤖       │
              │     像素小人        │
              │                     │
              │  [模型名称标签]     │
              │    Claude 3         │
              │                     │
              │  [工位名称标签]     │
              │   Planner Agent     │
              │                     │
              │  [当前任务标题]     │
              │                     │
              └─────────────────────┘
                   工位卡片
```

### 3.2 状态灯设计

每个工位有 3 个状态灯，每个灯有亮/灭两种状态：

```
      ┌───┐ ┌───┐ ┌───┐
idle: │   │ │   │ │ ○ │  只有绿灯亮（暗绿色）
      └───┘ └───┘ └───┘

      ┌───┐ ┌───┐ ┌───┐
running:│ ◉ │ │   │ │   │  蓝灯亮（亮蓝色，闪烁）
      └───┘ └───┘ └───┘

      ┌───┐ ┌───┐ ┌───┐
handoff:│   │ │ ◉ │ │   │  黄灯亮（紫色，闪烁）
      └───┘ └───┘ └───┘

      ┌───┐ ┌───┐ ┌───┐
completed:│   │ │   │ │ ◉ │  绿灯亮（亮绿色）
      └───┘ └───┘ └───┘

      ┌───┐ ┌───┐ ┌───┐
failed: │ ◉ │ │ ◉ │ │ ◉ │  三灯全红
      └───┘ └───┘ └───┘
```

### 3.3 像素小人状态动画

工位状态通过三种方式表达：工位状态灯、Worker 动作、工位上方浮动标签。

```
idle:
  工位空着，状态灯灰色
  Worker：静坐，偶尔眨眼（每 3-5 秒眨一次），双手放在桌上

queued:
  Worker：坐在工位等待，偶尔看向任务板
  状态灯：灰色

running:
  Worker：双手快速敲击键盘（循环动画），头部偶尔微动，思考时手托下巴偶尔点头
  状态灯：蓝色，闪烁
  浮动标签：显示当前 Task 标题

waiting / quota warning:
  Worker：停住或看向任务板，双手交叉或挠头
  状态灯：黄色
  浮动标签：Quota Low / Waiting

reviewing:
  Worker：手指滑动查看
  状态灯：蓝色
  浮动标签：Reviewing...

handoff:
  Worker：站起身，双手递出一个文件夹
  状态灯：紫色，闪烁
  浮动标签：Generating Handoff Summary
  交接动画：新 Worker 从门口进入，旧 Worker 将 Handoff Folder 交给新 Worker

blocked / error:
  Worker：抓头，显示警告图标
  状态灯：红色
  浮动标签：Error / Blocked

done:
  Worker：背靠椅子，双手抱头，显示 ✓ 气泡
  Worker 完成后可以淡出离开，工位保留绿色完成标记
  状态灯：绿色常亮
```

### 3.4 Completed Agents 缩略状态

Card Flow View 底部的 Completed Agents：

```
[Router ✓] [Planner ✓] [Research ✓] [Summarizer ✓]
    ↓
绿色背景 + 对勾
鼠标悬停显示简要信息
点击打开完整的 Agent Detail Modal
```

---

## 四、Handoff 交接动画

**这是产品的核心差异化动画，必须做的流畅且有仪式感。**

### 4.1 完整的 Handoff 动画流程

```
阶段 1：触发（0s - 0.5s）
  原 Agent 工位的状态灯从蓝 → 紫
  原小人停止工作，抬头
  原任务卡片开始发光（紫色光晕）

阶段 2：生成摘要（0.5s - 2s）
  原小人工位出现「生成摘要中...」文字
  小人面前出现一个「文件夹」图标，逐渐清晰
  进度条缓慢增长（模拟生成过程）

阶段 3：传递（2s - 3s）
  原小人拿起文件夹，站起身
  文件夹沿着贝塞尔曲线飞向目标工位
  飞行轨迹带紫色流光拖尾
  目标工位的小人伸手准备接

阶段 4：接手（3s - 4s）
  目标小人接住文件夹
  目标小人坐下
  目标工位状态灯变蓝
  文件夹融入目标小人的任务区
  出现「交接完成」提示

阶段 5：继续工作（4s 后）
  目标小人开始工作动画
  原小人恢复 idle 或离开（视情况）
```

### 4.2 动画参数

```css
/* 文件夹飞行动画 */
@keyframes folderFly {
  0% {
    transform: translate(0, 0) scale(1);
    opacity: 1;
  }
  50% {
    transform: translate(var(--fly-x), var(--fly-y) - 50px) scale(1.2);
    opacity: 1;
  }
  100% {
    transform: translate(var(--fly-x), var(--fly-y)) scale(1);
    opacity: 1;
  }
}

/* 拖尾效果 */
.folder-trail {
  position: absolute;
  width: 8px;
  height: 8px;
  background: rgba(139, 92, 246, 0.6);
  border-radius: 50%;
  filter: blur(2px);
  animation: fadeOut 0.5s ease forwards;
}

@keyframes fadeOut {
  to { opacity: 0; transform: scale(0.5); }
}
```

---

## 五、任务流转线（卡片视图）

卡片之间的连线表示任务流转关系。

### 5.1 连线完整样式

连线颜色：

```
灰色虚线：计划中的任务流
蓝色实线：正在执行的任务流
绿色实线：已完成的任务流
黄色虚线：等待或阻塞
紫色动画线：正在 Handoff
红色断裂线：出错或失败
```

连线样式规则：

```
虚线：尚未执行
实线：已经发生
流动动画线：正在发生
断裂线：失败
```

### 5.2 连线 CSS 定义

```css
.task-connection-line {
  stroke-width: 2;
  fill: none;
  transition: stroke 0.3s ease, stroke-dasharray 0.3s ease;
}

/* 计划中 - 灰色虚线 */
.task-connection-line.planned {
  stroke: $status-idle;
  stroke-dasharray: 5 5;
}

/* 执行中 - 蓝色实线 + 流动动画 */
.task-connection-line.running {
  stroke: $status-running;
  animation: lineFlow 2s linear infinite;
}

@keyframes lineFlow {
  0% { stroke-dashoffset: 0; }
  100% { stroke-dashoffset: -20; }
}

/* 完成 - 绿色实线 */
.task-connection-line.completed {
  stroke: $status-completed;
}

/* 等待/阻塞 - 黄色虚线 */
.task-connection-line.waiting {
  stroke: $status-pending;
  stroke-dasharray: 5 5;
}

/* Handoff - 紫色动画线 */
.task-connection-line.handoff {
  stroke: $status-handoff;
  animation: linePulse 1.5s ease-in-out infinite;
}

@keyframes linePulse {
  0%, 100% { stroke-opacity: 0.4; }
  50% { stroke-opacity: 1; }
}

/* 失败 - 红色断裂线 */
.task-connection-line.error {
  stroke: $status-failed;
  stroke-dasharray: 2 8;
}
```

### 5.3 连线箭头

连线的终点有箭头，指向下一个 Task。

```
Planner ────▶ Coder
```

箭头颜色跟随前置 Task 的状态。

### 5.4 Handoff Summary Card

当 Handoff 发生时，两个 Agent Card 之间出现小型 Handoff Summary Card：

```
┌──────────────┐   ┌─────────────────┐   ┌──────────────┐
│ Claude Coder │──▶│ Handoff Summary │──▶│ GPT Coder    │
│ Quota Low    │   │                 │   │ Loading...   │
└──────────────┘   └─────────────────┘   └──────────────┘
        ↓                    ↓                    ↓
    紫色边框            紫色动画连线            紫色边框
```

---

## 六、交互规则

### 6.1 Card Flow View 点击交互

点击 Agent Card：

```
打开 Agent Detail Modal
背景虚化
其他 Agent 暂时不可点击
右上角 X 关闭
点击遮罩关闭
Esc 关闭
```

Agent Detail Modal 有 5 个 Tab：

```
Overview / Task / Context / Tools / History
```

### 6.2 Pixel Office View 点击交互

点击像素工位：

```
不打开中心 Modal
而是在像素办公室内部出现内嵌式详情框 Station Popover
不虚化整个页面
其他像素区域仍然可见
点击 X 关闭
点击空白区域关闭
点击另一个工位时，详情框切换到另一个工位
```

Station Popover 内容（轻量级）：

```
Station: Coder
Worker: DeepSeek
Task: 实现 Agent Card
Status: Running
Next: Send to Reviewer

[View Full Detail] [View Logs] [Generate Handoff] [Pause]
```

点击 View Full Detail 后，再打开完整 Agent Detail Modal。

### 6.3 Completed Agents 缩略区交互

主视图底部的 Completed Agents 缩略区：

```
[Router ✓] [Planner ✓] [Research ✓] [Summarizer ✓]
```

点击缩略卡片：

```
打开 Agent Detail Modal
查看历史输出、模型调用、工具调用、Handoff 记录
```

### 6.4 视图切换

```
点击「视图切换」按钮时：
  1. 当前视图淡出（0.3s）
  2. 显示 loading 状态（0.2s）
  3. 新视图淡入（0.3s）

Pixel Office 切换加载提示：
  Preparing Pixel Office...
  正在同步 Agent 状态
  正在加载工位资源
  正在放置 Worker

两个视图共享同一套数据，切换时：
  - 选中的 Task / Agent 保持选中
  - 正在播放的动画平滑过渡到新视图
  - 正在 Handoff 的状态正确同步
```

### 6.5 右键菜单（v0.2，MVP可以推迟）

右键点击 Task 卡片显示菜单：

```
┌───────────────────────┐
│ ▶️  重新运行           │
│ 🔄  交接给其他 Agent   │
│ 📋  复制输出           │
│ 📜  查看完整日志       │
│ ⏭️  跳过此任务         │
│ 🗑️  取消任务           │
└───────────────────────┘
```

MVP 先做按钮，右键菜单推迟。

---

## 七、日志区动效

### 7.1 新日志出现

```
新日志条目从下方滑入：
  - 高度从 0 → 自然高度（0.2s）
  - 透明度从 0 → 1（0.2s）
  - 背景色闪烁一下对应颜色（0.3s）

例如，一条 error 日志出现时，背景先红一下再恢复正常。
```

### 7.2 日志级别颜色

```
info:    灰色文字
exec:    蓝色文字
done:    绿色文字
handoff: 紫色文字
warn:    黄色文字，背景浅黄色
error:   红色文字，背景浅红色
```

---

## 八、v0.1 简化策略

为了快速交付 MVP，v0.1 可以按这个优先级实现：

### P0 - 必须有

```
✅ Task 卡片的 5 种状态颜色（灰/蓝/紫/绿/红）
✅ 卡片上的状态图标（○/◉/↻/✓/✕）
✅ 点击卡片高亮
✅ 卡片悬停效果
✅ running 状态的呼吸动画
✅ handoff 状态的旋转图标
```

### P1 - 应该有

```
⏳ 像素视图的小人基础动画（idle/running）
⏳ 像素视图的状态灯
⏳ Task 之间的连线（静态）
⏳ 日志条目出现动画
⏳ Handoff 的基础动画
```

### P2 - 可以推迟

```
⏳ 完整的 Handoff 文件夹飞行动画
⏳ 像素小人的复杂表情动画
⏳ 任务连线的动态效果
⏳ 右键菜单
⏳ 双击展开卡片
```

---

## 九、性能与可用性原则

### 9.1 性能

```
1. 所有动画使用 CSS transform 和 opacity，避免触发重排
2. 运行中的动画总数不超过 5 个
3. 列表使用虚拟滚动（超过 50 个 Task 时）
4. 像素视图超过 10 个工位时，离屏的工位暂停动画
```

### 9.2 无障碍

```
1. 颜色不是唯一的状态标识，必须同时有图标
   （色盲用户可以通过图标区分状态）

2. 状态变化有文字提示
   （屏幕阅读器可以读出状态变更）

3. 动画可以关闭
   （提供「减少动画」开关，尊重用户的系统设置）
```

### 9.3 响应式

```
1. 卡片宽度自适应容器
2. 小屏幕下卡片单列排列
3. 工位视图在小屏幕下可以缩放和拖拽平移
```

---

## 十、验收标准

UI 状态系统 v0.1 完成的标志：

```
✅ Agent Card 可以正确显示 9 种状态
✅ 颜色和图标与设计一致
✅ running 状态有呼吸效果
✅ handoff 状态有旋转动画
✅ 连线可以正确显示 6 种状态样式
✅ 点击 Card 打开 Agent Detail Modal
✅ Modal 可以正确显示 5 个 Tab
✅ 状态变更时有平滑的过渡动画
✅ Completed Agents 缩略到底部
✅ Handoff Summary Card 显示在两个 Agent 之间
✅ Pixel Office 可以显示工位和小人
✅ Pixel Office 状态灯正确显示 9 种状态
✅ 点击 Pixel Office 工位打开 Station Popover
✅ 点击 View Full Detail 打开完整 Modal
✅ Handoff 时有文件夹交接动画
✅ 视图切换流畅，状态完全同步
✅ 日志区新条目可以平滑出现
```
