# ModelGate Agent Studio MVP 功能优先级裁剪

> 本文档用于约束当前 MVP 阶段的功能范围。当前阶段优先完成 `Goal → Task → Agent → Model Router → Handoff → Workspace → Final Summary` 闭环。
>
> 原则：不做普通 ChatGPT clone，不做完整像素办公室，不做复杂插件市场，不做完全自动化本地操作。

---

## 1. 当前 MVP 的核心目标

MVP 不是把所有愿景能力一次做完，而是证明 ModelGate Agent Studio 已经具备一个多模型 Agent 工作台的核心骨架。

必须优先跑通：

```text
用户输入 Goal
↓
Planner 拆解 Task
↓
Task 分配给 Agent
↓
Model Router 选择模型
↓
Agent Runtime 串行执行
↓
必要时触发 Handoff
↓
接手 Agent 继续任务
↓
Supervisor 生成 Final Summary
↓
Workspace 展示完整过程
```

判断标准：

> 只要某个功能不能直接加强 Goal → Task → Agent → Handoff → Workspace 闭环，就不要进入 MVP-A。

---

## 2. Must Have：没有它就无法展示核心价值

这些功能必须进入 MVP。少了它们，ModelGate 就无法区别于普通聊天工具或简单 API 聚合器。

### 2.1 Goal 输入与管理

必须包含：

- 创建 Goal
- 启动 Goal
- 查看 Goal 状态
- Goal 运行配置：
  - 是否允许多 Agent
  - 是否允许自动模型切换
  - 是否允许 Handoff
- Goal 进度：
  - total_tasks
  - completed_tasks
  - handoff_count
  - tokens_used
- Supervisor 生成 Final Summary

原因：

> Goal 是整个系统的起点。没有 Goal，就无法展示“围绕一个目标组织 AI 团队协作”。

### 2.2 Task 拆解与状态流转

必须包含：

- Planner 将 Goal 拆成 3-5 个 Task
- Task 状态管理：
  - pending
  - assigned
  - running
  - waiting
  - handoff
  - completed
  - failed
- Task 分配给 Agent
- Task 输出保存
- Task 完成标准
- 简单依赖处理

不需要第一版就做复杂任务 DAG，但必须能展示任务从一个 Agent 流转到另一个 Agent。

原因：

> Task 是多 Agent 协作的最小工作单元。没有 Task，产品会退化成普通聊天。

### 2.3 固定 Agent Station

必须包含：

- Planner Agent
- Coder Agent
- Reviewer Agent
- Summarizer Agent
- Supervisor Agent

可以包含但不强制：

- Research Agent

必须支持：

- Agent 职责说明
- 当前状态
- 默认模型
- 备用模型
- 是否允许 Handoff
- 当前任务绑定

原因：

> ModelGate 的核心不是“模型列表”，而是“角色化 Agent 工位”。Agent Station 是产品差异化的核心概念。

### 2.4 Model 配置与基础 Model Router

必须包含：

- Mock Model
- 至少一种 OpenAI-compatible 模型
- Anthropic / DeepSeek 中至少支持一种真实 Provider
- 模型能力标签：
  - planning
  - code
  - review
  - long-context
  - fast
  - low-cost
- 默认模型和备用模型
- 基础路由规则：
  - 按 Agent 角色选模型
  - 按任务类型选模型
  - 按额度状态切备用模型
- 路由解释：
  - 为什么当前 Task 选择这个模型

原因：

> 如果没有 Model Router，ModelGate 就只是手动切模型工具，而不是多模型 Agent 调度平台。

### 2.5 Agent Runtime：串行执行即可

必须包含：

- 加载 Task
- 加载 Agent 配置
- 选择模型
- 调用 Mock 或真实模型
- 保存 WorkerSession
- 保存 Task 输出
- 更新状态
- 写入执行日志

第一版只需要串行执行，不需要并行 Agent。

原因：

> Runtime 是让 Goal → Task → Agent 真正跑起来的执行层。没有 Runtime，Workspace 只是静态 UI。

