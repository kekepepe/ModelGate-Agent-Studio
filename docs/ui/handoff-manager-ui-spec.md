# Handoff Manager UI 设计规范

> 所属产品：ModelGate Agent Studio
>
> 关联文档：agent-workspace-ui-spec.md（共享设计系统）
>
> 文档定位：Handoff Manager 前端 UI 设计规范，覆盖列表页、详情抽屉、状态标签、空状态与失败状态。不包含代码实现。

---

## 1. Design Read

**Reading this as:** B2B developer-tool handoff management surface for multi-model power users, with a calm / structured / utility-first language, leaning toward the same warm-neutral system as Agent Workspace (Stone surface + muted functional accents + high information density).

---

## 2. Three Dials

| Dial                 | Value | Rationale                                                                           |
| -------------------- | ----- | ----------------------------------------------------------------------------------- |
| `DESIGN_VARIANCE`  | 4     | Tool surface; symmetrical table layouts with asymmetric detail panels.              |
| `MOTION_INTENSITY` | 3     | Functional only: status transitions, drawer slide, row hover. No decorative motion. |
| `VISUAL_DENSITY`   | 6     | Management page; dense tabular data with expandable detail drawers.                 |

---

## 3. 信息架构（4 层）

Handoff Manager 需要在一个页面内回答三个核心问题：**为什么交接、交给了谁、接手后怎样**。信息按 4 层组织：

| 层级                     | 作用                               | 承载位置                                      |
| ------------------------ | ---------------------------------- | --------------------------------------------- |
| **L1 — 全局筛选** | 让用户从大量记录中定位目标         | 列表页顶部 Filter Bar                         |
| **L2 — 列表摘要** | 一眼看到交接双方、原因、状态、结果 | 列表页 Table / Row                            |
| **L3 — 详情抽屉** | 查看完整摘要、时间线、参与者、结果 | HandoffDetailDrawer                           |
| **L4 — 审计追踪** | 追溯交接全过程的日志事件           | ExecutionLogPanel（已有组件，本文不重复设计） |

---

## 4. 页面布局

### 4.1 列表页（HandoffPage）

路由：`/handoffs`（MVP-B 阶段提供）

```
+-------------------------------------------------------------+
|  Page Header                                                |
|  [Handoffs]              [筛选面板]                        |
+-------------------------------------------------------------+
|  Filter Bar                                                 |
|  [Goal ▼] [Task ▼] [Reason ▼] [Status ▼] [From ▼] [To ▼]   |
+-------------------------------------------------------------+
|                                                             |
|  Handoff List Table                                        |
|  +------------------------------------------------------+  |
|  | Goal / Task | From → To | Reason | Status | Result | Created | ▶ |  |
|  +------------------------------------------------------+  |
|  | ... rows ...                                          |  |
|  +------------------------------------------------------+  |
|                                                             |
|  [← Prev]  Page 1 / 12  [Next →]                           |
+-------------------------------------------------------------+
```

**布局规则：**

- 页面最大宽度 `max-w-[1400px] mx-auto`，避免超宽屏表格拉伸导致阅读困难。
- 列表采用 Table 形式，非卡片。管理型数据表格比卡片更高效。
- 每行高度 56px，行与行之间用 `border-b` 分隔，不使用斑马纹。
- Hover 行时背景变为 `bg-stone-50`，过渡 150ms。
- 点击整行打开 Detail Drawer，整行是热区。
- 每行最右侧保留一个 chevron-right 图标，提示可展开。

**列宽分配（桌面端 ≥1280px）：**

| 列          | 宽度                  | 说明                                    |
| ----------- | --------------------- | --------------------------------------- |
| Goal / Task | flex-1, min-w-[280px] | 左对齐，Goal 名主文本，Task 名次文本    |
| From → To  | 200px                 | 居中，箭头连接双方 Agent 名             |
| Reason      | 120px                 | 居中，状态标签样式                      |
| Status      | 120px                 | 居中，彩色状态标签                      |
| Result      | 100px                 | 居中，结果标签（仅 completed 状态显示） |
| Created     | 140px                 | 右对齐，相对时间（"2h ago"）            |
| ▶          | 48px                  | 固定，展开图标                          |

