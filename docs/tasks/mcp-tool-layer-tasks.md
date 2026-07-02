# MCP Tool Layer MVP 开发任务拆解

> 基于 `docs/stories/mcp-tool-layer-stories.md` 的 6 条 P0 用户故事拆解

---

## Epic: MCP Tool Layer MVP

**目标：** 提供 Tool Registry + 工具执行引擎 + Runtime 工具调用循环 + 前端管理页面。

---

## Feature 1: Tool Registry 数据模型与 API

> 对应 Story: US-TL-01 / US-TL-02 / US-TL-03

### Task 1.1: 创建 tools 数据库迁移

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T1.1 |
| **story_id** | US-TL-01 / US-TL-02 |
| **文件** | `backend/migrations/009_create_tools.sql` |
| **任务说明** | 创建 `tool_definitions` 表：id, name (UNIQUE), display_name, description, category, risk_level CHECK(low/medium/high), parameters (TEXT/JSON), is_enabled (BOOLEAN default true), created_at, updated_at。创建 `tool_call_records` 表：id, goal_id, task_id, agent_id, worker_id, tool_name, tool_input (TEXT), tool_output (TEXT), status CHECK(started/completed/failed), latency_ms, error_message, created_at。索引覆盖：tool_name, goal_id, task_id, created_at。 |
| **完成标准** | 迁移脚本可执行，表结构与 PRD 对齐 |
| **依赖任务** | 无 |

### Task 1.2: 创建 Tool ORM 模型

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T1.2 |
| **story_id** | US-TL-01 / US-TL-06 |
| **文件** | `backend/src/models/tool.py` |
| **任务说明** | 创建 `ToolDefinition` 和 `ToolCallRecord` SQLAlchemy 模型，字段对齐迁移。json.loads/json.dumps 处理 parameters/tool_input 序列化。 |
| **完成标准** | 模型可被 SQLAlchemy 正确映射 |
| **依赖任务** | TL-T1.1 |

### Task 1.3: 创建 Tool Pydantic Schemas

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T1.3 |
| **story_id** | US-TL-02 / US-TL-03 |
| **文件** | `backend/src/schemas/tool.py` |
| **任务说明** | `ToolCreate`（name, display_name, description, category, risk_level, parameters dict, is_enabled）、`ToolUpdate`（全部可选）、`ToolOut`（带 id 和 timestamps）、`ToolCallRecordOut`。使用 `ConfigDict(from_attributes=True)`。 |
| **完成标准** | Schema 通过 Pydantic 校验，与 ORM 模型对齐 |
| **依赖任务** | TL-T1.2 |

### Task 1.4: 创建 Tools API 路由

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T1.4 |
| **story_id** | US-TL-01 / US-TL-02 / US-TL-03 / US-TL-05 |
| **文件** | `backend/src/routes/tools.py` |
| **任务说明** | 6 个端点：`GET /tools`（分页 + 筛选）、`GET /tools/{id}`、`POST /tools`（防重名 409）、`PUT /tools/{id}`、`DELETE /tools/{id}`、`PATCH /tools/{id}/toggle`。Tool Call 查询：`GET /tools/calls`（分页 + goal_id/task_id/tool_name 筛选）、`GET /tools/calls/{id}`。 |
| **完成标准** | 所有端点可调用，错误处理完整 |
| **依赖任务** | TL-T1.3 |

---

## Feature 2: Tool Executor 执行引擎

> 对应 Story: US-TL-04 / US-TL-06

### Task 2.1: 创建 Tool Executor 服务

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T2.1 |
| **story_id** | US-TL-04 |
| **文件** | `backend/src/services/tool_service.py` |
| **任务说明** | `ToolExecutor` 类：`async execute(db, tool_name, arguments, goal_id, task_id, agent_id, worker_id) -> ToolCallRecord`。包含工具注册表（dict[tool_name, callable]）、权限校验（查 agent.allowed_tools）、日志记录。每个工具实现为独立 async 函数。 |
| **完成标准** | 4 个内置工具可正确执行 |
| **依赖任务** | TL-T1.4 |

