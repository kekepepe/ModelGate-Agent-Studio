# 2026-07-18 Workspace 统一导航与信息架构重构开发计划

> 项目：ModelGate Agent Studio  
> 计划类型：前端信息架构与运行工作区重构  
> 核心目标：将当前封闭式 Workspace 运行页纳入 ModelGate 统一产品框架，使 Studio、Workspace、Assets、Evolution、Logs 形成连续、可返回、可恢复、可追踪的完整产品体验。

> **实施状态（2026-07-18）**：P0–P7 已完成仓库级开发与验收。Backend `398 passed, 1 skipped`；Frontend `175 passed`；Playwright 多视口 `9 passed, 15 intentionally skipped`；Docker Compose build 通过。完整证据见 `docs/roadmap/review/2026-07-18-Workspace统一导航与信息架构重构开发Review.md`。

---

## 1. 背景与问题说明

当前 ModelGate 主界面已经具备统一的产品导航：

- Studio
- Workspace
- Assets
- Evolution
- Logs
- 运行概览

但进入 Workspace 具体运行页面后，页面切换为一套独立 Header，并完全丢失主导航。用户进入后无法自然返回 Studio，也无法直接访问 Assets、Evolution、Logs 或其他 Workspace Run。

现状造成以下问题：

1. Workspace 看起来像另一个独立产品，而不是 ModelGate 的核心模块。
2. 用户无法判断当前页面位于产品的哪一层。
3. 缺少返回按钮、面包屑和运行列表，形成封闭页面。
4. Workspace、Logs、Evolution、Assets 之间的数据关系没有通过导航和 URL 表达。
5. 当前运行状态信息占用了全局 Header，导致全局导航和运行控制职责混杂。
6. 用户离开 Workspace 后是否会停止任务、能否恢复任务，缺少明确规则。
7. 主界面与 Workspace 使用不同 Logo、导航风格和页面结构，削弱产品一致性。
8. 浏览器刷新、返回、直接打开 Run URL 时的状态恢复逻辑不明确。

本次重构不是只增加一个“返回按钮”，而是重新建立 ModelGate 的全局 App Shell、Workspace 信息架构、路由结构、运行状态恢复和跨模块关联。

---

## 2. 重构目标

### 2.1 产品目标

1. Workspace 成为 ModelGate 主产品体系中的一级模块。
2. 用户在任意 Workspace 页面都可以明确知道当前位置。
3. 用户能够在一次点击内返回 Studio 或 Workspace Overview。
4. 用户离开具体运行页后，后台任务继续执行。
5. 用户再次进入时可以恢复原有 Run 状态。
6. Workspace、Logs、Evolution、Assets 通过 runId、goalId、artifactId 形成数据关联。
7. Card Flow 和 Pixel Office 明确成为同一个 Workspace Run 的两种视图。
8. 全局导航、运行导航和具体工作区三层职责清晰。

### 2.2 技术目标

1. 建立统一 App Shell。
2. 重构 Workspace 路由结构。
3. 抽离 Workspace Run Header。
4. 新增 Workspace Overview 页面。
5. 建立 Run 级状态恢复机制。
6. 建立跨页面筛选参数和跳转规则。
7. 保持现有 Goal、Task Tree、Card Flow、Pixel Office、Console Summary 功能不被破坏。
8. 补齐前端单元测试、组件测试和 Playwright 端到端测试。

### 2.3 体验目标

1. 用户 3 秒内识别当前所在模块和当前运行。
2. 用户无需修改 URL 即可离开 Workspace。
3. 用户离开页面不会误停止任务。
4. 用户刷新页面后不会丢失运行上下文。
5. 用户可以快速在运行、日志、产物和进化记录之间切换。

---

## 3. 非目标范围

本轮不处理以下内容：

1. 不重写 Agent Runtime 核心执行逻辑。
2. 不重构 Planner、Router、Handoff、Supervisor 的业务算法。
3. 不重做 Pixel Office 美术资源。
4. 不新增复杂多人协作权限。
5. 不实现完整通知中心。
6. 不实现完整桌面端或移动端适配。
7. 不实现新的模型 Provider。
8. 不改变 Goal 创建和任务拆解的核心业务定义。
9. 不把 Workspace 改造成自由节点式 Workflow Builder。

