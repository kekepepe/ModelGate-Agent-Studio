# Quota Manager UI 设计规范

> 所属产品：ModelGate Agent Studio
>
> 关联文档：`docs/design/agent-workspace-frontend-design.md`（共享设计系统）
>
> 文档定位：Quota Manager 前端 UI 设计规范，覆盖额度概览、模型状态面板、预警条、RiskBadge、额度设置。不包含代码实现。

---

## 1. Design Read

**Reading this as:** B2B developer-tool quota monitoring surface for multi-model power users, with a structured / calm / utility-first language, leaning toward the same warm-neutral system as Agent Workspace (Stone surface + muted functional accents + high information density).

**核心设计原则：** 不做财务报表。用颜色梯度和进度条一眼传达风险，让用户在 3 秒内判断哪个模型正常、哪个接近限制、哪个不可用。

---

## 2. Three Dials

| Dial | Value | Rationale |
|------|-------|-----------|
| `DESIGN_VARIANCE` | 4 | Tool surface; symmetrical summary cards + list layout, minimal visual variance. |
| `MOTION_INTENSITY` | 3 | Functional only: status transitions, progress bar fills, alert banner slide-in. |
| `VISUAL_DENSITY` | 6 | Monitoring page; summary cards + dense list rows + expandable detail. |

---

## 3. 信息架构（3 层）

Quota Manager 需要让用户在 3 秒内判断全局风险。信息按 3 层组织：

| 层级 | 作用 | 承载位置 |
|------|------|----------|
| **L1 — 全局摘要** | 一眼看到有几个模型正常/警告/受限 | 页面顶部 4 个 Summary Cards |
| **L2 — 模型状态列表** | 逐个查看每个模型的使用率、状态、最近调用 | 模型列表 / 可展开行 |
| **L3 — 单模型详情** | 查看使用统计、风险记录、额度设置、状态历史 | ModelUsageCard（展开面板） |

---

## 4. 页面布局

### 4.1 概览页（QuotaOverviewPage）

路由：`/quota`

```
+-------------------------------------------------------------+
|  Page Header                                                |
|  [Quota Manager]                               [刷新] [设置] |
|  监控所有模型的额度使用状态和风险级别                        |
+-------------------------------------------------------------+
|  Summary Cards                                              |
|  +-----------+ +-----------+ +-----------+ +-----------+   |
|  | 正常      | | 警告      | | 受限      | | 未知      |   |
|  |    5      | |    2      | |    1      | |    2      |   |
|  | ● 绿色   | | ● 黄色   | | ● 红色   | | ● 灰色   |   |
|  +-----------+ +-----------+ +-----------+ +-----------+   |
+-------------------------------------------------------------+
|  Filter Bar                                                 |
|  [搜索模型...] [Provider ▼] [Status ▼] [排序: 使用率 ▼]    |
+-------------------------------------------------------------+
|                                                             |
|  Model Usage List                                           |
|  +------------------------------------------------------+  |
|  | ● gpt-4o       ████████████░░  78%  WARNING   2m ago |  |
|  | ● claude-3.5   ██████████████  95%  NEAR_LIMIT 5m ago|  |
|  | ● deepseek     ██████░░░░░░░░  45%  NORMAL    1h ago |  |
|  | ● kimi-k2      ░░░░░░░░░░░░░░   --   UNKNOWN    --   |  |
|  | ● gpt-4        ██████████████ 100%  LIMITED   30m ago|  |
|  +------------------------------------------------------+  |
|                                                             |
+-------------------------------------------------------------+
```

**布局规则：**
- 页面最大宽度 `max-w-[1400px] mx-auto`。
- 顶部 4 个 Summary Cards 水平排列，等宽，间距 16px。
- 列表采用紧凑行形式，每行高度 56px。
- 行与行之间用 `border-b` 分隔，不使用斑马纹。
- Hover 行时背景变为 `bg-stone-50`，过渡 150ms。
- 点击整行展开 ModelUsageCard（accordion 展开，高度动画）。

**列表列宽分配（桌面端 ≥1280px）：**

