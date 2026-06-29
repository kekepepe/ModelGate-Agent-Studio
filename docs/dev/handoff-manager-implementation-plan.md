# Handoff Manager Implementation Plan

## 1. 已阅读文档

- `docs/dev/module-development-sop.md`
- `docs/prd/handoff-manager-prd.md`
- `docs/stories/handoff-manager-stories.md`
- `docs/tasks/handoff-manager-tasks.md`
- `docs/ui/handoff-manager-ui-spec.md`
- 参考了现有 Agent Registry / Model Router / Quota Manager 的前后端实现风格。

## 2. 当前项目结构判断

当前项目已经具备完整的模块化基础：

- 后端：`backend/src/models`、`schemas`、`services`、`routes` 分层清晰，FastAPI 路由统一挂载到 `/api/v1`，测试通过 `backend/tests/conftest.py` 重建数据库。
- 前端：`frontend/src/types`、`api`、`hooks`、`pages`、`components` 分层清晰，React Router 在 `App.tsx` 中集中注册页面。
- 已完成依赖模块：Agent Registry、Model Router、Quota Manager。
- 未完成依赖模块：Agent Workspace、Task、WorkerSession、ExecutionLog / Logs。Handoff Manager 的 P0 需要这些概念，因此本模块将只实现 Handoff 所需的最小数据对象，不扩展成完整 Workspace 或 Logs 模块。

## 3. P0 / P1 范围判定

### P0 Stories

- US-HM-01：手动触发任务交接
- US-HM-02：查看交接状态流转
- US-HM-03：查看完整交接摘要
- US-HM-04：接手 Agent 接受交接
- US-HM-05：交接完成后记录结果
- US-HM-06：交接事件写入日志
- US-HM-07：防止重复触发交接

### P0 Tasks

- HM-T1.1：创建 `handoff_records` 表
- HM-T1.2：HandoffStatus 状态机与转换规则
- HM-T1.3：HandoffSummary 数据结构与兜底生成
- HM-T2.1：`POST /tasks/:taskId/handoff`
- HM-T2.2：`GET /handoffs/:handoffId`
- HM-T2.3：`POST /handoffs/:handoffId/accept`
- HM-T2.4：`PATCH /handoffs/:handoffId/result`
- HM-T3.1：Summary mock 生成器
- HM-T3.2：上下文数据收集服务（MVP 最小实现）
- HM-T3.3：Summary 生成集成到工作流
- HM-T4.1：Handoff 事件写入 ExecutionLog（最小表实现）
- HM-T5.1：HandoffStatusIndicator
- HM-T5.2：Handoff 触发面板
- HM-T5.3：Handoff Detail Drawer
- HM-T5.4：接受交接 UI
- HM-T7.1 / HM-T7.2 / HM-T7.3：基础测试

### P1 本轮纳入范围

- HM-T6.1：`GET /handoffs` 列表 API
- HM-T6.2：`/handoffs` 独立列表页

原因：当前 Workspace 尚未实现，如果只做 Workspace 内入口，前端无法独立验收；独立 Handoff 页面可以作为 MVP-B 入口，同时复用同一详情抽屉。

### 暂缓范围

- 完整 Agent Workspace Card Flow / Pixel Office 动画
- 完整 Task/Goal 模块
- 完整 Worker runtime
- 完整 Logs / Observability 页面
- 真实 LLM Summary 生成
- Regenerate Summary
- 自动 Handoff
- 企业权限、审批、多租户

## 4. 计划新增文件

### 后端新增

- `backend/migrations/004_create_handoff_records.sql`
- `backend/src/models/handoff.py`
- `backend/src/schemas/handoff.py`
- `backend/src/services/handoff_service.py`
- `backend/src/routes/handoffs.py`
- `backend/tests/test_handoff_api.py`
- `backend/tests/test_handoff_service.py`

### 前端新增

- `frontend/src/types/handoff.ts`
- `frontend/src/api/handoffs.ts`
- `frontend/src/hooks/useHandoffs.ts`
- `frontend/src/pages/HandoffPage.tsx`
- `frontend/src/components/HandoffStatusTag.tsx`
- `frontend/src/components/HandoffStatusIndicator.tsx`
- `frontend/src/components/HandoffConfirmModal.tsx`
- `frontend/src/components/HandoffDetailDrawer.tsx`
- `frontend/src/components/HandoffList.tsx`
- `frontend/src/components/HandoffAcceptButton.tsx`
- `frontend/src/components/__tests__/HandoffStatusIndicator.test.tsx`
- `frontend/src/components/__tests__/HandoffConfirmModal.test.tsx`
- `frontend/src/components/__tests__/HandoffDetailDrawer.test.tsx`
- `frontend/src/components/__tests__/HandoffList.test.tsx`

## 5. 计划修改文件

### 后端修改

- `backend/src/main.py`：注册 Handoff 路由，导入模型以参与 `Base.metadata.create_all`。
- `backend/src/routes/__init__.py`：如需要，暴露 Handoff 路由模块。

### 前端修改

- `frontend/src/App.tsx`：新增 `/handoffs` 路由和导航入口。

### 文档修改

- `docs/dev/implementation-log.md`：第 7 轮追加 Handoff Manager 实现日志。

## 6. 后端实现顺序