**列宽分配（平板 768px–1279px）：**

- 隐藏 Created 列
- Reason 列收窄至 100px

**移动端（<768px）：**

- 表格退化为卡片列表
- 每张卡片包含：Goal 名、From→To、Status 标签、Created 时间
- 点击卡片进入独立详情页（非抽屉，因屏幕宽度不足）

---

### 4.2 详情抽屉（HandoffDetailDrawer）

从右侧滑出，桌面端宽度 560px，平板 480px，移动端全屏。

```
+------------------------------------------------------------+
|  [×]  Handoff #handoff-abc12                    [复制]    |
+------------------------------------------------------------+
|  Status: [generating_summary]                              |
|  Reason: [quota_exceeded]          Created: 2h ago        |
+------------------------------------------------------------+
|  PARTICIPANTS                                              |
|  +----------------+     +----------------+                |
|  | Coder Agent    | --> | Reviewer Agent |                |
|  | Claude         |     | GPT-4          |                |
|  +----------------+     +----------------+                |
+------------------------------------------------------------+
|  TIMELINE                                                  |
|  ● requested          2h ago                              |
|  ● generating_summary 1h 58m ago                          |
|  ○ ready              —                                   |
|  ○ accepted           —                                   |
|  ○ completed          —                                   |
+------------------------------------------------------------+
|  HANDOFF SUMMARY                                           |
|  ┌─ Original Goal ─────────────────────────────────────┐  |
|  | 实现用户登录模块的 JWT 认证...                        |  |
|  └─────────────────────────────────────────────────────┘  |
|  ┌─ Current Task ─────────────────────────────────────┐  |
|  | 编写登录接口的单元测试...                             |  |
|  └─────────────────────────────────────────────────────┘  |
|  ┌─ Completed Work ───────────────────────────────────┐  |
|  | • 已完成用户模型设计                                  |  |
|  | • 已完成登录接口基础实现                              |  |
|  └─────────────────────────────────────────────────────┘  |
|  ┌─ Unfinished Work ──────────────────────────────────┐  |
|  | • 单元测试覆盖率达到 80%                             |  |
|  | • 错误处理边界情况                                   |  |
|  └─────────────────────────────────────────────────────┘  |
|  ... (其余 Summary 字段)                                   |
+------------------------------------------------------------+
|  RESULT                                                    |
|  [尚未记录结果]                                             |
+------------------------------------------------------------+
```

**抽屉布局规则：**

- 头部固定，内容区可滚动。
- 滚动时头部保留底部阴影 `shadow-sm`，形成层级。
- 内容区分段，每段用 24px 间距分隔。
- 段标题：12px  uppercase，字重 600，颜色 `text-stone-400`，letter-spacing 0.05em。
- Summary 各字段用卡片式包裹：白色面板 + 1px `stone-200` 边框 + 8px 圆角 + 16px padding。
- 数组类型字段（completed_work[] 等）用列表展示，每项前有 `•` 或对应图标。
- 空字段显示 `—`（em dash），颜色 `text-stone-300`，不显示空白。

---

## 5. 组件规范

### 5.1 StatusTag（状态标签）

用于列表和抽屉中展示 HandoffStatus 和 HandoffResult。

**形态：**

- 高度 24px，水平内边距 10px
- 圆角 999px（pill）
- 字体 12px，字重 500
- 左侧可带 6px 圆点指示器（可选）

**颜色映射：**

| 状态                   | 背景色                   | 文字色                   | 圆点         | 说明         |
| ---------------------- | ------------------------ | ------------------------ | ------------ | ------------ |
| `requested`          | `#fef3c7` (琥珀-100)   | `#92400e` (琥珀-800)   | 琥珀圆点     | 等待处理     |
| `generating_summary` | `#ede9fe` (薰衣草-100) | `#5b4ba4` (薰衣草-800) | 紫色脉动圆点 | 唯一脉动动画 |
| `ready`              | `#ede9fe` (薰衣草-100) | `#5b4ba4` (薰衣草-800) | 紫色圆点     | 可接受       |
| `accepted`           | `#e0f2fe` (天蓝-100)   | `#0369a1` (天蓝-700)   | 蓝色圆点     | 已接受       |
| `completed`          | `#dcfce7` (鼠尾草-100) | `#166534` (鼠尾草-800) | 绿色圆点     | 已完成       |
| `failed`             | `#fee2e2` (砖红-100)   | `#991b1b` (砖红-800)   | 红色圆点     | 失败         |

