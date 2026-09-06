# Logs / Observability Implementation Plan

> 生成日期：2026-06-30
> 依据：docs/prd/logs-observability-prd.md、docs/stories/logs-observability-stories.md、docs/tasks/logs-observability-tasks.md、docs/ui/logs-observability-ui-spec.md
> 开发标准：docs/dev/module-development-sop.md

---

## 1. 范围声明

### P0（MVP-A，本轮必须完成）

| Story | 说明 | 覆盖 Task |
|-------|------|-----------|
| US-LO-01 | 查看实时执行日志 | LO-T1.1 / LO-T1.2 / LO-T2.1 / LO-T4.1 / LO-T4.2 |
| US-LO-02 | 筛选特定类型日志 | LO-T1.1 / LO-T2.1 / LO-T4.2 |
| US-LO-03 | 查看单条日志详情 | LO-T1.1 / LO-T2.2 / LO-T5.1 |
| US-LO-04 | 查看 Task 完整执行时间线 | LO-T1.1 / LO-T3.1 / LO-T6.1 / LO-T6.2 |
| US-LO-05 | 查看错误日志定位失败原因 | LO-T1.2 / LO-T2.1 / LO-T4.1 / LO-T4.3 |

### P1（MVP-B，本轮标记为预留，不实现 UI）

| Story | 说明 | 覆盖 Task |
|-------|------|-----------|
| US-LO-06 | 查看 Token 使用统计 | LO-T7.1 / LO-T7.2 — 仅后端聚合 API 预留接口，前端柱状图延后 |

### 明确不做

- Workspace 底部实时 ExecutionLogPanel（LO-T4.1/4.2/4.3 中的 Workspace 场景）—— 当前项目尚无 Workspace 页面（Module 6），Logs Page 独立路由 `/logs` 先承载全部日志查看需求。
- Memory / Skill Evolution 相关日志自动触发 —— 依赖 Module 6，当前只做数据模型预留。
- 日志自动清理/归档策略 —— 超出 MVP-A 范围。
- SSE/WebSocket 实时推送 —— 先以轮询实现，后续升级。

---

## 2. 当前项目状态分析

### 已有基础

| 文件 | 当前状态 | 处理方式 |
|------|----------|----------|
| `backend/src/models/handoff.py` | 存在极简 `ExecutionLog` 模型（9 个字段） | 扩展模型字段，保留向后兼容 |
| `backend/migrations/004_create_handoff_records.sql` | 已创建 `execution_logs` 表（9 列） | 新建 `005_expand_execution_logs.sql` 迁移 |
| `backend/src/schemas/handoff.py` | 存在极简 `ExecutionLogResponse` | 新建 `backend/src/schemas/log.py` 提供完整 Schema |
| `backend/src/services/handoff_service.py` | `_create_log()` 写极简日志 | 更新为写入新扩展字段 |
| `backend/src/routes/handoffs.py` | `GET /logs` 仅支持 `handoff_id` 过滤 | 新建 `backend/src/routes/logs.py` 提供完整 Logs API |
| `frontend/src/App.tsx` | 无 `/logs` 路由 | 新增路由和导航链接 |

### 前端现状

- 无任何日志相关类型、API、Hook、组件、页面。
- 需要从零搭建 Logs 模块前端。

---

## 3. 文件变更清单

### 3.1 新增文件

#### 后端

| 文件 | 说明 |
|------|------|
| `backend/migrations/005_expand_execution_logs.sql` | 删除旧 execution_logs 表，重建完整字段表 + 索引 |
| `backend/src/schemas/log.py` | LogEventType / LogEventStatus 枚举、ExecutionLog schema、list/detail/response schemas |
| `backend/src/services/log_service.py` | create_log、list_logs、get_log、get_task_timeline、聚合预留接口 |
| `backend/src/routes/logs.py` | `GET /logs`、`GET /logs/{log_id}`、`GET /logs/task/{task_id}/timeline` |

#### 前端

| 文件 | 说明 |
|------|------|
| `frontend/src/types/log.ts` | ExecutionLog 接口、LogEventType、LogEventStatus、LogFilters、TimelineEvent、分页响应 |
| `frontend/src/api/logs.ts` | getLogs、getLog、getTaskTimeline — Axios 封装 |
| `frontend/src/hooks/useLogs.ts` | useLogsQuery、useLogDetailQuery、useTaskTimelineQuery — TanStack Query hooks |
| `frontend/src/pages/LogsPage.tsx` | Logs 列表页面（含筛选、分页、详情抽屉） |
| `frontend/src/components/LogListItem.tsx` | 单条日志行组件（图标、摘要、状态色） |
| `frontend/src/components/LogDetailDrawer.tsx` | 日志详情抽屉（右侧滑出） |
| `frontend/src/components/LogFilters.tsx` | 筛选栏（event_type、event_status、时间范围、搜索） |
| `frontend/src/components/TaskTimeline.tsx` | Task 时间线组件（垂直节点 + 统计栏） |
| `frontend/src/components/__tests__/LogListItem.test.tsx` | 日志行组件测试 |
| `frontend/src/components/__tests__/LogDetailDrawer.test.tsx` | 详情抽屉测试 |
| `frontend/src/components/__tests__/LogFilters.test.tsx` | 筛选栏测试 |
| `frontend/src/components/__tests__/TaskTimeline.test.tsx` | 时间线组件测试 |