---

## 4. 核心设计原则

### 4.1 全局导航始终存在

除登录页、错误页等特殊页面外，Studio、Workspace、Assets、Evolution、Logs 页面统一复用 App Shell。

### 4.2 离开页面不等于停止运行

用户从 Workspace 跳转至 Logs、Evolution、Studio 或其他页面时，Run 保持后台执行。

### 4.3 运行控制与产品导航分离

- 全局 Header：负责产品模块导航。
- Run Header：负责当前运行信息与控制。
- Workspace Main：负责 Goal、Task、Agent 和视图展示。

### 4.4 URL 表达真实产品层级

具体运行必须拥有稳定 URL，刷新和直接访问时可恢复状态。

### 4.5 跨模块跳转保留上下文

从 Workspace 进入 Logs、Evolution、Assets 时，自动携带当前 runId、goalId 或 artifactId。

### 4.6 视觉统一，局部风格可差异化

全局导航统一；Pixel Office 仍可保持像素风，但不能影响整个应用的统一外壳。

---

## 5. 新信息架构

```text
ModelGate
├── Studio
│   ├── Team Templates
│   ├── Custom Teams
│   └── Create Run
│
├── Workspace
│   ├── Overview
│   │   ├── Active Runs
│   │   ├── Recent Runs
│   │   ├── Completed Runs
│   │   ├── Failed Runs
│   │   └── Stopped Runs
│   └── Run Detail
│       ├── Goal
│       ├── Task Tree
│       ├── Card Flow
│       ├── Pixel Office
│       ├── Console Summary
│       └── Run Controls
│
├── Assets
│   ├── Run Outputs
│   ├── Generated Files
│   └── Export History
│
├── Evolution
│   ├── Memory Drafts
│   ├── Skill Drafts
│   ├── Review Queue
│   └── Knowledge Records
│
├── Logs
│   ├── All Logs
│   ├── Run Logs
│   ├── Agent Logs
│   ├── Tool Calls
│   └── Errors
│
└── Run Overview
    ├── Active Agents
    ├── Quota
    ├── Parallelism
    └── Coordination Tokens
```

---

## 6. 路由设计

### 6.1 推荐路由

```text
/studio
/studio/teams/[teamId]

/workspace
/workspace/runs/[runId]

/assets
/assets?runId=[runId]
/assets/[assetId]

/evolution
/evolution?goalId=[goalId]
/evolution?runId=[runId]

/logs
/logs?runId=[runId]
/logs?goalId=[goalId]
/logs?agentId=[agentId]
```

### 6.2 路由行为

#### `/workspace`

展示 Workspace Overview，不自动进入某个 Run。

#### `/workspace/runs/[runId]`

展示具体运行页面，并根据 runId 请求完整状态。

#### 无效 runId

显示明确错误页面：

- Run 不存在
- Run 已删除
- 当前用户无权限
- 后端暂时不可用

同时提供：

- 返回 Workspace
- 返回 Studio
- 重试

### 6.3 旧路由迁移

如果当前已有旧 Workspace 路由：

```text
/workspace/[id]
/run/[id]
/agent-workspace/[id]
```

则统一重定向到：

```text
/workspace/runs/[runId]
```

---

## 7. 页面层级设计

### 7.1 第一层：Global App Shell

所有主业务页面共享：

```text
ModelGate | Studio | Workspace | Assets | Evolution | Logs | 运行概览
```

包含：

1. 统一 Logo。
2. 一级导航。
3. 当前选中状态。
4. 右侧全局运行概览。
5. 可选账户或设置入口。

### 7.2 第二层：Workspace Run Header

仅具体 Run 页面显示。

推荐结构：

```text
← 返回 Workspace
Studio / 代码交付团队 / Run #MG-1024
Goal: 完成一个可验证的代码交付
Ready | 0 Agents Active | Quota 0%
Pause | Resume | Stop | Export
```

