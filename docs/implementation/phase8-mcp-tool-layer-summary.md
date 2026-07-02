# Phase 8: MCP Tool Layer MVP — 实施总结

> 完成日期：2026-07-02

## 1. 完成内容

### Tool Registry 后端

- `backend/migrations/009_create_tools.sql` — tool_definitions + tool_call_records 表
- `backend/src/models/tool.py` — `ToolDefinition`, `ToolCallRecord` ORM 模型
- `backend/src/schemas/tool.py` — Pydantic schemas（ToolCreate, ToolUpdate, ToolOut, ToolCallRecordOut）
- `backend/src/routes/tools.py` — 8 个 API 端点（CRUD + toggle + calls 查询）
- `backend/src/services/tool_service.py` — Tool Registry CRUD + 4 个内置工具执行器 + 权限校验

### 4 个内置工具

| 工具 | 功能 |
|------|------|
| file_read | 读取文件内容 |
| file_search | glob 模式搜索文件 |
| git_diff | git diff 工作树变更 |
| test_runner | subprocess 执行测试命令 |

### Runtime 工具调用循环

- `backend/src/services/providers/base.py` — `ModelResponse` 增加 `tool_calls` 字段
- `backend/src/services/providers/mock_provider.py` — 支持模拟 `tool_calls` 响应
- `backend/src/services/runtime_service.py` — `_execute_single_task` 集成工具调用循环
- `backend/src/main.py` — 注册 tools router + 启动时 seed 内置工具

### 前端

- `frontend/src/types/tool.ts` — TypeScript 类型定义
- `frontend/src/api/tools.ts` — API 客户端（8 个函数）
- `frontend/src/hooks/useTools.ts` — 8 个 TanStack Query hooks
- `frontend/src/pages/ToolManagerPage.tsx` — 工具管理页面（列表/筛选/添加/编辑/删除/启用禁用）
- `frontend/src/components/AgentConfigForm.tsx` — 工具权限从 MOCK_TOOLS 改为 useTools 动态加载
- `frontend/src/components/TaskDetailPanel.tsx` — Task 详情展示工具调用记录
- `frontend/src/App.tsx` — 新增 `/tools` 路由和导航

### 测试

- `backend/tests/test_tools_api.py` — 17 个 API 测试
- `frontend/src/components/__tests__/TaskDetailPanel.test.tsx` — 添加 QueryClientProvider

## 2. 最终测试结果

```text
Backend: 204 passed (新增 17 工具 API 测试)
Frontend: 143 passed
Total: 347 passed
Status: 零回归
Build: 通过
```

## 3. 验收标准达成

1. ✅ `GET /tools` 返回内置工具列表
2. ✅ `POST /tools` 可注册新工具
3. ✅ Runtime 工具调用循环端到端可运行（Mock 支持 tool_calls）
4. ✅ 工具调用受 `Agent.allowed_tools` 权限控制
5. ✅ 每次工具调用产生 `tool_call` 类型日志
6. ✅ 前端 `/tools` 页面可查看、管理工具
7. ✅ Workspace Task 详情面板展示工具调用记录

## 4. 文件清单

| 类别 | 新增 | 修改 |
|------|------|------|
| 后端 | migrations/009, models/tool.py, schemas/tool.py, routes/tools.py, services/tool_service.py, tests/test_tools_api.py | providers/base.py, providers/mock_provider.py, runtime_service.py, main.py |
| 前端 | types/tool.ts, api/tools.ts, hooks/useTools.ts, pages/ToolManagerPage.tsx | App.tsx, AgentConfigForm.tsx, TaskDetailPanel.tsx, TaskDetailPanel.test.tsx |
| 文档 | docs/prd/mcp-tool-layer-prd.md, docs/stories/mcp-tool-layer-stories.md, docs/tasks/mcp-tool-layer-tasks.md, docs/ui/mcp-tool-layer-ui-spec.md | - |