**Result 标签（仅在 completed 状态后展示）：**

| 结果        | 背景色      | 文字色      |
| ----------- | ----------- | ----------- |
| `success` | `#dcfce7` | `#166534` |
| `partial` | `#fef3c7` | `#92400e` |
| `failed`  | `#fee2e2` | `#991b1b` |

**脉动动画（generating_summary 专属）：**

- 圆点执行 `scale(1) → scale(1.4) → scale(1)`，opacity `1 → 0.6 → 1`
- 周期 2s，ease-in-out，infinite
- 整个标签背景可有极微弱的 opacity 脉动（1 → 0.85 → 1），同周期，营造"正在工作中"的感知

---

### 5.2 ParticipantArrow（交接双方可视化）

用于详情抽屉的 PARTICIPANTS 区块，清晰表达"从谁交给谁"。

```
+---------------+         +---------------+
| [Avatar]      |    →    | [Avatar]      |
| Coder Agent   |  ----   | Reviewer Agent|
| Claude        |         | GPT-4         |
+---------------+         +---------------+
```

**规则：**

- 双方各用一个竖向卡片展示：Avatar（32px 圆）+ Agent 名（14px 字重 500）+ Model 名（12px `text-stone-400`）
- 中间用水平箭头连接，箭头颜色 `stone-300`，线条 2px
- 箭头上方可悬浮交接原因标签（如 "quota_exceeded"）
- From 卡片边框使用 `stone-200`，To 卡片边框使用 Handoff 主题色（`#8b7ec8` 低饱和紫），暗示"这是接收方"
- 若 Handoff 已完成，箭头颜色变为 `stone-400`，增加实感

---

### 5.3 Timeline（时间线）

用于详情抽屉展示 Handoff 状态流转历史。

**规则：**

- 垂直时间线，左侧圆点 + 右侧文本
- 已完成节点：实心圆点，颜色对应状态色
- 当前节点：实心圆点 + 微弱光晕（box-shadow，同状态色，opacity 0.3）
- 未到达节点：空心圆点，`border-2 stone-200`，内部空白
- 节点间用 2px 竖线连接，已完成段实线（状态色），未完成段虚线（`stone-200`）
- 时间文本右对齐，12px，`text-stone-400`
- 每个节点显示：状态名 + 时间戳

---

### 5.4 SummarySection（摘要字段卡片）

用于详情抽屉中展示 HandoffSummary 的 9 个字段。

**规则：**

- 每个字段一个卡片，白色背景 + 1px `stone-200` 边框 + 8px 圆角
- 卡片内标题：12px 字重 600，`text-stone-500`，上方带对应图标（16px）
- 卡片内内容：14px，`text-stone-700`，行高 1.6
- 数组类型：每项一行，左侧 `•` 或对应图标（如 completed_work 用 check-circle，errors_and_risks 用 alert-circle）
- 字符串类型：直接展示，允许换行
- 空值：显示 `—`，居中，`text-stone-300`

**字段图标映射：**

| 字段                  | 图标          | 图标色               |
| --------------------- | ------------- | -------------------- |
| original_goal         | Target        | `stone-400`        |
| current_task          | FileText      | `stone-400`        |
| completed_work        | CheckCircle   | `#166534` (鼠尾草) |
| unfinished_work       | Circle        | `#92400e` (琥珀)   |
| important_constraints | Shield        | `#0369a1` (天蓝)   |
| key_decisions         | GitBranch     | `stone-400`        |
| errors_and_risks      | AlertTriangle | `#991b1b` (砖红)   |
| next_suggested_steps  | ArrowRight    | `stone-400`        |
| context_needed        | HelpCircle    | `stone-400`        |