#### 测试

| 文件 | 说明 |
|------|------|
| `backend/tests/test_log_api.py` | Logs API 集成测试（列表、详情、时间线） |
| `backend/tests/test_log_service.py` | Log Service 单元测试 |

### 3.2 修改文件

| 文件 | 修改内容 |
|------|----------|
| `backend/src/models/handoff.py` | 扩展 `ExecutionLog` 模型字段：event_type、event_status、input_summary、output_summary、token_usage(Text/JSON)、latency_ms、metadata(Text/JSON)、routing_info(Text/JSON)、error_type、error_code、tool_name、quota_status、handoff_status |
| `backend/src/services/handoff_service.py` | 更新 `_create_log()` 调用，传入 `event_type`、`event_status` 等新字段；替换 `level/action` 为 `event_type/event_status` 语义 |
| `backend/src/main.py` | `include_router(logs.router, prefix=settings.api_v1_prefix)` |
| `frontend/src/App.tsx` | 添加 `/logs` 路由和导航栏链接 |

---

## 4. 数据结构变更

### ExecutionLog 模型扩展（backend/src/models/handoff.py）

```python
class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String(36), nullable=True, index=True)
    task_id = Column(String(36), nullable=True, index=True)
    agent_id = Column(String(36), nullable=True, index=True)
    worker_id = Column(String(36), nullable=True)
    model_id = Column(String(100), nullable=True, index=True)
    handoff_id = Column(String(36), nullable=True, index=True)

    # 新字段：替换 level/action 语义
    event_type = Column(String(50), nullable=False, index=True)
    event_status = Column(String(50), nullable=False, index=True)

    # 内容摘要
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)

    # Token 消耗（JSON）
    token_usage = Column(Text, nullable=True)  # {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    # 性能
    latency_ms = Column(Integer, nullable=True)

    # 错误信息
    error_type = Column(String(50), nullable=True)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    # 工具信息
    tool_name = Column(String(100), nullable=True)

    # 状态快照
    quota_status = Column(String(50), nullable=True)
    handoff_status = Column(String(50), nullable=True)

    # 扩展元数据（JSON）
    metadata = Column(Text, nullable=True)
    routing_info = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
```

**兼容性说明：**
- `level` / `action` 两个旧字段被 `event_type` / `event_status` 替代。由于当前没有生产数据，直接删除旧列重建表。
- `handoff_service.py` 中的 `_create_log` 调用方全部更新。

### 迁移脚本（005_expand_execution_logs.sql）

SQLite 不支持完整的 `ALTER TABLE DROP COLUMN`，策略：
1. `DROP TABLE IF EXISTS execution_logs`
2. `CREATE TABLE execution_logs (...)` 完整新表结构
3. 重建全部索引

> 风险：会丢失已有日志数据。当前 execution_logs 仅由 Handoff Manager 内部生成，且数据量极小，可接受。将在风险章节标注。

---

## 5. API 设计

### 5.1 GET /logs

- 查询参数：`goal_id`、`task_id`、`agent_id`、`model_id`、`event_type`（逗号分隔多值）、`event_status`（逗号分隔多值）、`start_time`、`end_time`、`search`、`page`、`page_size`
- 响应：`{ items: ExecutionLog[], total: number, page: number, page_size: number, total_pages: number }`

### 5.2 GET /logs/{log_id}

- 响应：完整 `ExecutionLog` 对象 + 关联 Agent/Goal/Task 名称（减少前端多次请求）

### 5.3 GET /logs/task/{task_id}/timeline

- 响应：`{ events: TimelineEvent[], summary: { total_duration_ms, total_tokens, model_call_count, handoff_count, error_count } }`

### 5.4 POST /logs（内部写入接口）

- 请求体：`ExecutionLogCreate` schema
- 响应：`{ log_id: string }`
- 说明：供 Handoff Service / 其他模块内部调用，不直接暴露给前端

---

## 6. 开发顺序

### Phase 1 — 数据模型 + 后端 API（Round 2）

1. **Migration**: `005_expand_execution_logs.sql` — 重建表结构
2. **Model**: 扩展 `backend/src/models/handoff.py` 的 `ExecutionLog`
3. **Schema**: 新建 `backend/src/schemas/log.py`
4. **Service**: 新建 `backend/src/services/log_service.py`（create_log、list_logs、get_log、timeline）
5. **Routes**: 新建 `backend/src/routes/logs.py`
6. **Update handoff_service.py**: 更新 `_create_log` 使用新字段
7. **Update main.py**: 注册 logs router
8. **Backend Tests**: `test_log_api.py` + `test_log_service.py`

### Phase 2 — 前端基础（Round 3）

