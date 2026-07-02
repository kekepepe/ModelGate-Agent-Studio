# Visualization & Statistics PRD

> 模块：P2-2 Visualization & Statistics
> 日期：2026-07-02

## 1. 背景

ModelGate Agent Studio 已具备 Goal 执行、模型路由、Quota 记录、Handoff、日志、Supervisor Review、Knowledge Base 与 MCP Tool Layer。当前系统产生了大量运行数据，但缺少一个统一入口将这些数据聚合成趋势、分布和健康度视图。

Visualization & Statistics 的目标是把执行数据转化为可操作的仪表板，帮助用户快速判断：系统是否在运行、Token 使用是否异常、模型/工具使用分布如何、Agent 成功率如何、Quota 是否接近风险线。

## 2. 目标

1. 提供系统级 Dashboard 聚合统计 API。
2. 提供最近 N 天趋势数据 API。
3. 提供 Agent 执行表现 API。
4. 前端 Dashboard 展示摘要卡片与至少 4 类图表。
5. Quota 页面补充趋势可视化，帮助观察资源消耗。
6. 保持空状态、加载状态、错误状态完整。

## 3. 非目标

- 不做实时 WebSocket 推送。
- 不做可拖拽 Dashboard 布局。
- 不做高级 BI 查询编辑器。
- 不引入复杂动画或 3D 可视化。
- 不修改现有 Runtime 执行链路。

## 4. 用户价值

| 用户 | 需求 | 价值 |
|------|------|------|
| 项目操作者 | 查看系统今日运行状态 | 快速判断是否有异常 |
| Agent 团队配置者 | 比较 Agent 成功率与任务量 | 调整角色配置和模型分配 |
| 模型/Quota 管理者 | 查看 Token、请求、Quota 趋势 | 防止成本或配额失控 |
| 调试者 | 查看工具调用与 Handoff 统计 | 定位执行链路薄弱环节 |

## 5. 数据范围

Dashboard 聚合以下已有数据：

- `goals`：活跃目标、今日完成目标、最近目标。
- `tasks`：任务完成/失败趋势、Agent 任务统计、Token/耗时统计。
- `agent_stations`：Agent 状态、累计完成/失败/移交统计。
- `quota_records`：模型 Token、请求次数、Quota 状态、使用率。
- `execution_logs`：模型调用、工具调用、Token 使用、延迟。
- `tool_call_records`：工具调用量、成功率。
- `handoff_records`：Handoff 今日数量与 Agent 表现。

## 6. API 需求

### 6.1 `GET /dashboard/stats`

返回当前系统概览：

```json
{
  "active_goals": 2,
  "completed_goals_today": 3,
  "total_tokens_today": 12000,
  "total_model_calls_today": 24,
  "total_tool_calls_today": 8,
  "handoffs_today": 1,
  "agents_status": [{"agent_id": "a1", "name": "Coder", "role": "coder", "status": "idle"}],
  "model_usage": [{"model_id": "m1", "display_name": "GPT-4o", "tokens_used": 5000, "calls_count": 10}],
  "tool_usage": [{"tool_name": "file_read", "call_count": 5, "success_rate": 0.8}],
  "recent_goals": [{"id": "g1", "title": "Build feature", "status": "done", "updated_at": "..."}]
}
```

### 6.2 `GET /dashboard/trends?days=7`

返回最近 N 天趋势：

```json
{
  "daily": [
    {
      "date": "2026-07-02",
      "tokens": 3200,
      "model_calls": 6,
      "tool_calls": 4,
      "handoffs": 1,
      "tasks_completed": 3,
      "tasks_failed": 1,
      "quota_usage_percent": 42.5
    }
  ]
}
```

### 6.3 `GET /dashboard/agent-performance`

返回 Agent 维度表现：

```json
{
  "agents": [
    {
      "agent_id": "a1",
      "name": "Coder",
      "role": "coder",
      "tasks_completed": 8,
      "tasks_failed": 2,
      "success_rate": 0.8,
      "avg_tokens_per_task": 1800,
      "avg_duration_ms": 4200,
      "total_handoffs_initiated": 1
    }
  ]
}
```

## 7. 前端需求

Dashboard 页面包含：

1. 顶部摘要卡片：活跃目标、今日完成、今日 Token、今日工具调用、今日 Handoff。
2. Token 趋势折线图。
3. 模型使用分布饼图。
4. Agent 成功率柱状图。
5. Quota 趋势面积图。
6. 工具使用统计柱状图。
7. 最近目标列表。

## 8. 验收标准

1. `GET /dashboard/stats` 返回系统级聚合统计。
2. `GET /dashboard/trends` 返回可用于图表的时间序列。
3. `GET /dashboard/agent-performance` 返回 Agent 任务成功率和平均消耗。
4. Dashboard 页面展示至少 4 种图表。
5. 图表在空数据时展示明确空状态。
6. 页面具备加载态、错误态。
7. 前端 build 通过。
8. 后端 Dashboard API 测试通过。
