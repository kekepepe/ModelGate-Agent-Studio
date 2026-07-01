# Runtime MVP Implementation Log

> 生成日期：2026-07-01
> 对应实现计划：`docs/roadmap/modelgate-next-step-full-plan.md`

---

## 1. 本轮目标

实现最小可运行的 Goal → Task → Worker → Model → Logs → Quota → Handoff 执行链路。

让用户输入 Goal 后点击执行，Runtime 自动完成：Router 选模型 → Quota 检查 → WorkerSession 创建 → Mock Model 调用 → Logs 写入 → Quota 记录 → Task/Agent 状态更新 → 必要时触发 Handoff。

---

## 2. 新增文件

### 后端

| 文件 | 说明 |
|------|------|
| `backend/src/services/mock_provider.py` | Mock 模型提供者，可替换的 Protocol 接口。支持按模型配置输出文本、token 数、延迟，记录调用历史 |
| `backend/src/services/runtime_service.py` | Runtime 编排器。`execute_goal_pipeline()` 全链路执行，`execute_task_step()` 单步执行。内部包含状态机转换、日志写入、配额记录、Handoff 桥接 |
| `backend/src/schemas/runtime.py` | Pydantic 请求/响应模型：ExecutionStepResult、GoalExecutionResult |
| `backend/src/routes/runtime.py` | POST /runtime/execute/{goal_id}、POST /runtime/execute-step/{task_id} |
| `backend/tests/test_mock_provider.py` | MockProvider 9 个单元测试 |
| `backend/tests/test_runtime_service.py` | Runtime 服务 6 个测试（状态转换、管道执行） |
| `backend/tests/test_runtime_api.py` | Runtime API 5 个集成测试 |

### 前端

| 文件 | 说明 |
|------|------|
| `frontend/src/types/runtime.ts` | TypeScript 接口：ExecutionStep、GoalExecutionResult |
| `frontend/src/api/runtime.ts` | executeGoal()、executeStep() Axios 封装 |

---

## 3. 修改文件

| 文件 | 变更 |
|------|------|
| `backend/src/main.py` | 注册 runtime 路由 `app.include_router(runtime_routes.router, ...)` |
| `frontend/src/hooks/useWorkspace.ts` | 新增 `useExecuteGoal`、`useExecuteStep` mutation hooks；`useTaskDetail` 添加 `refetchInterval: 2000` |
| `frontend/src/pages/WorkspacePage.tsx` | 新增 "▶ 执行" 按钮（goal 状态为 planning/running 时可见）；传入 `isLoading` 给 TaskDetailPanel；修复布局为 `flex-1 min-h-0` |
| `frontend/src/components/BottomConsole.tsx` | 展开时添加 `refetchInterval: 2000` 实现日志实时轮询 |
| `frontend/src/components/__tests__/GoalInputPanel.test.tsx` | 补充 `vi` 导入 |
| `frontend/src/components/__tests__/TaskDetailPanel.test.tsx` | 修复未使用变量 |

---

## 4. 当前执行链路

```
POST /runtime/execute/{goal_id}
  │
  ├─ Phase 1: Planning
  │   ├─ 校验 goal.status ∈ {planning, running}
  │   ├─ goal: planning → running
  │   ├─ 查找 planner Task (status=pending/assigned)
  │   └─ _execute_single_task()
  │       ├─ Task: pending → assigned
  │       ├─ Router: select_model(task_type="planning")
  │       ├─ Quota: check_and_intercept(model_id)
  │       │   └─ 如被拦截 → 创建 HandoffTask 镜像 → trigger_handoff → 返回 handoff
  │       ├─ WorkerSession: 创建 (status=running)
  │       ├─ Task: assigned → running
  │       ├─ Agent: idle → running
  │       ├─ Log: agent_step started + task_status_change
  │       ├─ MockProvider.generate(prompt, model_id, system_prompt)
  │       ├─ Log: model_call completed (token_usage, latency, routing_info)
  │       ├─ Quota: record_usage(tokens)
  │       ├─ Task: running → completed (output, tokens_used, duration_ms)
  │       ├─ WorkerSession: running → completed
  │       ├─ Agent: running → idle, total_tasks_completed += 1
  │       └─ Log: agent_step completed + task_status_change
  │
  ├─ Phase 2: Execution
  │   └─ while pending tasks exist:
  │       └─ _execute_single_task() (同上，task_type 从 agent.role 推断)
  │
  └─ Phase 3: Completion
      ├─ 统计 completed/failed/handoff 数量
      └─ goal: running → completed/failed/handoff
```

### 关键设计点

1. **Handoff 桥接**：`handoff_service.trigger_handoff()` 期望 `HandoffTask` 记录（handoff_tasks 表），Runtime 在执行前创建同 ID 的镜像 HandoffTask，保持两个 task 模型同步。

2. **Mock Provider 可替换**：`ModelProvider` Protocol 定义了 `generate(prompt, model_id, ...) -> ModelResponse` 接口。`MockModelProvider` 当前实现是同步的（`time.sleep` 模拟延迟）。真实 Provider 实现同样的 Protocol 即可无缝替换。

3. **Provider 单例**：通过 `get_provider()` / `set_provider()` 管理全局 Provider 实例，测试时可以注入自定义 Provider。

4. **前端执行按钮**：WorkspacePage 中 goal 状态为 `planning` 或 `running` 时显示 "▶ 执行" 按钮，点击调用 `POST /runtime/execute/{goal_id}`。执行中按钮禁用。

---

## 5. 测试结果

```text
Backend: 157 passed (含 20 Runtime 专项测试)
  - test_mock_provider.py: 9 passed
  - test_runtime_service.py: 6 passed
  - test_runtime_api.py: 5 passed

Frontend: 145 passed
  - 含 Workspace 组件测试 40 passed

Total: 302 passed
Status: 零回归
```

---

## 6. 当前限制

| 限制 | 影响 | 计划 |
|------|------|------|
| 仍使用 Mock Provider | 输出为模拟文本，非真实模型结果 | 阶段 2 接入 OpenAI-compatible Provider |
| 无 RuntimeRun/RuntimeStatus 统一查询 | Workspace 需从多接口拼接状态 | 阶段 1 新增 `GET /runtime/status/{goal_id}` |
| Workspace 运行态展示不完整 | 无 RoutingResultCard、RiskBadge、FinalOutput | 阶段 1 补齐 |
| 无 Runtime 事件流 | 执行过程难以追溯和复盘 | 阶段 1 规范 execution_logs 事件类型 |
| Handoff 接手后继续执行未验证 | Handoff 后流程未完整测试 | 阶段 1 E2E 测试覆盖 |
| 无 Supervisor 审查 | 任务完成即结束，无质量把关 | 阶段 3 |
| 无真实 Provider | 无法使用真实 LLM | 阶段 2 |
| 无 E2E 测试 | 缺少端到端验证 | 阶段 1 补齐 3 条 |

---

## 7. 下一步

进入阶段 1：Runtime E2E Demo & Stabilization。

核心任务：
1. 新增 `GET /runtime/status/{goal_id}` RuntimeStatus 查询 API
2. Workspace 运行态展示增强（TaskCard 状态、RoutingResultCard、RiskBadge、FinalOutput）
3. 新增 3 条 E2E/集成测试
4. 规范 Runtime 事件流