职责：

- 显示当前团队。
- 显示 Run ID。
- 显示 Goal 摘要。
- 显示运行状态。
- 显示 Agent 数量。
- 显示并行状态。
- 显示 Token 与 Quota。
- 提供 Pause、Resume、Stop、Export。

### 7.3 第三层：Workspace View Toolbar

```text
Card Flow | Pixel Office
```

可扩展：

```text
Card Flow | Pixel Office | Timeline
```

当前阶段只保留前两种。

### 7.4 第四层：Workspace Main Content

```text
左侧：Goal + Run Config + Task Tree
中间：Card Flow / Pixel Office
底部：Console Summary / Live Logs
可选右侧：Task Detail / Agent Detail
```

---

## 8. 页面详细设计

## 8.1 Studio 页面

保持现有团队模板卡片，但修改“立即运行”流程。

### 新流程

```text
点击“立即运行”
→ 打开 Goal 创建弹窗或进入 Goal 配置
→ 创建 Run
→ 后端返回 runId
→ 跳转 /workspace/runs/[runId]
```

### 必须补充

1. 创建 Run 的 loading 状态。
2. 创建失败错误提示。
3. 防止重复点击创建多个 Run。
4. 创建成功后保存最近使用团队。
5. 配置按钮与立即运行按钮职责区分。

---

## 8.2 Workspace Overview 页面

### 页面目标

作为所有运行的入口，避免用户只能依赖 Studio 或浏览器历史进入具体 Run。

### 页面区块

#### A. Active Runs

展示：

- Run 名称
- Team 名称
- Goal 摘要
- 状态
- 当前阶段
- 活跃 Agent 数量
- 完成进度
- Quota
- 更新时间
- 进入 Workspace
- Pause / Stop 快捷操作

#### B. Recent Runs

展示最近访问或最近更新的 Run。

#### C. Completed Runs

展示：

- 完成时间
- 最终产物
- Export
- 查看 Logs
- 查看 Evolution

#### D. Failed / Stopped Runs

展示：

- 失败原因
- 最后阶段
- 恢复运行
- 克隆 Run
- 查看错误日志

### 筛选项

- 状态
- 团队
- 时间范围
- Goal 关键词
- 是否有错误
- 是否发生 Handoff

### 空状态

```text
当前没有运行中的 Workspace。
从 Studio 选择一支 Agent 团队并创建 Goal。
```

按钮：

```text
前往 Studio
```

---

## 8.3 Workspace Run Detail 页面

### 左侧栏

#### Goal 区

- Team 名称
- Capability Pool
- Goal 输入
- 补充说明
- 完成标准
- Run Config
- 创建并规划 / 重新规划

#### Task Tree 区

- 任务层级
- 状态
- 依赖关系
- 当前 Agent
- 错误提示
- 点击查看详情

### 中间主区域

#### Card Flow

- 每个卡片代表 Agent / Task。
- 展示状态、模型、耗时、输出摘要。
- 已完成 Agent 缩略收起。
- 新 Agent 激活后动态出现。
- Handoff 使用连线与状态表达。

#### Pixel Office

- 工位代表 Agent Station。
- 像素小人代表 Worker。
- 小人进入、工作、等待、交接、离开。
- Handoff Folder 表示上下文交接。
- 所有视觉状态必须由真实运行状态驱动。

### 底部 Console Summary

展示：

- Tasks Completed
- In Progress
- Waiting
- Handoffs
- Errors
- Last Update

支持展开为 Live Logs。

---

## 8.4 Logs 页面关联

从 Workspace 点击 Logs 时跳转：

```text
/logs?runId=[currentRunId]
```

Logs 页面默认筛选当前 Run，并展示：

- 模型调用
- Agent 状态变化
- Tool Calls
- Handoff
- Error
- Token Usage
- Quota Events

提供“返回当前 Workspace”入口。

---

## 8.5 Evolution 页面关联

从 Workspace 点击 Evolution 时跳转：

```text
/evolution?goalId=[goalId]&runId=[runId]
```

默认展示：