### 2.6 Handoff 机制

必须包含：

- 手动触发 Handoff
- 额度 warning 或模型错误时提示 Handoff
- Handoff Summary 生成
- HandoffRecord 保存
- 接手 Agent 读取交接摘要继续任务
- Handoff 页面或详情查看

Handoff Summary 必须包含：

- original_goal
- current_task
- completed_work
- unfinished_work
- important_constraints
- key_decisions
- errors_and_risks
- next_suggested_steps
- context_needed

原因：

> Handoff 是 ModelGate 最重要的差异化之一。没有 Handoff，就无法证明“任务不中断、模型可交接”。

### 2.7 Workspace 核心视图

必须包含：

- Goal 输入区
- Run Config
- Task Tree
- Card Flow View
- Agent Card
- Agent 状态颜色
- Agent Detail Modal
- Bottom Console
- Handoff Summary Card
- Final Summary 展示

Card Flow View 是 MVP 默认主视图。

原因：

> Workspace 是用户感知产品价值的主界面。MVP 必须先让用户看懂任务如何流转，而不是追求视觉炫酷。

### 2.8 Logs / Execution Trace

必须包含：

- Goal 创建日志
- Task 拆解日志
- Agent 开始执行日志
- 模型调用日志
- Task 状态变化日志
- Handoff 日志
- Error 日志
- Supervisor 汇总日志

原因：

> 多 Agent 系统如果不可追踪，用户无法信任。日志是“可解释协作”的基础。

### 2.9 Quota 基础统计

必须包含：

- 每个模型 token 使用量
- 每个模型 request 使用量
- 手动配置 daily limit
- warning / blocked 状态
- Handoff 触发阈值

不需要真实读取 Claude Code / Codex Plan 额度。

原因：

> 额度感知是 Handoff 的触发基础，但第一版用手动配置和统计估算即可。

---

## 3. Should Have：有它更完整，但不是第一版必须

这些功能建议进入 MVP 后半段，或者在 V0 闭环跑通后补齐。

### 3.1 Agent Registry 可编辑

第一版可以先固定 Agent，后续再支持：

- 创建自定义 Agent
- 编辑 Agent Prompt
- 编辑默认模型
- 编辑备用模型
- 设置 max_steps_per_task
- 设置 handoff_threshold_tokens

判断：

> 固定 Agent 足够跑通核心闭环。可编辑 Agent 会让产品更完整，但不是第一天必须。

### 3.2 Models 页面完整配置

Should Have：

- Provider 管理
- API Key 状态显示
- 模型连接测试
- 模型启用 / 禁用
- 能力标签编辑
- base_url 配置

判断：

> MVP 需要模型配置，但第一版可以先用配置文件、Mock 数据或最小 UI，不必一开始做完整模型管理后台。

### 3.3 Dashboard

Should Have：

- 活跃 Goal
- 最近 Goal
- Agent 状态概览
- 模型额度概览
- 最近 Handoff
- 快速进入 Workspace

判断：

> Dashboard 是入口页，但不是核心价值页。Workspace 比 Dashboard 优先级更高。

### 3.4 Handoff 独立页面

Should Have：

- Handoff 列表
- 按 Goal / Task 筛选
- 查看交接摘要
- 查看交接原因
- 查看接手结果

判断：

> Handoff 详情必须能看，但不一定第一版就需要完整独立页面。可以先在 Workspace Modal 或 Bottom Console 中展示。

### 3.5 Logs 独立页面

Should Have：

- 全局日志列表
- 按 Goal 筛选
- 按 Task 筛选
- 按 Agent 筛选
- 按 level 筛选

判断：

> 日志必须有，但第一版可以先放 Bottom Console；独立 Logs 页面可以后补。

### 3.6 Pixel Office 静态版

Should Have：

- 固定工位
- Worker 显示
- 状态灯
- Station Popover
- Handoff Folder 的轻量表达

判断：

> Pixel Office 是视觉差异化，但不是 MVP 信息架构核心。第一版做到静态或轻动画即可，不做完整办公室动画。

