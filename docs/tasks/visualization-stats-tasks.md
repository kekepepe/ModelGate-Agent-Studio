# Visualization & Statistics Implementation Tasks

> 模块：P2-2 Visualization & Statistics
> 日期：2026-07-02

## Round 1 — 模块文档

- [ ] 编写 PRD：`docs/prd/visualization-stats-prd.md`
- [ ] 编写用户故事：`docs/stories/visualization-stats-stories.md`
- [ ] 编写任务拆解：`docs/tasks/visualization-stats-tasks.md`
- [ ] 编写 UI 规范：`docs/ui/visualization-stats-ui-spec.md`

## Round 2 — 后端 Dashboard API

### 2.1 Schema

- [ ] 新增 `backend/src/schemas/dashboard.py`
- [ ] 定义 Summary Cards、Trend、ModelUsage、ToolUsage、AgentPerformance、RecentGoal schemas

### 2.2 Service

- [ ] 新增 `backend/src/services/stats_service.py`
- [ ] 实现 `get_dashboard_stats(db)`
- [ ] 实现 `get_dashboard_trends(db, days)`
- [ ] 实现 `get_agent_performance(db)`
- [ ] 日期范围按本地当前日期的 UTC day window 计算
- [ ] 确保空数据返回 0 和空数组

### 2.3 Routes

- [ ] 新增 `backend/src/routes/dashboard.py`
- [ ] 实现 `GET /dashboard/stats`
- [ ] 实现 `GET /dashboard/trends?days=7`
- [ ] 实现 `GET /dashboard/agent-performance`
- [ ] 注册 router 到 `backend/src/main.py`

## Round 3 — 前端 Dashboard

### 3.1 依赖

- [ ] 安装 `recharts`

### 3.2 类型/API/Hook

- [ ] 新增 `frontend/src/types/dashboard.ts`
- [ ] 新增 `frontend/src/api/dashboard.ts`
- [ ] 新增 `frontend/src/hooks/useDashboard.ts`

### 3.3 组件

- [ ] 新增 `StatsSummaryCards.tsx`
- [ ] 新增 `TokenUsageChart.tsx`
- [ ] 新增 `ModelUsagePieChart.tsx`
- [ ] 新增 `AgentPerformanceChart.tsx`
- [ ] 新增 `QuotaTrendChart.tsx`
- [ ] 新增 `ToolUsageChart.tsx`

### 3.4 页面集成

- [ ] 新增 `DashboardPage.tsx`
- [ ] 在 `App.tsx` 添加 `/dashboard` 路由和导航
- [ ] 在 `QuotaOverviewPage.tsx` 嵌入 Quota 趋势图

## Round 4 — 测试

### 后端

- [ ] 新增 `backend/tests/test_dashboard_api.py`
- [ ] 测试 stats 空数据
- [ ] 测试 stats 有数据聚合
- [ ] 测试 trends 默认和 days 参数
- [ ] 测试 agent-performance 成功率计算

### 前端

- [ ] 新增 Dashboard 相关组件测试
- [ ] Mock hooks 或 API 返回，验证摘要卡片、图表空状态、页面加载/错误状态

## Round 5 — 自查

- [ ] 检查 API 字段命名是否与前端类型一致
- [ ] 检查空状态和错误状态
- [ ] 检查图表响应式容器
- [ ] 检查是否引入过度抽象

## Round 6 — 修复

- [ ] 修复测试失败
- [ ] 修复 build/type/lint 问题
- [ ] 修复聚合边界条件

## Round 7 — 实施总结

- [ ] 新增 `docs/implementation/phase9-visualization-stats-summary.md`
- [ ] 记录新增/修改文件
- [ ] 记录测试结果
- [ ] 记录验收标准达成情况