- 当前 Run 产生的 Memory Draft
- Skill Draft
- Project Memory Draft
- User Preference Draft
- Handoff Knowledge

提供“返回当前 Workspace”入口。

---

## 8.6 Assets 页面关联

从 Workspace 点击 Export 或 Assets 时跳转：

```text
/assets?runId=[runId]
```

展示：

- 最终输出
- 生成文件
- 报告
- 代码包
- Export 历史
- 下载状态

---

## 9. 组件架构

### 9.1 新增组件

```text
components/app-shell/
├── AppShell.tsx
├── GlobalHeader.tsx
├── GlobalNav.tsx
├── GlobalRunOverview.tsx
└── AppBreadcrumb.tsx

components/workspace/
├── WorkspaceOverview.tsx
├── RunList.tsx
├── RunListItem.tsx
├── WorkspaceRunHeader.tsx
├── WorkspaceViewTabs.tsx
├── RunStatusBadge.tsx
├── RunControlButtons.tsx
├── GoalPanel.tsx
├── TaskTreePanel.tsx
├── ConsoleSummary.tsx
├── LiveLogsDrawer.tsx
└── RunNotFoundState.tsx
```

### 9.2 重构组件

可能需要重构：

- 现有 Workspace Header
- 当前团队选择器
- Quota 展示
- Agent Active 展示
- Pause / Resume / Stop / Export
- Card Flow / Pixel Office Tabs
- Console Summary

### 9.3 组件职责边界

#### AppShell

只负责全局框架，不读取具体 Run 业务数据。

#### WorkspaceRunHeader

只负责当前 Run 元信息和控制。

#### WorkspaceOverview

只负责 Run 列表和筛选。

#### CardFlow / PixelOffice

只消费统一的 Run View Model，不直接自行请求不同格式的数据。

---

## 10. 前端状态管理设计

### 10.1 状态分层

#### 全局状态

- 当前用户
- 全局导航状态
- 活跃 Run 数量
- 全局 Quota 概览
- Provider 健康状态

#### Run 状态

- runId
- goalId
- teamId
- runStatus
- tasks
- workers
- agentStations
- handoffs
- tokenUsage
- quotaStatus
- artifacts
- logs
- lastUpdatedAt

#### 页面临时状态

- 当前 Workspace View
- 左侧栏展开状态
- Console 展开状态
- 当前选中 Task
- 当前选中 Agent
- 筛选条件

### 10.2 推荐数据获取方式

使用统一 Query Key：

```text
['workspace-run', runId]
['workspace-runs', filters]
['workspace-run-logs', runId]
['workspace-run-assets', runId]
['workspace-run-evolution', runId]
```

### 10.3 页面刷新恢复

进入 `/workspace/runs/[runId]` 时：

1. 读取 URL 中的 runId。
2. 请求 Run 基础信息。
3. 请求任务树。
4. 请求 Worker / Agent 状态。
5. 请求 Quota 和 Token。
6. 建立 SSE / WebSocket 或轮询。
7. 恢复用户上次选择的 Card Flow / Pixel Office。

### 10.4 视图选择持久化

推荐保存：

```text
workspace:view:[runId] = card | pixel
```

优先级：

1. URL 查询参数。
2. 本地持久化。
3. 默认 Card Flow。

---

## 11. 后端接口需求

如果现有接口不足，需要补充以下能力。

### 11.1 Run 列表

```http
GET /api/runs
```

支持参数：

- status
- team_id
- search
- page
- page_size
- sort

### 11.2 Run 详情

```http
GET /api/runs/{run_id}
```

返回：

- Run 元信息
- Goal
- Team
- Status
- Progress
- Agents Active
- Parallelism
- Token Usage
- Quota
- Created At
- Updated At

### 11.3 Run 运行视图

```http
GET /api/runs/{run_id}/workspace
```

返回：

- Task Tree
- Agent Stations
- Workers
- Handoffs
- Console Summary

### 11.4 Run 控制

```http
POST /api/runs/{run_id}/pause
POST /api/runs/{run_id}/resume
POST /api/runs/{run_id}/stop
POST /api/runs/{run_id}/export
```