| 列 | 宽度 | 说明 |
|----|------|------|
| 状态圆点 | 32px | 左侧 12px 圆点 |
| 模型名 | flex-1, min-w-[200px] | 模型名 14px 字重 500 + provider 12px 次要文字 |
| 使用率进度条 | 200px | 水平进度条 + 百分比数字 |
| 状态标签 | 120px | QuotaStatusTag |
| 总 tokens | 140px | 右对齐，12px `Geist Mono` |
| 最近调用 | 120px | 右对齐，相对时间 |

**移动端（<768px）：**
- 列表退化为卡片，每张卡片包含：模型名、状态标签、进度条、最近调用时间
- 点击卡片进入独立详情页（底部 Sheet）

---

### 4.2 模型详情展开面板（ModelUsageCard）

点击列表行后，下方展开详情面板，不占用独立空间。

```
+-------------------------------------------------------------+
| ● claude-3.5-sonnet   ██████████████  95%  NEAR_LIMIT       |
+-------------------------------------------------------------+
| 展开详情：                                                  |
| ┌─ 使用率 ─────────────────────────────────────────────┐   |
| | ████████████████████░░░░  95%                        |   |
| | 已用 950K / 上限 1M tokens                           |   |
| | 额度模式: known  |  重置周期: monthly                |   |
| └──────────────────────────────────────────────────────┘   |
|                                                             |
| ┌─ 使用统计 ───────────────────────────────────────────┐   |
| | 调用次数        1,234 次                              |   |
| | Input tokens    600K                                  |   |
| | Output tokens   350K                                  |   |
| | 总 tokens       950K                                  |   |
| | 最近使用        2 分钟前                              |   |
| └──────────────────────────────────────────────────────┘   |
|                                                             |
| ┌─ 风险记录 ───────────────────────────────────────────┐   |
| | ⚠ 3 小时前  429 rate limit (冷却 1 分钟)             |   |
| | ✕ 1 小时前  insufficient_quota                       |   |
| | ✕ 30 分钟前 insufficient_quota                       |   |
| └──────────────────────────────────────────────────────┘   |
|                                                             |
| [设置额度]  [标记为正常]  [查看历史]                       |
+-------------------------------------------------------------+
```

**展开面板规则：**
- 展开动画：高度 0 → auto，250ms，ease
- 面板内背景 `bg-stone-50`，左右 padding 与列表对齐，上下 padding 20px
- 内部分段，每段用白色卡片包裹：1px `stone-200` 边框 + 8px 圆角 + 16px padding
- 段标题：12px 字重 600，`text-stone-500`
- 统计项用两列网格：标签左对齐，数值右对齐
- 风险记录用列表展示，每条前有对应状态图标
- 底部操作按钮：左对齐，次按钮样式

---

## 5. 组件规范

### 5.1 SummaryCard（顶部摘要卡片）

用于页面顶部展示全局统计。

**形态：**
- 宽度均分（桌面端 4 列，移动端 2 列）
- 高度 100px
- 白色背景 + 1px `stone-200` 边框 + 12px 圆角 + 20px padding
- 内部垂直布局：数字（32px 字重 700）+ 标签（12px 字重 500）+ 状态圆点（8px）

**颜色映射：**

| 类型 | 数字颜色 | 标签颜色 | 圆点颜色 | 边框 hover |
|------|----------|----------|----------|------------|
| `normal` | `#166534` (鼠尾草-800) | `#57534e` (暖灰-600) | `#22c55e` (绿-500) | 无 |
| `warning` | `#92400e` (琥珀-800) | `#57534e` | `#f59e0b` (琥珀-500) | 无 |
| `limited` | `#991b1b` (砖红-800) | `#57534e` | `#ef4444` (红-500) | 无 |
| `unknown` | `#78716c` (暖灰-500) | `#57534e` | `#a8a29e` (暖灰-400) | 无 |

**规则：**
- 数字使用 `Geist Mono` 字体
- 点击卡片可筛选列表（只显示对应状态的模型）
- 再次点击取消筛选
- 选中状态：卡片边框 2px，对应状态色