### 3.7 WebSocket / SSE 实时更新

Should Have：

- Task 状态推送
- Log 推送
- Handoff 事件推送
- Goal 进度推送

如果开发成本高，可以先用轮询。

判断：

> 实时性会提升体验，但不是核心闭环成立的必要条件。

### 3.8 简单错误处理与 Retry

Should Have：

- Task failed 状态
- Error Log
- Retry Task
- Generate Handoff from Error

判断：

> MVP 需要基本失败恢复，但不需要复杂自动重试策略。

---

## 4. Could Have：锦上添花

这些功能可以提升体验，但不应该影响 MVP 发布节奏。

### 4.1 Pixel Office 动画增强

Could Have：

- Worker 入场动画
- Worker 行走路径
- Handoff Folder 飞行动画
- 工位动作变化
- Worker 离场动画
- 更多像素细节

判断：

> 有助于产品记忆点，但不能让动画拖慢核心闭环开发。

### 4.2 Quota 页面高级图表

Could Have：

- 7 天 token 趋势
- 请求量趋势
- 模型成本估算
- 使用量预测
- 额度消耗热力图

判断：

> 第一版只要能触发 warning 和 Handoff 即可，高级统计后置。

### 4.3 Research Agent

Could Have：

- 搜索任务
- 资料整理
- 文档摘要
- 外部信息引用

判断：

> Research Agent 有价值，但当前核心闭环用 Planner / Coder / Reviewer / Summarizer / Supervisor 已经足够。

### 4.4 简单任务依赖图

Could Have：

- Task dependency 可视化
- waiting 状态
- 依赖完成后自动进入下一步

判断：

> 可以增强“任务编排”感，但复杂 DAG 不应进入第一版。

### 4.5 Export Summary

Could Have：

- 导出 Final Summary
- 导出 Handoff Summary
- 导出执行日志
- Markdown 下载

判断：

> 对演示和复盘有帮助，但不是核心闭环必需。

### 4.6 Model Performance 基础记录

Could Have：

- 模型调用成功率
- 平均 token
- 平均耗时
- 用户评分

判断：

> 对后续 Model Router 优化有帮助，但完整 Model Performance 属于 V1 或后续。

### 4.7 Prompt 模板管理

Could Have：

- Planner Prompt 模板
- Handoff Summary Prompt 模板
- Supervisor Review Prompt 模板

判断：

> 可以提高输出稳定性，但第一版可以写死在后端配置中。

---

## 5. Won't Have：当前阶段不做

这些功能明确不进入当前 MVP，否则项目会失焦。

### 5.1 普通 ChatGPT Clone

不做：

- 通用聊天主页
- 多轮闲聊
- 单模型对话列表
- Prompt 对话收藏
- 类 ChatGPT 的聊天历史管理

原因：

> ModelGate 不是普通 AI 聊天工具。它的核心是任务级 Agent 协作，而不是聊天窗口。

### 5.2 完整像素办公室

不做：

- 完整办公室地图
- 复杂角色动画
- 拖拽工位
- 自定义办公室布局
- 类游戏化交互
- 大量像素素材系统

原因：

> Pixel Office 是表达层，不是核心流程。MVP 先做 Card Flow View，Pixel Office 只保留轻量差异化。

### 5.3 复杂插件市场 / MCP 生态

不做：

- MCP Marketplace
- 第三方插件发布
- 插件评分
- 插件权限市场
- 插件依赖管理
- 付费插件

原因：

> 插件生态需要安全、权限、审核和版本兼容，不适合当前 MVP。

### 5.4 完全自动化本地操作

不做：

- Agent 自动修改本地项目文件
- 自动执行终端命令
- 自动提交 Git
- 自动创建 PR
- 自动运行高风险脚本
- 无确认执行文件系统操作

原因：

> 当前阶段优先证明协作和交接，不做高风险自动执行。未来也必须用户确认后执行。

### 5.5 Memory / Knowledge Evolution

当前 MVP 不做完整：