### 11.5 Run 日志

```http
GET /api/runs/{run_id}/logs
```

### 11.6 Run 产物

```http
GET /api/runs/{run_id}/assets
```

### 11.7 Run 进化记录

```http
GET /api/runs/{run_id}/evolution
```

### 11.8 实时状态

推荐优先级：

1. SSE
2. WebSocket
3. 轮询兜底

事件示例：

```text
run.status.changed
run.progress.changed
agent.activated
agent.status.changed
task.status.changed
handoff.started
handoff.completed
quota.updated
artifact.created
log.created
run.completed
run.failed
```

---

## 12. 运行状态定义

统一状态枚举：

```text
draft
planning
ready
running
paused
waiting
handoff
reviewing
completed
failed
stopped
```

### 页面显示规则

| 状态 | 显示文案 | 可执行操作 |
|---|---|---|
| draft | 草稿 | 创建并规划 |
| planning | 规划中 | 暂停、停止 |
| ready | 已就绪 | 启动、停止 |
| running | 运行中 | 暂停、停止 |
| paused | 已暂停 | 恢复、停止 |
| waiting | 等待中 | 停止 |
| handoff | 交接中 | 停止 |
| reviewing | 审查中 | 暂停、停止 |
| completed | 已完成 | 导出、查看产物 |
| failed | 失败 | 重试、查看日志 |
| stopped | 已停止 | 克隆、查看日志 |

---

## 13. 导航与交互规则

### 13.1 点击 Logo

跳转：

```text
/studio
```

### 13.2 点击 Studio

跳转：

```text
/studio
```

不停止当前 Run。

### 13.3 点击 Workspace

跳转：

```text
/workspace
```

进入 Run Overview。

### 13.4 点击 Logs

当前位于 Run 页面时：

```text
/logs?runId=[runId]
```

否则：

```text
/logs
```

### 13.5 点击 Evolution

当前位于 Run 页面时：

```text
/evolution?runId=[runId]&goalId=[goalId]
```

### 13.6 点击 Assets

当前位于 Run 页面时：

```text
/assets?runId=[runId]
```

### 13.7 浏览器返回

必须正常返回上一级，不使用强制 replace 破坏历史记录。

### 13.8 离开运行页

- 不提示“是否停止任务”。
- 不调用 stop API。
- 保持后台运行。
- 仅在存在未保存本地配置时提示离开确认。

---

## 14. Pause、Resume、Stop、Export 规则

### 14.1 Pause

- 仅 running / planning / reviewing 可用。
- 点击后按钮进入 loading。
- 后端确认成功后状态变为 paused。
- 不允许重复点击。

### 14.2 Resume

- 仅 paused 可用。
- 恢复后继续从持久化状态执行。

### 14.3 Stop

- 属于破坏性操作。
- 必须二次确认。
- 提示停止后是否可以恢复。
- 成功后状态变为 stopped。

### 14.4 Export

- completed 时默认可用。
- running 时可导出当前快照，但必须标注“运行中快照”。
- 导出后产物进入 Assets。

---

## 15. 视觉统一要求

### 15.1 Header

统一：

- Logo
- 高度
- 背景色
- 分隔线
- 字体
- 导航间距
- Hover
- Active 状态

### 15.2 Logo

图 1 与图 2 当前存在不同 Logo，不应继续保留两套主品牌标识。

建议：

- App Shell 使用唯一 ModelGate Logo。
- Pixel Office 内可使用像素图标作为局部装饰，但不替代主品牌 Logo。

### 15.3 颜色

- 保持低饱和、浅色、类 Claude 的整体方向。
- Workspace 状态色仅用于表达状态。
- 不因 Pixel Office 切换成完全不同的产品视觉语言。

### 15.4 响应式

本轮最低要求：

- 1440px 桌面宽度完整显示。
- 1280px 不出现横向溢出。
- 1024px 可压缩左侧栏。
- 暂不要求移动端完整可用。

---

## 16. 实施阶段

## 阶段 P0：现状梳理与保护

### 任务

