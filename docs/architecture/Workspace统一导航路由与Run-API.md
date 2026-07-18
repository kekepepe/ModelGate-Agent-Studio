# Workspace 统一导航路由与 Run API

> 生效日期：2026-07-18  
> 对应计划：`docs/roadmap/2026-07-18-Workspace统一导航与信息架构重构开发计划.md`

## 1. 页面路由

| 路由 | 页面职责 | 上下文 |
|---|---|---|
| `/studio` | 选择团队并创建 Run | 无 |
| `/workspace` | Run Overview、状态筛选、搜索 | Run 列表 |
| `/workspace/new?team={teamId}` | 配置 Goal 与 Run | teamId |
| `/workspace/runs/{runId}` | 具体 Run 的 Goal、Task Tree、Card/Pixel、Console 与控制 | runId |
| `/assets?runId={runId}` | 当前 Run 产物与导出记录 | runId |
| `/logs?runId={runId}&goalId={goalId}` | 当前 Run 日志 | runId、goalId |
| `/evolution?runId={runId}&goalId={goalId}` | 当前 Run 的 Memory/Skill 审核 | runId、goalId |

旧路由 `/workspace/{id}`、`/run/{id}`、`/agent-workspace/{id}` 会重定向至 `/workspace/runs/{id}`。后端 Run 解析同时接受新 `run_id` 和旧 `goal_id`，用于兼容历史收藏。

## 2. Run 标识规则

- 创建 Goal 时同步分配公开、稳定的 `run_id`。
- Runtime 仍在真正执行时才创建 `RuntimeRun`，但复用已分配的 `run_id`。
- 因此规划、暂停、执行、审查和完成阶段使用同一 URL。
- 前端离开 Run Detail 只会卸载观察界面，不调用 Stop；后台执行线程与数据库状态不依赖页面连接。

## 3. Run API

### 创建与列表

```http
POST /api/v1/goals
GET  /api/v1/runs?status={active|completed|failed|stopped}&team_id={id}&search={text}
```

创建响应包含：

```json
{
  "goal_id": "goal-uuid",
  "run_id": "run-uuid",
  "status": "idle"
}
```

### 详情、工作区和产物

```http
GET  /api/v1/runs/{runId}
GET  /api/v1/runs/{runId}/workspace
GET  /api/v1/runs/{runId}/assets
POST /api/v1/runs/{runId}/export
```

`GET /runs/{runId}` 返回 Overview 所需的真实聚合数据：Goal/Runtime 状态、Task 进度、活跃 Agent、Token/Quota、Handoff、错误与产物数量。

`POST /runs/{runId}/export` 注册一个 `run_snapshot` Artifact，并返回可下载 JSON；非完成态导出明确标记为 `snapshot=true`。

### 跨模块筛选

```http
GET /api/v1/logs?run_id={runId}
GET /api/v1/knowledge/evolution?run_id={runId}&goal_id={goalId}
```

服务端会把 `run_id` 解析为对应 Goal；页面同时保留 `runId`，用于“返回当前 Workspace”。

## 4. 恢复与控制

- Run Detail 以 URL 的 `runId` 重新请求完整 Workspace State。
- SSE 推送用于即时刷新，2 秒轮询保留为断线恢复兜底。
- 视图优先级：`?view=card|pixel` → `localStorage[workspace:view:{runId}]` → `card`。
- Pause 支持 `planning`、`running`、`reviewing`；规划态恢复回 `planning`，执行态恢复回 `running`。
- Stop 必须经过浏览器确认，成功后 Goal/Run/未完成 Task 进入取消态。
- 导航到 Studio、Overview、Logs、Evolution 或 Assets 不触发 Pause/Stop。

## 5. 错误行为

无效 Run、已删除 Run 或后端不可用时，Run Detail 显示独立错误状态，提供“重试”“返回 Workspace”“返回 Studio”，不会渲染空白工作区。