### Task 2.2: 实现 4 个内置工具

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T2.2 |
| **story_id** | US-TL-04 |
| **文件** | `backend/src/services/tool_service.py`（内置函数） |
| **任务说明** | 实现 `_file_read(path)`: 读取文件返回内容或 FileNotFoundError；`_file_search(pattern, dir?)`: 使用 glob 匹配文件列表；`_git_diff(ref?, file?)`: 执行 git diff 命令返回结果；`_test_runner(command, cwd?)`: 使用 subprocess 执行测试命令返回 stdout/stderr。每个工具返回 {"success": bool, "result": str}。 |
| **完成标准** | 4 个工具可独立调用并返回正确结果 |
| **依赖任务** | TL-T2.1 |

### Task 2.3: 内置工具的种子数据

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T2.3 |
| **story_id** | US-TL-01 |
| **文件** | `backend/src/services/tool_service.py` |
| **任务说明** | 提供 `seed_builtin_tools(db)` 函数，将 4 个 MVP 工具写入 tool_definitions 表（幂等：存在则跳过）。在 app 启动时调用。 |
| **完成标准** | 首次启动后，GET /tools 返回 4 个工具 |
| **依赖任务** | TL-T2.2 |

---

## Feature 3: Runtime 工具调用循环

> 对应 Story: US-TL-04 / US-TL-06

### Task 3.1: 扩展 ModelResponse 支持 tool_calls

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T3.1 |
| **story_id** | US-TL-04 |
| **文件** | `backend/src/services/providers/base.py` |
| **任务说明** | `ModelResponse` dataclass 增加 `tool_calls: Optional[List[Dict[str, Any]]] = None` 字段。包含 id, function.name, function.arguments。 |
| **完成标准** | ModelResponse 可携带 tool_calls 数据 |
| **依赖任务** | 无 |

### Task 3.2: 扩展 Mock Provider 支持 tool_calls

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T3.2 |
| **story_id** | US-TL-04 |
| **文件** | `backend/src/services/providers/mock_provider.py` |
| **任务说明** | Mock 支持配置 `_mock_tool_calls` 字典，per-model 配置是否返回 tool_calls。当配置了 tool_calls 时，`finish_reason="tool_calls"` 并返回指定的 tool_calls 数组。否则返回 "stop"。 |
| **完成标准** | Mock provider 可模拟 tool_calls 响应 |
| **依赖任务** | TL-T3.1 |

### Task 3.3: Runtime 集成工具调用循环

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T3.3 |
| **story_id** | US-TL-04 / US-TL-06 |
| **文件** | `backend/src/services/runtime_service.py` |
| **任务说明** | 修改 `_execute_single_task`：1) model call 前将 agent.allowed_tools 转为 OpenAI tools 格式传入 ModelRequest.tools；2) model call 后检查 response.finish_reason；3) 若是 "tool_calls"，进入工具调用循环：解析 tool_calls → 权限校验 → 执行 → 记录日志 → 追加 messages → 循环调用 model（最多 max_tool_calls_per_task 次）；4) 最终输出写入 task.output。 |
| **完成标准** | 工具调用循环可端到端运行 |
| **依赖任务** | TL-T2.1, TL-T3.2 |

### Task 3.4: main.py 注册 tools router + 启动 seed

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T3.4 |
| **story_id** | US-TL-01 |
| **文件** | `backend/src/main.py` |
| **任务说明** | `import tools as tools_router` → `app.include_router(tools_router.router, prefix=..., tags=["Tools"])`。在 startup 事件中调用 `seed_builtin_tools(db)`。 |
| **完成标准** | 启动后 /api/v1/tools 可访问 |
| **依赖任务** | TL-T1.4, TL-T2.3 |

---

## Feature 4: 前端 Tool Manager + Workspace 集成

> 对应 Story: US-TL-01 / US-TL-05

### Task 4.1: 创建前端类型和 API 客户端

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T4.1 |
| **story_id** | US-TL-01 / US-TL-05 |
| **文件** | `frontend/src/types/tool.ts`, `frontend/src/api/tools.ts` |
| **任务说明** | TypeScript 类型：`ToolDefinition`, `ToolCallRecord`, `ToolCreateData`, `ToolUpdateData`。Axios 客户端：`getTools()`, `getTool()`, `createTool()`, `updateTool()`, `deleteTool()`, `toggleTool()`, `getToolCalls()`, `getToolCall()`。 |
| **完成标准** | 类型与实际 API 响应对齐 |
| **依赖任务** | TL-T1.4 |