1. 梳理现有 Workspace 路由。
2. 梳理当前 Header 组件。
3. 梳理 Studio、Assets、Evolution、Logs 的布局组件。
4. 梳理 Run 状态数据来源。
5. 梳理 Pause、Resume、Stop、Export 接口。
6. 梳理刷新后状态恢复能力。
7. 增加现状 Playwright 基线测试。

### 产物

- 当前路由图
- 当前组件依赖图
- 当前 API 清单
- 重构影响文件清单
- 基线测试结果

### 验收

- 清楚定位所有 Workspace 入口。
- 清楚识别 Header 重复实现。
- 现有主要流程有测试保护。

---

## 阶段 P1：统一 App Shell

### 任务

1. 新建 AppShell。
2. 抽离 GlobalHeader。
3. 抽离 GlobalNav。
4. 统一 Logo。
5. 将 Studio 接入 AppShell。
6. 将 Workspace 接入 AppShell。
7. 将 Assets、Evolution、Logs 接入 AppShell。
8. 实现导航 Active 状态。
9. 实现全局运行概览占位或真实数据。

### 验收

- 所有一级页面使用同一 Header。
- Workspace 中能够看到 Studio、Workspace、Assets、Evolution、Logs。
- Logo 点击返回 Studio。
- 页面切换时 Header 不闪烁、不重复挂载。

---

## 阶段 P2：Workspace 路由重构

### 任务

1. 新增 `/workspace`。
2. 新增 `/workspace/runs/[runId]`。
3. 旧路由重定向。
4. 增加 Run Not Found。
5. 增加 Run Loading Skeleton。
6. 增加 Run Error State。
7. 支持浏览器刷新恢复。

### 验收

- 具体 Run 有稳定 URL。
- 直接访问 URL 可恢复页面。
- 无效 runId 有明确错误页。
- 浏览器返回行为正常。

---

## 阶段 P3：Workspace Overview

### 任务

1. 实现 Active Runs。
2. 实现 Recent Runs。
3. 实现 Completed Runs。
4. 实现 Failed / Stopped Runs。
5. 实现状态筛选。
6. 实现搜索。
7. 实现空状态。
8. 实现进入具体 Run。
9. 实现快速查看 Logs / Assets / Evolution。

### 验收

- 用户可从 Workspace 一级入口找到所有运行。
- 用户不依赖浏览器历史进入 Run。
- 列表状态与后端一致。

---

## 阶段 P4：Workspace Run Header

### 任务

1. 移除当前独立全屏 Header。
2. 新增 WorkspaceRunHeader。
3. 增加返回 Workspace。
4. 增加面包屑。
5. 展示 Team、Run ID、Goal。
6. 展示状态、Agents、Token、Quota。
7. 迁移 Pause、Resume、Stop、Export。
8. 完成不同状态的按钮禁用逻辑。
9. Stop 增加确认对话框。

### 验收

- 全局导航和运行控制职责分离。
- 所有 Run 控制正确工作。
- 返回 Workspace 不停止任务。

---

## 阶段 P5：跨模块关联

### 任务

1. Workspace → Logs 携带 runId。
2. Workspace → Evolution 携带 runId、goalId。
3. Workspace → Assets 携带 runId。
4. Logs 增加返回 Workspace。
5. Evolution 增加返回 Workspace。
6. Assets 增加返回 Workspace。
7. 各页面显示当前筛选上下文。

### 验收

- 用户可在 Run、Logs、Evolution、Assets 间连续跳转。
- 不丢失当前 Run 上下文。
- URL 能表达筛选条件。

---

## 阶段 P6：状态恢复与实时更新

### 任务

1. 统一 Run View Model。
2. 建立 Run Query Cache。
3. 实现 SSE / WebSocket 或轮询。
4. 实现断线重连。
5. 实现页面隐藏后恢复。
6. 实现刷新恢复。
7. 持久化 Card Flow / Pixel Office 选择。
8. 处理 Run 完成、失败、停止事件。

### 验收

- 离开并返回后状态正确。
- 刷新后状态正确。
- 不重复创建 Worker 或 Task。
- 实时事件不会导致 UI 抖动。