---

### 5.2 QuotaStatusTag（额度状态标签）

用于列表和详情中展示 QuotaStatus。

**形态：**
- 高度 22px，水平内边距 8px
- 圆角 999px（pill）
- 字体 11px，字重 600，uppercase，letter-spacing 0.03em

**颜色映射：**

| 状态 | 背景色 | 文字色 | 说明 |
|------|--------|--------|------|
| `normal` | `#dcfce7` (鼠尾草-100) | `#166534` (鼠尾草-800) | 正常 |
| `warning` | `#fef3c7` (琥珀-100) | `#92400e` (琥珀-800) | 警告 |
| `near_limit` | `#ffedd5` (橙-100) | `#9a3412` (橙-800) | 接近上限 |
| `limited` | `#fee2e2` (砖红-100) | `#991b1b` (砖红-800) | 已受限 |
| `cooldown` | `#e0f2fe` (天蓝-100) | `#0369a1` (天蓝-700) | 冷却中 |
| `unknown` | `#f5f5f4` (暖灰-100) | `#78716c` (暖灰-500) | 未知 |

---

### 5.3 UsageProgressBar（使用率进度条）

核心组件，用于一眼传达风险程度。

**形态：**
- 总长度 160px（桌面端），高度 8px
- 背景轨道：`bg-stone-200`，圆角 999px
- 填充条：圆角 999px，宽度按 usage_percent 比例
- 填充条右侧显示百分比数字（12px `Geist Mono`，与填充条同色）

**颜色规则：**

| usage_percent | 填充条颜色 |
|---------------|-----------|
| < 70% | `#22c55e` (绿-500) |
| 70% - 89% | `#f59e0b` (琥珀-500) |
| 90% - 99% | `#f97316` (橙-500) |
| ≥ 100% | `#ef4444` (红-500) |
| unknown / null | `#d6d3d1` (暖灰-300)，显示 "--" |

**动画：**
- 首次加载时，填充条从宽度 0 动画到目标宽度，duration 800ms，ease-out
- 数据刷新时，填充条宽度平滑过渡 400ms
- 颜色变化时，背景色过渡 300ms

**规则：**
- unknown 模式下不显示进度条，显示灰色虚线框 + "--"
- 超过 100% 时填充条占满轨道，颜色为红色
- 百分比数字保留 0 位小数（如 "78%"），unknown 显示 "--"

---

### 5.4 RiskBadge（风险徽章）

用于 Workspace 中 WorkerBadge、TaskCard 等位置展示模型额度状态。

**形态：**
- 尺寸 16px 圆点（小）或 20px 圆点（中）
- 圆角 999px
- 内部显示对应图标（8px 或 10px）

**颜色与图标映射：**

| 状态 | 背景色 | 图标 | 图标色 |
|------|--------|------|--------|
| `normal` | `#22c55e` (绿-500) | Check | 白色 |
| `warning` | `#f59e0b` (琥珀-500) | Warning | 白色 |
| `near_limit` | `#f97316` (橙-500) | AlertCircle | 白色 |
| `limited` | `#ef4444` (红-500) | X | 白色 |
| `cooldown` | `#3b82f6` (蓝-500) | Clock | 白色 |
| `unknown` | `#a8a29e` (暖灰-400) | HelpCircle | 白色 |

**Tooltip：**
- Hover 时显示 Tooltip，内容：
  - 模型名
  - quota_status 文本
  - usage_percent（如有）
  - estimated_remaining（如有）
  - limit_error_count（如 > 0）
- Tooltip 背景 `stone-800`，文字白色，圆角 8px，padding 12px

---

### 5.5 QuotaAlertBanner（额度预警条）

用于 Workspace TopStatusBar 展示全局额度预警。

