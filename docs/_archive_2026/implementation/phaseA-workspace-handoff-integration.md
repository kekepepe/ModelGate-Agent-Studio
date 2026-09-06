# Phase A：Workspace Handoff 收拢 — 实施记录

> 日期：2026-07-14  
> 对应方案：[下一阶段产品与开发总方案](../roadmap/2026-07-14-下一阶段产品与开发总方案.md) 的 Phase A。

## 已完成

1. 顶层导航移除了 Handoff Manager、Model Router、Quota Manager 的日常入口；旧路由保留，以支持既有审计和兼容性。
2. Handoff 服务已支持 Runtime / Workspace 使用的 `tasks` 表，不再只支持独立演示用的 `handoff_tasks` 表。
3. Workspace State 新增 Goal 级交接时间线，并为每个 Task 提供其最新交接及完整交接列表。
4. Workspace 的 Task Card 现在展示当前 Agent、模型、输出片段与交接入口；运行中或失败的 Task 可直接触发 Handoff。
5. Task Detail 新增 `Handoff` 标签，交接记录在该 Task 的上下文中显示；详情通过 Workspace 内侧滑 Sheet 打开。
6. 接受或保存 Handoff 结果后会刷新 Workspace 查询缓存，用户无需跳转独立页面查看接手状态。
7. Workspace State 额外聚合每个 Task 的最新 Router 决策、当前 Worker Context、模型额度状态和最近 10 条日志；Router / Context / Logs 标签不再请求独立接口。
8. Model Router 已改为读取 Quota Manager 的真实记录：`limited` / `cooldown` 模型会在评分前被排除，`warning` / `near_limit` 仍会作为路由风险与评分因素呈现。若某个 Agent 的默认模型被阻断，Runtime 会生成可见的自动 Handoff，而不是静默替换模型。
9. Provider 调用失败会优先生成带错误上下文的自动 Handoff；接受交接后，Runtime 会复用接手 Worker 已确认的模型与上下文继续执行，而不是重新路由回失败模型。
10. 本地首次启动会在 Agent Station 为空时写入六个可用的默认角色 Agent；若部署环境刻意未配置 Planner，创建 Goal 会返回明确的配置错误，不再生成无法执行的未分配 Task。
11. 新 Goal 在完整角色配置下会生成可观察的 `Planner → Coder → Reviewer` 串行计划；最小部署仍可只运行 Planner，不会伪造并行或 DAG 调度能力。
12. 中心区已改为编号任务协作流，顺序与 Workspace API 的 `flow_position` 一致；每一步仍使用原 Task Card 展示实际执行者、模型、额度、输出与 Handoff。
13. Runtime Status 新增最终运行报告：完成/未完成任务、Supervisor 质量结论、风险、实际使用模型和 Handoff 次数均在 Workspace 完成面板呈现；Provider 尚无单价表时不会伪造货币成本。

## 关键兼容性决策

- 保留 `HandoffTask`、`/handoff/tasks` 与 `/handoffs`：它们仍可服务于既有测试、调试和历史审计。
- 新的日常路径使用 Runtime 创建的 `Task`。源模型优先取该 Task 当前 Worker 的模型，若没有 Worker，则回退至所属 Agent 的默认模型。
- Workspace Task 没有 `assigned_model_id` 字段；接手模型由新建的 `WorkerSession` 保存，避免为了 UI 迁移引入重复字段。

## 验证

```text
backend: 全量测试 217 passed
frontend: 全量测试 153 passed
frontend: 生产构建通过
浏览器级验证: 新建 Goal → 分配 Planner → 执行 → 完成，并在 Workspace 显示实际模型、额度、输出和日志
```

## 后续工作

1. 将已人工验证的 Workspace 主流程固化为可重复的浏览器级 E2E 脚本，并补齐正常、取消、失败、接手完成四条 Handoff 路径。
2. 继续把中心区演进为可读的任务依赖与协作流，而不回到两组静态卡片。