---

## 阶段 P7：测试与回归

### 单元测试

- GlobalNav Active 状态
- WorkspaceRunHeader 状态显示
- RunControlButtons 可用性
- 状态到文案映射
- URL 参数生成
- View 持久化

### 组件测试

- Workspace Overview 列表
- Run Loading / Error / Empty
- Stop 确认框
- Quota 更新
- Task Tree 更新

### Playwright 测试

1. Studio 创建 Run 并进入 Workspace。
2. Workspace 显示统一全局导航。
3. 点击返回 Workspace Overview。
4. 离开 Workspace 后 Run 保持运行。
5. 重新进入恢复状态。
6. 刷新具体 Run 页面恢复状态。
7. Workspace 跳转 Logs 并携带 runId。
8. Workspace 跳转 Evolution 并携带 goalId。
9. Workspace 跳转 Assets 并携带 runId。
10. Pause / Resume 正常。
11. Stop 二次确认正常。
12. 无效 runId 显示错误页。
13. Card Flow / Pixel Office 切换保持。
14. 浏览器返回正常。

### 视觉回归

- Studio Header
- Workspace Overview
- Workspace Run Detail
- Card Flow
- Pixel Office
- Console Summary
- Logs 带筛选状态
- Evolution 带筛选状态

---

## 17. 完整验收标准

### 信息架构

- [x] Workspace 属于 ModelGate 一级导航。
- [x] Workspace Overview 与 Run Detail 层级明确。
- [x] 具体 Run 使用稳定 URL。
- [x] 浏览器刷新、前进、后退正常。

### 全局导航

- [x] Workspace 页面始终显示全局导航。
- [x] Logo、Studio、Workspace、Assets、Evolution、Logs 均可点击。
- [x] 当前导航项高亮正确。
- [x] 所有页面使用统一 Logo 和 Header。

### 返回与切换

- [x] 具体 Run 可一键返回 Workspace Overview。
- [x] 可返回 Studio。
- [x] 离开页面不停止 Run。
- [x] 不存在必须手动修改 URL 才能离开的情况。

### 运行状态

- [x] 刷新后可恢复 Run。
- [x] 离开后重新进入可恢复 Run。
- [x] Pause、Resume、Stop、Export 状态正确。
- [x] Stop 有二次确认。
- [x] Quota、Token、Agent 数量与后端一致。

### 跨模块关联

- [x] Logs 支持 runId 筛选。
- [x] Evolution 支持 runId、goalId 筛选。
- [x] Assets 支持 runId 筛选。
- [x] 各页面可返回当前 Workspace。

### 视觉一致性

- [x] Studio 与 Workspace 使用同一 App Shell。
- [x] Pixel Office 保持局部像素风，但不破坏全局视觉。
- [x] Header 高度、边框、字体、间距统一。
- [x] 1280px 以上无明显横向溢出。

### 测试

- [x] 单元测试通过。
- [x] 组件测试通过。
- [x] Playwright 新增用例通过。
- [x] 原有 Workspace 用例无回归。
- [x] `git diff --check` 通过。
- [x] Docker 环境构建通过。

---

## 18. 风险与处理方案

### 风险 1：Workspace Header 与业务逻辑耦合严重

处理：

- 先抽离数据适配层。
- 再拆分展示组件。
- 不在同一提交中同时重写接口和 UI。

### 风险 2：离开页面后运行实际会中断

处理：

- 检查执行是否依赖前端连接。
- 将执行状态放到后端持久化。
- 前端仅作为观察和控制端。

### 风险 3：实时事件与轮询重复更新

处理：

- 定义唯一事件序列号或 updatedAt。
- 对旧事件去重。
- SSE 断开时才启用轮询兜底。

### 风险 4：旧 URL 和收藏失效

处理：

- 保留重定向。
- 增加兼容期。
- 不立即删除旧路由。

### 风险 5：Workspace Overview 接口尚不存在

处理：

- 第一阶段可用已有 Run 数据组合。
- 第二阶段补充聚合接口。
- 前端保留 Adapter，避免组件绑定临时结构。