**WARNING 状态：**
- 背景 `#fef3c7` (琥珀-50)
- 左侧 3px 竖条 `#f59e0b` (琥珀-500)
- 左侧 Warning 图标（16px，琥珀色）
- 文案："Claude 3.5 Sonnet 使用率 78% (WARNING)，建议关注或准备 Handoff"
- 右侧按钮：[查看额度] 文本按钮 + [立即 Handoff] 主按钮（小型）
- 右侧关闭按钮（X 图标）
- 高度 48px，水平 padding 16px

**LIMITED 状态：**
- 背景 `#fee2e2` (砖红-50)
- 左侧 3px 竖条 `#ef4444` (红-500)
- 左侧 AlertTriangle 图标（16px，红色）
- 文案："Claude 3.5 Sonnet 已受限，任务已自动 Handoff 至 GPT-4o"
- 右侧 [查看额度] 文本按钮
- **无关闭按钮**（LIMITED 不可关闭）
- 高度 48px

**多条预警：**
- 多个模型同时 WARNING 时，预警条垂直堆叠，间距 4px
- 超过 3 条时，显示前 2 条 + "还有 2 个模型额度预警" 折叠提示
- 点击折叠提示展开全部

**动画：**
- 出现：从顶部滑入 8px + opacity 0→1，300ms，ease-out
- 消失：opacity 1→0 + 高度收缩，250ms

---

### 5.6 ModelUsageRow（列表行）

用于概览页列表展示单条模型记录。

**规则：**
- 整行高度 56px，垂直居中
- 左侧 12px 状态圆点（实心，颜色对应 QuotaStatus）
- 模型名：14px 字重 500，`text-stone-800`
- Provider：12px `text-stone-400`，位于模型名下方或右侧
- 使用率进度条：160px 宽，位于行中央
- 状态标签：QuotaStatusTag
- 总 tokens：12px `Geist Mono`，右对齐，`text-stone-500`
- 最近调用：12px `text-stone-400`，右对齐，相对时间
- 整行 hover：`bg-stone-50`
- 点击整行展开/折叠详情面板
- 展开状态：行底部边框变为 2px 状态色，左侧出现竖向高亮条

---

### 5.7 QuotaConfigForm（额度设置表单）

用于 ModelUsageCard 中设置模型额度上限。

**触发条件：** quota_mode 为 unknown/estimated 时显示 [设置额度] 按钮

**表单字段：**
- token_limit：数字输入框，单位 "tokens"
- request_limit：数字输入框，单位 "次"
- cost_limit：数字输入框，单位 "USD"
- reset_period：下拉选择（daily / weekly / monthly / never）
- reset_date：数字输入（1-31），仅 monthly 时显示

**规则：**
- 模态框形式，宽度 480px
- 标题："设置额度上限"
- token_limit 必填，其他可选
- 保存后：usage_percent 进度条立即更新，quota_status 标签变色
- 乐观更新：前端先计算并展示新状态，再等待 API 确认

---

## 6. 空状态

### 6.1 列表空状态（无模型记录）

```
+---------------------------------------------------+
|                                                   |
|              [Icon: BarChart]                      |
|                                                   |
|         暂无额度记录                              |
|                                                   |
|   开始调用模型后，系统会自动记录使用量和额度状态。  |
|                                                   |
+---------------------------------------------------+
```

**规则：**
- 图标：48px，`text-stone-300`
- 标题：16px 字重 500，`text-stone-600`
- 描述：14px `text-stone-400`

### 6.2 Unknown 模型状态

- 进度条位置显示虚线框 + "--"
- 显示弱提示："未设置额度上限，系统无法计算使用率"
- [设置额度] 按钮突出显示

---

## 7. 交互动效

| 场景 | 动效 | 时长 | 缓动 |
|------|------|------|------|
| 进度条首次加载 | 宽度 0 → 目标值 | 800ms | ease-out |
| 进度条数据刷新 | 宽度平滑过渡 | 400ms | ease |
| 状态标签切换 | 背景色 + 文字色渐变 | 300ms | ease |
| 行展开 | 高度 0 → auto + opacity | 250ms | ease |
| 行折叠 | 反向 | 200ms | ease |
| 预警条出现 | 从顶部滑入 8px + opacity | 300ms | ease-out |
| 预警条消失 | opacity + 高度收缩 | 250ms | ease |
| SummaryCard hover | 边框颜色变化 | 150ms | ease |
| RiskBadge hover | Tooltip 出现 | 200ms | ease |
| 列表数据刷新 | 骨架屏脉冲 | 1.5s | ease-in-out, infinite |