---

### 5.5 HandoffRow（列表行）

用于列表页展示单条 Handoff 记录。

**规则：**

- 整行高度 56px，垂直居中
- Goal 名：14px 字重 500，`text-stone-800`，单行截断
- Task 名：12px `text-stone-400`，单行截断，位于 Goal 名下方
- From → To：双方 Agent 名用 12px 字重 500 展示，中间用右箭头图标（16px，`stone-300`）连接
- Reason：StatusTag 样式，pill，但尺寸缩小（高 20px，字号 11px）
- Status：标准 StatusTag
- Result：标准 StatusTag（仅在 completed 时显示，否则留空）
- Created：12px `text-stone-400`，使用相对时间
- 整行 hover：`bg-stone-50`，过渡 150ms
- 点击热区：整行（除复制等操作按钮外）

---

## 6. 空状态

### 6.1 列表空状态（无交接记录）

```
+---------------------------------------------------+
|                                                   |
|                [Icon: ArrowLeftRight]              |
|                                                   |
|         No handoff records yet                    |
|                                                   |
|   Handoffs happen when a task is transferred      |
|   from one agent or model to another.             |
|   Trigger your first handoff from the Workspace.  |
|                                                   |
|          [Go to Workspace]                        |
|                                                   |
+---------------------------------------------------+
```

**规则：**

- 图标：48px，`text-stone-300`
- 标题：16px 字重 500，`text-stone-600`
- 描述：14px `text-stone-400`，最大宽度 400px，居中，行高 1.5
- 按钮：链接样式或次按钮，跳转 Workspace
- 当筛选条件导致无结果时，显示 "No results match your filters" + [Clear Filters] 按钮

### 6.2 摘要生成中状态（抽屉内）

当 Handoff 处于 `generating_summary` 状态时打开抽屉：

- Summary 区域显示占位骨架屏：3 行文本脉冲动画，高度 16px，间距 8px，圆角 4px，颜色 `stone-200`
- 顶部显示提示条："Generating summary... This may take a few seconds."，背景 `lavender-50`，文字 `lavender-800`，左侧 spinner 图标
- 已生成的字段（如 original_goal 可能有兜底值）正常展示，未生成的字段显示骨架屏

### 6.3 摘要生成失败状态

当 Handoff 处于 `failed` 状态且失败原因是 summary 生成失败时：

- 抽屉顶部显示错误提示条：背景 `brickred-50`，左侧 AlertTriangle 图标，`brickred-800` 文字
- 错误内容："Summary generation failed. A fallback summary has been provided."
- Summary 区域展示兜底摘要（Fallback Summary），用区别于正常摘要的样式：背景 `stone-50`，边框 `stone-200`，顶部标注 "Fallback Summary"
- 提供 [Retry Generate] 按钮（MVP-B 阶段）

---

## 7. 失败状态设计

### 7.1 Handoff 失败（状态 = failed）

列表页：

- 整行背景保持白色，不特殊变色（避免满屏红色焦虑）
- Status 标签为红色 failed
- Result 列留空（因未到达 completed）
- 行左侧可有一个 3px 宽红色竖条作为弱提示（`border-l-3 border-red-700`）

抽屉内：

- 头部 Status 为红色 failed 标签
- 错误原因（如果有）以 AlertBanner 形式展示在头部下方
- Timeline 中失败节点用红色实心圆点，若知道失败发生在哪一步，该步之前的连线为实线，之后的为虚线
- 若失败发生在 `generating_summary` 阶段，Summary 区域展示兜底数据并标注 Fallback

### 7.2 重复 Handoff 冲突

Workspace 内触发时：

- [Handoff] 按钮禁用，`opacity-50`，cursor not-allowed
- Hover 禁用按钮时显示 Tooltip："An active handoff already exists for this task"
- 若用户通过 API 直接调用触发 409，显示 Toast 错误：红色左侧竖条 + 错误文案 + 关闭按钮

### 7.3 接手后任务再次失败

