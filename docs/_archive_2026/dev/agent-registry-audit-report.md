# Agent Registry 第 5 轮自查报告

> 检查日期：2026-06-27
> 检查依据：`docs/prd/agent-registry-prd.md`、`docs/stories/agent-registry-stories.md`、`docs/tasks/agent-registry-tasks.md`、`docs/ui/agent-registry-ui-spec.md`、`docs/dev/agent-registry-implementation-plan.md`

---

## 一、P0 Story 完成情况

| Story | 状态 | 偏差说明 |
|-------|------|----------|
| US-AR-01 查看列表 | ✅ 完成 | 列表、搜索、筛选、排序、点击编辑均实现 |
| US-AR-02 创建 Agent | ⚠️ 基本完成 | 核心流程完成，但提交按钮未在表单无效时禁用；无 toast 提示；无 API 错误展示 |
| US-AR-03 编辑配置 | ⚠️ 基本完成 | 核心流程完成，但 running Agent 编辑时无警告横幅；无 toast 提示；无 API 错误展示 |
| US-AR-04 启用/禁用 | ⚠️ 基本完成 | 核心流程完成，但 mutation 失败时 Switch 无回弹处理 |
| US-AR-05 模板创建 | ✅ 完成 | 6 模板卡片、预填、创建、刷新均实现 |

**结论：5 个 P0 Story 核心功能均已实现，存在 4 项 UI/交互 polish 类偏差，不影响主流程。**

---

## 二、P0 Task 完成情况

| Task | 状态 | 偏差说明 |
|------|------|----------|
| AG-T1.1 agent_stations 表 | ✅ 完成 | 字段、索引、约束均正确 |
| AG-T1.2 枚举与校验 | ⚠️ 基本完成 | name/max_steps 校验已覆盖；**role 合法性校验缺失** |
| AG-T2.1 GET /agents | ✅ 完成 | 筛选、搜索、排序、分页均实现 |
| AG-T2.2 POST /agents | ⚠️ 基本完成 | 必填校验、template_id 均实现；**model_id 硬校验缺失**（已知风险） |
| AG-T2.3 PATCH /agents/:id | ⚠️ 基本完成 | 部分更新实现；**model_id 硬校验缺失** |
| AG-T2.4 PATCH /agents/:id/status | ✅ 完成 | 启用/禁用、404 处理均实现 |
| AG-T3.1 模板数据 + API | ✅ 完成 | 6 模板、接口、测试均覆盖 |
| AG-T3.2 模板创建集成 | ✅ 完成 | template_id 预填充、覆盖、非法值处理均实现 |
| AG-T4.1 页面框架 + 列表 | ✅ 完成 | 路由、列表、筛选、空状态均实现 |
| AG-T4.2 对接真实 API | ✅ 完成 | loading、error、empty 状态均实现 |
| AG-T4.3 创建/编辑表单 | ⚠️ 基本完成 | 字段完整、校验实现；**提交按钮未按校验状态禁用**；**无 API 错误展示** |
| AG-T4.4 启用/禁用开关 | ⚠️ 基本完成 | Switch、确认框、变灰均实现；**mutation 失败无回弹** |
| AG-T4.5 模板创建 UI | ✅ 完成 | 卡片、预填、创建、刷新均实现 |
| AG-T6.1 后端测试 | ✅ 完成 | 21 个测试覆盖全部 API 的 happy path 和主要错误 path |
| AG-T6.2 前端组件测试 | ⚠️ 基本完成 | AgentList/AgentConfigForm/AgentStatusToggle 已测试；**AgentTemplateCards 缺少测试** |

**结论：15 个 P0 Task 中 10 个完全完成，5 个基本完成（偏差均为 UI polish 或已知风险范围内的校验缺失）。**

---

## 三、字段一致性检查

前后端 AgentStation 字段完全一致，无缺失字段：

| 字段 | PRD | 后端 Model | 后端 Schema | 前端 Type | 一致 |
|------|-----|------------|-------------|-----------|------|
| id ~ updated_at | ✅ | ✅ | ✅ | ✅ | 全部一致 |

**注意项：**
- PRD 中 `description` 标记为 `string`（非可选），但前后端 schema 均按 `Optional` 处理。实际功能无影响。
- PRD 中 `status` 枚举包含 `disabled`，但实现中 `disabled` 由前端根据 `is_enabled=false` 合成展示，后端 status 字段本身不被设为 `disabled`。这是设计选择，功能等价。

---

## 四、API 路径一致性

| 接口 | PRD | 后端 Route | 前端调用 | 一致 |
|------|-----|------------|----------|------|
| GET /agents | ✅ | ✅ | ✅ | ✅ |
| GET /agents/:id | ✅ | ✅ | ✅ | ✅ |
| POST /agents | ✅ | ✅ | ✅ | ✅ |
| PATCH /agents/:id | ✅ | ✅ | ✅ | ✅ |
| PATCH /agents/:id/status | ✅ | ✅ | ✅ | ✅ |
| GET /agents/templates | ✅ | ✅ | ✅ | ✅ |

**全部一致。**

---

## 五、Status 枚举一致性

| 值 | PRD | 后端 | 前端 STATUS_CONFIG | 一致 |
|----|-----|------|-------------------|------|
| idle | ✅ | ✅ | ✅ | ✅ |
| running | ✅ | ✅ | ✅ | ✅ |
| handoff | ✅ | ✅ | ✅ | ✅ |
| blocked | ✅ | ✅ | ✅ | ✅ |
| error | ✅ | ✅ | ✅ | ✅ |
| disabled | ✅ | 前端合成 | ✅ | ⚠️ 语义等价 |