1. **Types**: `frontend/src/types/log.ts`
2. **API**: `frontend/src/api/logs.ts`
3. **Hooks**: `frontend/src/hooks/useLogs.ts`
4. **Components**:
   - `LogFilters.tsx` — 筛选栏
   - `LogListItem.tsx` — 日志行
   - `LogDetailDrawer.tsx` — 详情抽屉
   - `TaskTimeline.tsx` — 时间线
5. **Page**: `frontend/src/pages/LogsPage.tsx` — 整合列表 + 筛选 + 抽屉 + 时间线
6. **Update App.tsx**: 添加 `/logs` 路由和导航

### Phase 3 — 测试补全（Round 4）

1. **Backend**: 补充 API 边界测试（空列表、404、筛选组合、时间线统计）
2. **Frontend**: 组件渲染测试、交互测试（筛选点击、抽屉打开、时间线节点）
3. **Type Check**: `npx tsc -b --noEmit`
4. **Build**: `npm run build`

---

## 7. Mock / 真实接口依赖

| 依赖项 | 状态 | 策略 |
|--------|------|------|
| Agent 名称（日志列表显示 agent_name） | 真实 — `agents` 表已存在 | 后端 `JOIN` 查询或前端二次查询 |
| Goal 名称 | 无 Goal 模块表 | 后端仅返回 `goal_id`，前端显示 ID 前 8 位 + "Goal" 前缀 |
| Task 标题 | 真实 — `handoff_tasks` 表已存在 | 后端 `JOIN` `handoff_tasks` 表获取 `title` |
| Model 名称 | 真实 — `models` 表已存在 | 后端 `JOIN` 查询 |
| Workspace 页面 | 不存在（Module 6） | LogsPage 独立承载全部功能，不等待 Workspace |
| 实时日志写入来源 | Handoff Service 可写入 | 其他模块（Runtime、Quota）尚未就绪，Handoff 事件作为真实日志来源 |

---

## 8. 风险点与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| Migration 005 删除旧表丢失数据 | 极低 — 当前仅 Handoff Service 生成少量内部日志 | 接受；在迁移脚本中显式 `DROP TABLE` 并注释说明 |
| `handoff_service.py` 中 `_create_log` 调用点多 | 中等 — 需全部更新字段映射 | 逐一检查，使用 `event_type`/`event_status` 替代 `level`/`action` |
| 前端无现有日志数据导致页面空旷 | 中 — UI 验收困难 | Handoff Service 持续产生日志；同时提供 demo/log seeder API 或 mock 数据 |
| Task Timeline 需要 task 列表数据源 | 中 — 当前无 Task 管理页面 | LogsPage 左侧用 `handoff_tasks` 表作为 Task 列表来源（Module 4 已创建） |
| Token 统计聚合查询在大数据量下慢 | 低 — MVP 数据量小 | P1 功能延后；如需要，后续加 SQLite 索引或内存缓存 |
| event_type / event_status 枚举前后端不一致 | 中 — 类型安全风险 | 统一在 `frontend/src/types/log.ts` 和 `backend/src/schemas/log.py` 中硬编码枚举，并在测试中校验完整性 |

---

## 9. P0 Story → 文件映射

| Story | 关键文件 |
|-------|----------|
| US-LO-01 查看实时执行日志 | `backend/src/services/log_service.py` (list_logs)、`frontend/src/pages/LogsPage.tsx`、`frontend/src/api/logs.ts`、`frontend/src/hooks/useLogs.ts` |
| US-LO-02 筛选特定类型日志 | `backend/src/routes/logs.py` (GET /logs 筛选参数)、`frontend/src/components/LogFilters.tsx` |
| US-LO-03 查看单条日志详情 | `backend/src/routes/logs.py` (GET /logs/{id})、`frontend/src/components/LogDetailDrawer.tsx` |
| US-LO-04 查看 Task 时间线 | `backend/src/routes/logs.py` (GET /logs/task/{id}/timeline)、`frontend/src/components/TaskTimeline.tsx` |
| US-LO-05 查看错误日志 | `frontend/src/components/LogListItem.tsx` (错误状态红色高亮)、`frontend/src/components/LogFilters.tsx` ("仅错误" 快速筛选) |

---

## 10. 验收检查单（Round 5 审计用）

- [ ] `GET /logs` 返回分页结果，含 `total_pages`
- [ ] `GET /logs` 支持 `event_type` 多值筛选（逗号分隔）
- [ ] `GET /logs` 支持 `search` 在 input_summary / output_summary / error_message 中模糊匹配
- [ ] `GET /logs/{log_id}` 返回完整字段，包含 token_usage / metadata / routing_info 的 JSON 解析
- [ ] `GET /logs/task/{task_id}/timeline` 返回 events 数组 + summary 统计
- [ ] 日志列表页面 `/logs` 可访问，显示日志行（时间、类型图标、状态色、摘要）
- [ ] 点击日志行打开右侧详情抽屉
- [ ] 筛选栏支持 event_type / event_status / 时间范围 / 搜索
- [ ] "仅错误" 快速筛选按钮工作正常
- [ ] Task Timeline 组件正确渲染垂直节点和统计栏
- [ ] 前端类型检查通过
- [ ] 前端构建通过
- [ ] 后端测试全部通过
- [ ] 前端组件测试全部通过