Handoff 已完成（completed），但 `result_after_handoff = failed`：

- 列表页 Result 标签为红色 failed
- 抽屉内 Result 区域用 AlertBanner 展示："The task failed after handoff."
- 显示 `result_note`（如果有）
- 提供快捷操作：[View Task] 跳转对应 Task 详情

---

## 8. 交互动效

| 场景                    | 动效                                                                            | 时长       | 缓动                             |
| ----------------------- | ------------------------------------------------------------------------------- | ---------- | -------------------------------- |
| 抽屉打开                | 从右侧 `translateX(100%) → translateX(0)`，同时背景遮罩 `opacity 0 → 0.3` | 300ms      | `cubic-bezier(0.4, 0, 0.2, 1)` |
| 抽屉关闭                | 反向                                                                            | 250ms      | `cubic-bezier(0.4, 0, 0.2, 1)` |
| 列表行 hover            | `bg-stone-50`                                                                 | 150ms      | ease                             |
| StatusTag 状态切换      | 背景色 + 文字色渐变                                                             | 300ms      | ease                             |
| generating_summary 脉动 | 圆点 scale + opacity                                                            | 2s         | ease-in-out, infinite            |
| Timeline 节点到达       | 新节点从上方滑入 8px + opacity 0→1                                             | 300ms      | ease-out                         |
| Summary 卡片展开        | 高度 0 → auto（若有折叠功能）                                                  | 250ms      | ease                             |
| 空状态出现              | 整体 opacity 0→1 + translateY(8px→0)                                          | 400ms      | ease-out                         |
| 骨架屏脉冲              | 背景色 opacity 波动                                                             | 1.5s       | ease-in-out, infinite            |
| 复制成功反馈            | 按钮文本短暂变为 "Copied" + check 图标，2s 后恢复                               | 200ms / 2s | ease                             |

**动效原则：**

- 所有动效都是功能性的，没有装饰性动画。
- `generating_summary` 的脉动是唯一持续动画，用于表达"后台正在工作"。
- 失败状态不使用抖动动画，使用颜色和静态图标表达即可，避免制造焦虑。

---

## 9. 响应式策略

| 断点              | 布局变化                                                           |
| ----------------- | ------------------------------------------------------------------ |
| `≥1280px`      | 完整 7 列表格，抽屉 560px                                          |
| `768px–1279px` | 隐藏 Created 列，抽屉 480px                                        |
| `<768px`        | 表格退化为卡片列表；点击卡片进入独立详情页（非抽屉），顶部返回按钮 |

---

## 10. 颜色令牌（与 Agent Workspace 共享）

Handoff Manager 复用 Agent Workspace 的设计系统，新增/复用以下令牌：

| 令牌                        | 值                  | 用途                         |
| --------------------------- | ------------------- | ---------------------------- |
| `surface`                 | `#fafaf9`         | 页面背景                     |
| `panel`                   | `#ffffff`         | 卡片、抽屉面板               |
| `border-default`          | `#e7e5e4`         | 卡片边框、表格分隔线         |
| `text-primary`            | `#1c1917`         | 标题、主文本                 |
| `text-secondary`          | `#57534e`         | 次要文本                     |
| `text-tertiary`           | `#a8a29e`         | 时间戳、占位符               |
| `handoff-lavender-bg`     | `#ede9fe`         | handoff 状态标签背景         |
| `handoff-lavender-text`   | `#5b4ba4`         | handoff 状态标签文字         |
| `handoff-lavender-border` | `#8b7ec8`         | To Agent 卡片边框、手气紫    |
| `amber-bg`                | `#fef3c7`         | requested 标签背景           |
| `amber-text`              | `#92400e`         | requested 标签文字           |
| `sky-bg`                  | `#e0f2fe`         | accepted 标签背景            |
| `sky-text`                | `#0369a1`         | accepted 标签文字            |
| `sage-bg`                 | `#dcfce7`         | completed / success 标签背景 |
| `sage-text`               | `#166534`         | completed / success 标签文字 |
| `brick-bg`                | `#fee2e2`         | failed 标签背景              |
| `brick-text`              | `#991b1b`         | failed 标签文字              |
| `overlay`                 | `rgba(0,0,0,0.3)` | 抽屉遮罩                     |