1. 新增 `HandoffRecord`、`HandoffTask`、`WorkerSession`、`ExecutionLog` 最小模型。
2. 新增迁移脚本 `004_create_handoff_records.sql`，包含 Handoff 表和最小 stub 表结构。
3. 定义 Handoff 枚举、Pydantic schema、Summary schema。
4. 实现状态机：合法转换与 active handoff 判断。
5. 实现兜底 Summary 生成器，确保 9 个字段永远存在。
6. 实现最小上下文收集：从 `HandoffTask`、Agent、Model、ExecutionLog 汇总基础信息。
7. 实现 `POST /tasks/{task_id}/handoff`：校验 Task 状态、校验 to_agent、to_model、阻止重复，创建记录，写日志，生成 Summary，状态到 ready。
8. 实现 `GET /handoffs/{handoff_id}`：返回完整摘要、关联 Task/Agent/Worker 基本信息。
9. 实现 `POST /handoffs/{handoff_id}/accept`：ready → accepted，创建最小 WorkerSession，更新 task 到 running，写日志。
10. 实现 `PATCH /handoffs/{handoff_id}/result`：accepted → completed，记录 result、note、completed_at，写日志。
11. 实现 `GET /handoffs`：列表、筛选、分页，支持前端独立 Handoff 页面。
12. 为测试和手动演示提供最小 demo task 创建 API（如需要则放在 Handoff 路由中，明确标注为 demo/support，不替代完整 Task 模块）。

## 7. 前端实现顺序

1. 新增 `types/handoff.ts`，定义 HandoffStatus、HandoffReason、HandoffResult、HandoffSummary、HandoffRecord、列表项和请求类型。
2. 新增 `api/handoffs.ts`，对接后端接口。
3. 新增 `useHandoffs.ts`，提供列表、详情、触发、accept、result hooks。
4. 新增 `HandoffStatusTag` 和 `HandoffStatusIndicator`。
5. 新增 `HandoffDetailDrawer`，展示参与者、时间线、9 个 Summary 字段、Result 区域、Accept 按钮。
6. 新增 `HandoffConfirmModal`，支持选择 Agent、原因、描述并触发 Handoff。
7. 新增 `HandoffList`，实现表格/移动端卡片列表、状态/结果标签、行点击打开详情。
8. 新增 `HandoffPage`，实现 header、filter bar、loading/error/empty/no-result 状态、详情抽屉。
9. 修改 `App.tsx`，新增 `/handoffs` 导航入口。

## 8. 测试实现顺序

### 后端测试

1. `test_handoff_service.py`
   - 状态机合法/非法转换
   - active handoff 判断
   - Summary fallback 字段完整性
   - 事件日志创建
2. `test_handoff_api.py`
   - 创建 handoff happy path
   - 重复 handoff 返回 409
   - Task 不存在 / 状态非法 / Agent 不存在
   - 获取详情完整 Summary
   - accept ready handoff 并创建 WorkerSession
   - result 更新 accepted handoff
   - 列表筛选与分页

### 前端测试

1. `HandoffStatusIndicator.test.tsx`：6 种状态渲染。
2. `HandoffConfirmModal.test.tsx`：表单字段、Agent 选择、提交、取消。
3. `HandoffDetailDrawer.test.tsx`：9 个 Summary 字段、timeline、Accept、Result 展示。
4. `HandoffList.test.tsx`：列表渲染、empty、row click、状态/结果标签。

## 9. Mock / Stub 数据说明

- Summary 生成：MVP 使用后端 fallback/mock 生成器，不调用真实 LLM。原因：真实 Agent Runtime 和 Summarizer 调用链尚未实现。
- Task/Worker/ExecutionLog：本模块新增最小 stub 表，只包含 Handoff P0 需要的字段。原因：完整 Workspace、Task、Worker、Logs 模块尚未开发。
- 前端 Handoff 页面：使用真实 Handoff API，不使用本地 mock fallback。
- HandoffConfirmModal 的 Agent 列表：复用 Agent Registry `GET /agents` 真实接口。

## 10. 真实接口依赖

- Agent Registry：校验 `to_agent_id`，展示 from/to agent 名称。
- Model Router：校验或展示 `to_model_id`，如缺失则使用目标 Agent 的 `default_model_id`。
- Quota Manager：后续可把 `quota_exceeded` 触发原因与 quota status 连接，本轮只保存原因字段。
- Logs / Observability：本轮实现最小 `ExecutionLog` 写入和查询基础，不实现完整 Logs 页面。
- Agent Workspace：本轮不实现 Workspace Card Flow，只提供可复用组件与 `/handoffs` 页面。

## 11. 风险点

| 风险 | 应对 |
|---|---|
| Task / Worker / Logs 模块未就绪 | 在 Handoff 模块内实现最小 stub，字段只覆盖 Handoff P0，后续模块可迁移或扩展 |
| PRD 要求异步 summary，但测试需要稳定 | MVP 中同步生成 mock Summary 并快速完成 requested → generating_summary → ready，保留状态时间戳和日志 |
| Workspace UI 未实现导致 P0 UI 无入口 | 先实现独立 `/handoffs` 页面和可复用组件，Workspace 开发时复用这些组件 |
| SQLite 不支持 JSONB | 使用 Text 存 JSON，与现有 Agent/Model 的 JSON list 存储方式一致 |
| Handoff 状态机复杂 | 集中在 service 中定义转换矩阵和 `is_active_handoff`，用单元测试覆盖 |
| 可能影响已有模块 | 只新增 Handoff 路由和导航入口，不改 Agent/Router/Quota 业务逻辑 |

## 12. 轮次交付标准

- 第 1 轮：本文件已生成。
- 第 2 轮：Handoff 后端模型、schema、service、API 可用。
- 第 3 轮：`/handoffs` 页面与核心组件可用。
- 第 4 轮：后端和前端基础测试通过。
- 第 5 轮：输出对照 PRD / Stories / Tasks / UI Spec 的自查报告。
- 第 6 轮：只修复自查报告问题并重跑相关测试。
- 第 7 轮：追加 `docs/dev/implementation-log.md`。