### Task 4.2: 创建 TanStack Query hooks

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T4.2 |
| **story_id** | US-TL-01 / US-TL-05 |
| **文件** | `frontend/src/hooks/useTools.ts` |
| **任务说明** | `useTools(filters)`, `useTool(id)`, `useCreateTool()`, `useUpdateTool()`, `useDeleteTool()`, `useToggleTool()`, `useToolCalls(filters)`, `useToolCall(id)`。 |
| **完成标准** | Hooks 正确产生 API 调用 |
| **依赖任务** | TL-T4.1 |

### Task 4.3: 创建 ToolManagerPage

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T4.3 |
| **story_id** | US-TL-01 / US-TL-02 / US-TL-03 |
| **文件** | `frontend/src/pages/ToolManagerPage.tsx` |
| **任务说明** | 工具列表表格（name, display_name, category, risk_level, is_enabled, 操作）。筛选：category dropdown + risk_level dropdown。添加/编辑模态框。删除确认。启用/禁用 toggle。空状态 / 加载状态 / 错误状态。 |
| **完成标准** | 页面可访问、可管理工具 |
| **依赖任务** | TL-T4.2 |

### Task 4.4: App.tsx 添加路由 + TaskDetailPanel 展示工具调用

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T4.4 |
| **story_id** | US-TL-01 / US-TL-05 |
| **文件** | `frontend/src/App.tsx`, `frontend/src/components/TaskDetailPanel.tsx` |
| **任务说明** | 添加 `/tools` 路由和导航入口。TaskDetailPanel 底部新增"工具调用记录"区域，使用 useToolCalls({ task_id }) 查询并按时间轴展示。 |
| **完成标准** | 导航可见，工具调用记录在 Task 详情展示 |
| **依赖任务** | TL-T4.3 |

### Task 4.5: AgentConfigForm 工具权限改为动态加载

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T4.5 |
| **story_id** | US-TL-01 / US-TL-06 |
| **文件** | `frontend/src/components/AgentConfigForm.tsx` |
| **任务说明** | Step 2 的工具权限 checkbox 从 MOCK_TOOLS 改为 useTools 动态加载。deprecation：MOCK_TOOLS 从 agent.ts 移除导入。 |
| **完成标准** | Agent 创建时工具列表来自 API |
| **依赖任务** | TL-T4.2 |

---

## Feature 5: 测试

> 对应 Story: 所有 P0 Story

### Task 5.1: 后端工具 API 测试

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T5.1 |
| **story_id** | US-TL-01 / US-TL-02 / US-TL-03 |
| **文件** | `backend/tests/test_tools_api.py` |
| **任务说明** | 测试：list tools、list with filters、create tool success、create duplicate name 409、get tool、update tool、delete tool、toggle tool enable/disable、get tool calls、get tool call not found。 |
| **完成标准** | 10+ 测试全部通过 |
| **依赖任务** | TL-T1.4 |

### Task 5.2: 后端工具执行引擎测试

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T5.2 |
| **story_id** | US-TL-04 / US-TL-06 |
| **文件** | `backend/tests/test_tool_service.py` |
| **任务说明** | 测试：file_read 成功/路径不存在、file_search 匹配/无匹配、git_diff 返回结果、test_runner 执行成功/失败、权限校验（allowed 工具可调用、not-allowed 工具被拒绝）。 |
| **完成标准** | 8+ 测试全部通过 |
| **依赖任务** | TL-T2.1 |

### Task 5.3: 前端 ToolManagerPage 测试

| 属性 | 值 |
|------|-----|
| **task_id** | TL-T5.3 |
| **story_id** | US-TL-01 / US-TL-03 |
| **文件** | `frontend/src/components/__tests__/ToolManagerPage.test.tsx` |
| **任务说明** | 测试：页面渲染、列表展示、筛选、空状态、加载状态、错误状态、创建工具、删除确认。 |
| **完成标准** | 7+ 测试全部通过 |
| **依赖任务** | TL-T4.3 |