### 风险 6：App Shell 重构影响所有页面

处理：

- 分页面迁移。
- 先完成 Studio 和 Workspace。
- 每迁移一个页面执行一次视觉和路由回归。

---

## 19. 推荐提交拆分

### Commit 1

```text
refactor(layout): add shared ModelGate app shell
```

### Commit 2

```text
refactor(workspace): add workspace overview and run routes
```

### Commit 3

```text
refactor(workspace): separate global navigation from run header
```

### Commit 4

```text
feat(workspace): persist and restore run view state
```

### Commit 5

```text
feat(navigation): link workspace runs with logs evolution and assets
```

### Commit 6

```text
test(workspace): add navigation and run recovery coverage
```

避免将全部修改堆积在一个大提交中。

---

## 20. 建议开发顺序

```text
1. 现状测试保护
2. App Shell
3. Workspace 新路由
4. Workspace Overview
5. Workspace Run Header
6. 返回与面包屑
7. 跨模块关联
8. 状态恢复
9. 实时更新
10. Playwright 回归
11. 视觉调整
12. 文档更新
```

---

## 21. 预期交付物

1. 统一 App Shell。
2. Workspace Overview 页面。
3. Workspace Run Detail 新路由。
4. Workspace Run Header。
5. 全局导航与运行控制拆分。
6. 跨 Logs、Evolution、Assets 的上下文跳转。
7. Run 状态恢复机制。
8. 旧路由兼容重定向。
9. 完整单元测试和 Playwright 测试。
10. 更新后的页面结构文档。
11. 更新后的路由文档。
12. 更新后的 API 说明。
13. 开发 Review 报告。

---

## 22. Claude Code 执行提示词

```text
请基于本计划对 ModelGate Agent Studio 的 Workspace 信息架构进行完整重构。

目标不是只增加一个返回按钮，而是将 Workspace 纳入统一 ModelGate App Shell，并建立 Workspace Overview、具体 Run 页面、跨模块导航和运行状态恢复机制。

开发要求：

1. 先检查现有项目结构、路由、Workspace Header、运行状态接口和测试，不要直接修改。
2. 输出受影响文件清单和实施顺序。
3. 保留现有 Goal、Task Tree、Card Flow、Pixel Office、Console Summary 功能。
4. 所有一级页面统一复用 App Shell。
5. 新增 `/workspace` 和 `/workspace/runs/[runId]`。
6. 具体 Run 页面使用 Workspace Run Header，不再使用独立全屏 Header。
7. 离开 Workspace 不得停止后端任务。
8. Workspace、Logs、Evolution、Assets 通过 runId、goalId 关联。
9. 支持刷新恢复、浏览器返回、无效 runId 错误状态。
10. 每完成一个阶段执行相关测试。
11. 不得大范围无关重构。
12. 不得只实现静态 UI，所有状态必须连接真实数据。
13. 完成后提交完整 Review，包括：
   - 修改文件
   - 路由变化
   - API 变化
   - 测试结果
   - 未完成项
   - 风险
   - 截图或录屏说明

请按以下顺序执行：

P0 现状梳理与测试保护
P1 统一 App Shell
P2 Workspace 路由重构
P3 Workspace Overview
P4 Workspace Run Header
P5 跨模块关联
P6 状态恢复与实时更新
P7 测试与回归

每个阶段完成后先验证，再进入下一阶段。
```

---

## 23. 最终产品效果

重构后的用户路径应为：

```text
Studio 选择团队
→ 创建 Goal
→ 创建 Run
→ 进入 Workspace Run Detail
→ 在 Card Flow / Pixel Office 中观察执行
→ 随时进入 Logs 查看过程
→ 进入 Assets 查看产物
→ 进入 Evolution 审核记忆与 Skill
→ 返回 Workspace Overview 查看其他运行
→ 返回 Studio 创建新的团队任务
```

最终 Workspace 不再是一个脱离主产品的封闭页面，而是 ModelGate Agent Studio 中负责运行、观察和控制 Agent 团队的核心工作区。