**注意：** 不使用高饱和紫色（如 `#9333ea`）。所有 handoff 相关紫色均使用低饱和薰衣草色系（`#ede9fe` / `#5b4ba4`），与 Workspace 中 TaskCard handoff 状态保持一致。

---

## 11. 字体规范

复用 Agent Workspace 字体系统：

- 字体族：`Geist`（正文）+ `Geist Mono`（ID、时间戳、代码片段）
- 列表 Goal 名：14px / 500 / `text-stone-800`
- 列表 Task 名：12px / 400 / `text-stone-400`
- 抽屉标题：18px / 600 / `text-stone-900`
- 段标题：12px / 600 / uppercase / `text-stone-400` / tracking-wide
- Summary 卡片标题：12px / 600 / `text-stone-500`
- Summary 卡片内容：14px / 400 / `text-stone-700` / leading-relaxed
- 状态标签：12px / 500
- 时间戳 / ID：12px / 400 / `Geist Mono` / `text-stone-400`

---

## 12. 交互规则摘要

### 12.1 列表页交互

- 点击行 → 打开 Detail Drawer
- 点击筛选条件下拉 → 展开筛选面板（多选用 checkbox 列表，单选用 radio 列表）
- 点击表头 → 按该列排序（Created 默认倒序）
- 分页：上一页 / 下一页，页码输入框

### 12.2 抽屉交互

- 点击遮罩 / 按 ESC / 点击 [×] → 关闭抽屉
- 点击 [复制] → 复制 Handoff ID 到剪贴板，按钮文本短暂变为 "Copied"
- 点击 Timeline 节点 → 无操作（仅展示）
- 若 Status = `ready`，抽屉底部显示 [Accept Handoff] 主按钮（MVP-A 阶段用户手动 accept）
- 若 Status = `completed` 且 result 未记录，显示 Result 编辑区域（下拉 + 备注 + 保存）
- 内容区滚动时，头部和底部操作栏固定（sticky）

### 12.3 与 Workspace 的衔接

- 列表页点击 "Go to Workspace" 跳转 `/workspace`
- Workspace 中点击 Handoff Summary Card 或 TaskCard HandoffIndicator 打开同一个 HandoffDetailDrawer 组件
- 抽屉组件在 Workspace 和 HandoffPage 中复用，行为完全一致

---

## 13. P0 vs P1 设计范围

| 功能                               | 优先级 | MVP 阶段 | 说明                                  |
| ---------------------------------- | ------ | -------- | ------------------------------------- |
| Workspace 内 Handoff 触发面板      | P0     | MVP-A    | HandoffConfirmModal                   |
| Workspace 内 TaskCard Handoff 状态 | P0     | MVP-A    | 紫色边框 + HandoffStatusIndicator     |
| Handoff Detail Drawer              | P0     | MVP-A    | 查看 Summary、时间线、参与者          |
| Handoff 接受交接 UI                | P0     | MVP-A    | Accept 按钮 + Worker 切换             |
| ExecutionLogPanel Handoff 日志     | P0     | MVP-A    | 紫色标签                              |
| Handoff 列表页                     | P1     | MVP-B    | 独立 `/handoffs` 页面               |
| Handoff 列表筛选                   | P1     | MVP-B    | Goal / Task / Reason / Status / Agent |
| Handoff 列表分页                   | P1     | MVP-B    | page / page_size                      |
| Result 手动标记                    | P1     | MVP-B    | 下拉 + 备注                           |
| Regenerate Summary                 | P1     | MVP-B    | [Retry Generate] 按钮                 |

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
>
> 相关文档：
>
> - agent-workspace-ui-spec.md — 共享设计系统与颜色令牌
> - `docs/prd/handoff-manager-prd.md` — 产品需求
> - `docs/stories/handoff-manager-stories.md` — 用户故事
> - `docs/tasks/handoff-manager-tasks.md` — 开发任务（HM-T6.2 对应本文列表页）
