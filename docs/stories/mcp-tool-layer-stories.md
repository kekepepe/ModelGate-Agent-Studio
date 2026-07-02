# MCP Tool Layer 用户故事

> 基于 `docs/prd/mcp-tool-layer-prd.md`
> P0: 6 条 | P1: 3 条（延后）

---

## Epic: MCP Tool Layer MVP

**目标：** Agent 能够在 Runtime 中调用工具（file_read, file_search, git_diff, test_runner）完成任务，工具调用过程可观测。

**Epic 验收标准：**
1. 4 个内置工具可在 Tool Registry 中查看和管理
2. Runtime 执行时，Agent 可通过工具调用循环完成文件操作、搜索、diff 查看和测试执行
3. 工具调用全过程写入日志，Workspace 中可查看
4. Agent.allowed_tools 控制权限，不在列表中的工具不可调用

---

## US-TL-01：查看工具注册表（P0）

**As** 平台管理员
**I want** 在 Tool Manager 页面查看所有已注册工具
**So that** 了解平台提供了哪些可调用工具

**验收标准：**
1. Tool Manager 页面以表格展示所有工具
2. 每个工具显示：name、display_name、category、risk_level、is_enabled 状态
3. 支持按 category 和 risk_level 筛选
4. 空状态：无工具时显示引导文字
5. 加载状态：骨架屏
6. 失败状态：错误提示 + 重试按钮

---

## US-TL-02：注册新工具定义（P0）

**As** 平台管理员
**I want** 通过 API 注册新工具定义
**So that** 扩展 Agent 的工具能力范围

**验收标准：**
1. `POST /tools` 接收 tool 定义（name, display_name, description, category, risk_level, parameters）
2. name 必须唯一，重复返回 409
3. parameters 必须为合法 JSON Schema 格式
4. 注册后 `GET /tools` 立即可见

---

## US-TL-03：更新/删除/启用禁用工具（P0）

**As** 平台管理员
**I want** 修改、删除或切换工具的启用状态
**So that** 动态管理工具注册表

**验收标准：**
1. `PUT /tools/{id}` 更新工具定义（显示名、描述、分类、风险级别、参数）
2. `DELETE /tools/{id}` 删除工具（软删除或硬删除，MVP 为硬删除）
3. `PATCH /tools/{id}/toggle` 切换 is_enabled
4. 已禁用的工具在 Runtime 中不可调用

---

## US-TL-04：Runtime 中调用工具（P0）

**As** 开发者用户
**I want** Agent 在执行任务时能够调用工具（如读取文件、搜索代码）
**So that** Agent 能够感知和操作项目环境

**验收标准：**
1. Agent 的任务描述包含工具调用需求时，模型返回 tool_calls 能被 runtime_service 捕获
2. tool_calls 中的 tool_name 必须在 Agent.allowed_tools 中，否则跳过
3. tool_name 对应的工具在 ToolRegistry 中且 is_enabled=true
4. 工具调用结果（输出/错误）追加到对话上下文，继续调用模型
5. 工具调用循环最多执行 max_tool_calls_per_task 次（默认 20）

---

## US-TL-05：查看工具调用记录（P0）

**As** 开发者用户
**I want** 在 Workspace 中查看 Agent 的工具调用历史
**So that** 了解 Agent 使用了哪些工具及其结果

**验收标准：**
1. Task 详情面板展示该 Task 的所有 tool_call 记录
2. 每条记录显示：tool_name、状态（started/completed/failed）、耗时、输入参数摘要、输出截断（前200字符）
3. 可选查看完整输入/输出
4. 空状态：无工具调用时隐藏此区域
5. 按时间轴排列

---

## US-TL-06：工具权限在 Runtime 中生效（P0）

**As** 系统架构师
**I want** Agent 只能调用其 allowed_tools 列表中的工具
**So that** 防止越权调用高风险工具

**验收标准：**
1. Runtime 在执行 tool_call 前校验 tool_name ∈ agent.allowed_tools
2. 不在列表中的工具调用被拒绝，写入 error 日志
3. Agent 配置中的 allowed_tools 来自 Tool Registry（非硬编码字符串）
4. 高风险工具（test_runner）需显式授权

---

## US-TL-07：通过 MCP 协议连接外部工具（P1 - 延后）

**As** 开发者用户
**I want** 连接外部 MCP Server
**So that** 使用第三方提供的工具能力

**验收标准（延后）：**
1. 配置 MCP Server 地址后，自动发现其提供的工具
2. 外部工具和内置工具在统一注册表中管理
3. 外部工具调用遵循相同权限和日志机制

---

## US-TL-08：工具调用超时和重试（P1 - 延后）

**As** 开发者用户
**I want** 工具调用支持超时和自动重试
**So that** 长时间运行的工具不会阻塞整个任务流程

**验收标准（延后）：**
1. 各工具可配置 timeout（默认 30s）
2. 超时后自动标记失败
3. 支持配置重试次数

---

## US-TL-09：file_write 和 terminal_execute 工具（P1 - 延后）

**As** 开发者用户
**I want** Agent 能够写入文件和执行终端命令
**So that** 完成更复杂的开发任务

**验收标准（延后）：**
1. file_write: 写入文件内容，支持创建新文件和覆写
2. terminal_execute: 执行终端命令并返回输出
3. 高风险工具需要额外的确认步骤