---

## 8. 响应式策略

| 断点 | 布局变化 |
|------|----------|
| `≥1280px` | 4 个 SummaryCard 水平排列，列表 6 列 |
| `768px–1279px` | SummaryCard 2×2 网格，列表隐藏 Provider 列 |
| `<768px` | SummaryCard 水平滚动，列表退化为卡片 |

---

## 9. 颜色令牌（与 Agent Workspace 共享）

| 令牌 | 值 | 用途 |
|------|-----|------|
| `surface` | `#fafaf9` | 页面背景 |
| `panel` | `#ffffff` | 卡片、展开面板 |
| `border-default` | `#e7e5e4` | 卡片边框、列表分隔线 |
| `text-primary` | `#1c1917` | 标题、主文本 |
| `text-secondary` | `#57534e` | 次要文本 |
| `text-tertiary` | `#a8a29e` | 时间戳、占位符 |
| `quota-normal` | `#22c55e` | normal 状态 |
| `quota-warning` | `#f59e0b` | warning 状态 |
| `quota-near-limit` | `#f97316` | near_limit 状态 |
| `quota-limited` | `#ef4444` | limited 状态 |
| `quota-cooldown` | `#3b82f6` | cooldown 状态 |
| `quota-unknown` | `#a8a29e` | unknown 状态 |
| `progress-track` | `#e7e5e4` | 进度条轨道 |
| `overlay` | `rgba(0,0,0,0.3)` | 模态框遮罩 |

---

## 10. 字体规范

复用 Agent Workspace 字体系统：
- 字体族：`Geist`（正文）+ `Geist Mono`（数字、百分比、tokens）
- 页面标题：20px / 600 / `text-stone-900`
- SummaryCard 数字：32px / 700 / `Geist Mono`
- SummaryCard 标签：12px / 500 / `text-stone-600`
- 列表模型名：14px / 500 / `text-stone-800`
- 列表 Provider：12px / 400 / `text-stone-400`
- 百分比数字：12px / 500 / `Geist Mono`
- 状态标签：11px / 600 / uppercase
- 段标题：12px / 600 / `text-stone-500`
- 统计数值：14px / 500 / `Geist Mono` / `text-stone-700`

---

## 11. P0 vs P1 设计范围

| 功能 | 优先级 | MVP 阶段 | 说明 |
|------|--------|----------|------|
| Quota Overview 页面 | P0 | MVP-A | 列表、SummaryCards、筛选排序 |
| 使用率进度条 | P0 | MVP-A | 6 色梯度进度条 |
| QuotaStatusTag | P0 | MVP-A | 6 种状态标签 |
| RiskBadge | P0 | MVP-A | Workspace 各位置徽章 |
| QuotaAlertBanner | P0 | MVP-A | TopStatusBar 预警条 |
| 额度设置表单 | P0 | MVP-A | token_limit 等字段 |
| 模型详情展开面板 | P0 | MVP-A | 使用统计、风险记录 |
| Usage Trend 图表 | P1 | MVP-B | 24h/7d/30d 趋势 |
| QuotaStatusHistory | P1 | MVP-B | 状态变化时间线 |
| Handoff Trigger History | P1 | MVP-B | 额度触发的 Handoff 记录 |

---

> 文档版本：v1.0
>
> 最后更新：2026-06-25
>
> 相关文档：
> - `docs/design/agent-workspace-frontend-design.md` — 共享设计系统与颜色令牌
> - `docs/prd/quota-manager-prd.md` — 产品需求
> - `docs/stories/quota-manager-stories.md` — 用户故事
> - `docs/tasks/quota-manager-tasks.md` — 开发任务（QM-T4.x / QM-T6.x 对应本文前端组件）