- 自动长期 Memory 写入
- Knowledge Evolution Agent
- Memory Draft
- Evolution Review
- Project Memory 检索
- User Preference Memory
- Agent Experience Memory
- Memory 置信度评分
- Memory 过期机制

原因：

> Memory 是 V1 核心，不应提前塞进 MVP。否则会同时引入检索、审核、防污染和 UI 管理复杂度。

### 5.6 Skill Library

当前 MVP 不做完整：

- Skill Library 页面
- Skill 自动生成
- Skill Draft
- Skill 版本管理
- Skill 成功率统计
- Skill Marketplace
- Skill 推荐

原因：

> Skill 是任务沉淀后的复用能力，应该建立在稳定的 Goal / Task / Agent / Handoff 执行记录之上。

### 5.7 多人协作和账号体系

不做：

- 登录注册
- 团队空间
- 多用户协作
- 评论系统
- 权限管理
- 团队知识库
- 多端同步

原因：

> 当前产品应保持本地单用户，先验证核心工作台。

### 5.8 复杂调度

不做：

- 多 Agent 并行执行
- 复杂 DAG 工作流编辑器
- 自动任务优先级优化
- 跨 Goal 调度
- 事件驱动全量编排
- 微服务拆分

原因：

> MVP 先用串行流程保证状态机稳定。复杂调度会显著增加开发和调试成本。

---

## 6. 推荐 MVP 切线

### 6.1 MVP-A：必须先完成

```text
Goal 输入
→ Planner 拆 Task
→ 固定 Agent Station
→ Model Router 基础选择
→ 串行 Runtime
→ 手动 Handoff
→ Handoff Summary
→ Supervisor Final Summary
→ Workspace Card Flow View
→ Bottom Console Logs
```

MVP-A 的验收标准：

1. 输入一个 Goal 后，可以生成 3-5 个 Task。
2. Task 可以分配给固定 Agent Station。
3. Model Router 可以为不同 Agent 选择模型并说明原因。
4. Runtime 可以串行执行任务并更新状态。
5. 用户可以手动触发 Handoff。
6. Handoff Summary 足够让接手 Agent 继续执行。
7. Supervisor 可以生成最终汇总。
8. Workspace Card Flow View 能展示完整任务流转。
9. Bottom Console 能展示关键日志。

### 6.2 MVP-B：核心增强

```text
Agent Registry 可编辑
Models 页面
Quota warning
Handoff 页面
Logs 页面
Pixel Office 静态版
错误 Retry
Workspace 双视图同步
```

MVP-B 的验收标准：

1. 用户可以编辑 Agent 默认模型和备用模型。
2. 用户可以配置至少 3 类模型 Provider 或 Mock Provider。
3. 模型额度接近阈值时可以提示 Handoff。
4. Handoff 页面能查看历史交接记录。
5. Logs 页面能筛选 Goal、Task、Agent 相关日志。
6. Pixel Office 静态版能展示工位、Worker 和状态灯。
7. Card Flow View 与 Pixel Office View 使用同一份 WorkspaceState。
8. Task 出错后可以 Retry 或 Generate Handoff。

### 6.3 MVP-C：体验增强

```text
Dashboard
WebSocket/SSE
Quota 趋势
Pixel Office 轻动画
Export Summary
Model Performance 基础统计
```

MVP-C 的验收标准：

1. Dashboard 能展示活跃 Goal、最近任务和模型额度概览。
2. Workspace 状态可以通过 WebSocket/SSE 或稳定轮询更新。
3. Quota 页面能展示基础趋势。
4. Pixel Office 有轻量 Handoff 表达，但不做完整动画系统。
5. 用户可以导出 Final Summary 或 Handoff Summary。
6. 系统能记录模型调用成功率、耗时和 token 用量。

---

## 7. 当前阶段推荐结论

当前最优先级不是扩展功能，而是尽快完成：

```text
MVP-A：Goal → Task → Agent → Model Router → Handoff → Workspace
```

只有 MVP-A 稳定后，再进入 MVP-B。MVP-C 可以作为演示增强和体验优化，不应阻塞第一版可用闭环。