---

## 六、空状态 / 加载状态 / 错误状态

| 场景 | 状态 |
|------|------|
| 列表空状态 | ✅ AgentList 有完整空状态（图标 + 文案） |
| 列表加载 | ✅ AgentRegistryPage 有 spinner |
| 列表错误 | ✅ AgentRegistryPage 有错误横幅 + 重试按钮 |
| 表单提交中 | ✅ 按钮显示 "保存中..." 并禁用 |
| 表单提交错误 | ❌ **无 API 错误展示**（模态框不关闭但无错误横幅） |
| 筛选无结果 | ❌ **未单独处理**（与空列表共用同一空状态，无"清除筛选"按钮） |

---

## 七、Mock 数据检查

| Mock 数据 | 位置 | 是否标注 | 说明 |
|-----------|------|----------|------|
| MOCK_MODELS | `frontend/src/types/agent.ts` | ✅ 变量名含 MOCK | 因 Model Router 未就绪，符合计划 |
| MOCK_TOOLS | `frontend/src/types/agent.ts` | ✅ 变量名含 MOCK | 因 MCP 模块未就绪，符合计划 |
| 模板数据 | `backend/src/data/agent_templates.py` | ✅ 代码注释说明 | MVP 无需数据库表，符合计划 |

**无未标注 mock 混入正式逻辑。**

---

## 八、测试覆盖检查

### 后端：21 个测试

| 测试类 | 数量 | 覆盖 |
|--------|------|------|
| TestListAgents | 5 | 空列表、有数据、role 筛选、status 筛选、search |
| TestCreateAgent | 6 | 成功、缺 name、缺 role+model、缺 model、模板创建、非法模板 |
| TestGetAgent | 2 | 成功、404 |
| TestUpdateAgent | 4 | 更新 name、404、非法 max_steps、部分更新 |
| TestUpdateAgentStatus | 3 | 禁用、启用、404 |
| TestListTemplates | 1 | 返回 6 个模板 |

**全部 21 个测试通过（Round 4 已验证）。**

### 前端：17 个测试（文档记录 18，实际 17）

| 测试文件 | 数量 | 覆盖 |
|----------|------|------|
| AgentList.test.tsx | 6 | 空状态、渲染、角色标签、状态灯、点击事件、禁用样式 |
| AgentConfigForm.test.tsx | 7 | 创建表单、校验(name/model)、保存、取消、编辑预填、更新、Handoff 开关 |
| AgentStatusToggle.test.tsx | 4 | 启用状态、禁用状态、确认弹窗、取消弹窗 |

**缺失：AgentTemplateCards.test.tsx**（AG-T6.2 明确要求覆盖，但未实现）

---

## 九、问题清单（按修复优先级排序）

### P1 — 必须修复（影响验收标准）

| # | 问题 | 来源 | 影响 |
|---|------|------|------|
| 1 | **AgentTemplateCards 缺少单元测试** | AG-T6.2 | 前端测试覆盖不完整 |
| 2 | **AgentConfigForm 编辑 running Agent 时无警告横幅** | US-AR-03 AC-2 | running 状态编辑缺少用户提示 |
| 3 | **AgentConfigForm 提交按钮未在表单无效时禁用** | US-AR-02 AC-3 | 用户可点击创建/保存即使必填项为空 |

### P2 — 应该修复（影响体验）

| # | 问题 | 来源 | 影响 |
|---|------|------|------|
| 4 | **AgentConfigForm 提交失败后无 API 错误展示** | US-AR-02/03 AC | 用户不知道保存为何失败 |
| 5 | **AgentStatusToggle mutation 失败无回弹处理** | AG-T4.4 AC-5 | API 失败时 Switch 可能显示错误状态 |
| 6 | **缺少 Toast 提示（创建/编辑成功）** | US-AR-02/03 AC | 用户无成功反馈 |
| 7 | **Backend 未校验 role 合法性** | AG-T1.2 AC | 可传入非法 role 值 |

### P3 — 可选修复（已知风险/设计选择）

| # | 问题 | 来源 | 影响 |
|---|------|------|------|
| 8 | default_model_id 硬校验缺失 | AG-T2.2/2.3 AC | Model Router 未就绪，符合计划风险应对 |
| 9 | 筛选无结果时未显示"清除筛选"按钮 | UI Spec 7.1 | 与空列表共用状态，体验稍差 |

---

## 十、总体评估

| 维度 | 评分 | 说明 |
|------|------|------|
| 功能完整性 | 90% | 5 个 P0 Story 核心流程全部跑通，缺失主要是 toast、错误展示、警告横幅等 polish |
| 字段一致性 | 98% | 前后端字段完全对齐，仅 description 可选性有细微差异 |
| API 一致性 | 100% | 6 个接口路径、请求/响应格式均对齐 PRD |
| 状态覆盖 | 80% | 列表的 loading/error/empty 齐全；表单缺少 API 错误状态 |
| 测试覆盖 | 85% | 后端 21 测试完整；前端缺 AgentTemplateCards 测试 |
| Mock 标注 | 100% | 所有 mock 均已明确标注 |

**结论：Agent Registry MVP 实现质量良好，核心功能完整。建议在第 6 轮优先修复 P1 问题（3 项），视时间处理 P2 问题（4 项）。P3 问题可延后。**
