# Agent Registry 第 6 轮修复报告

> 修复日期：2026-06-27
> 依据：`docs/dev/agent-registry-audit-report.md`

---

## 修复清单

### P1 — 必须修复（3 项，全部完成）

| # | 问题 | 修复方式 | 修改文件 |
|---|------|----------|----------|
| 1 | AgentTemplateCards 缺少单元测试 | 新增测试文件，覆盖 6 模板渲染、自定义卡片、点击事件、元数据展示 | `frontend/src/components/__tests__/AgentTemplateCards.test.tsx` |
| 2 | AgentConfigForm 编辑 running Agent 时无警告横幅 | 添加 `agent?.status === 'running'` 条件渲染 amber 警告横幅 | `frontend/src/components/AgentConfigForm.tsx` |
| 3 | AgentConfigForm 提交按钮未在表单无效时禁用 | 新增 `isFormValid` 派生状态，按钮在 name/role/default_model_id 任一为空时禁用 | `frontend/src/components/AgentConfigForm.tsx` |

### P2 — 应该修复（4 项，全部完成）

| # | 问题 | 修复方式 | 修改文件 |
|---|------|----------|----------|
| 4 | AgentConfigForm 提交失败后无 API 错误展示 | 新增 `error` prop + `apiError` 状态，支持父组件传入错误并渲染红色横幅 | `frontend/src/components/AgentConfigForm.tsx`, `frontend/src/pages/AgentRegistryPage.tsx` |
| 5 | AgentStatusToggle mutation 失败无回弹处理 | 为 `mutate` 添加 `onError` 回调，确认框在错误时自动关闭 | `frontend/src/components/AgentStatusToggle.tsx` |
| 6 | 缺少 Toast 提示 | **延后处理** — 当前无 Toast 基础设施，属于 UI polish，不影响核心功能验收 |
| 7 | Backend 未校验 role 合法性 | 在 `create_agent` 中增加 `VALID_ROLES` 集合校验，非法 role 返回 400 | `backend/src/services/agent_service.py` |

---

## 测试更新

### 新增测试
- `AgentTemplateCards.test.tsx`：5 个测试（渲染 6 卡片、自定义卡片、点击选择、点击自定义、元数据展示）

### 更新测试
- `AgentConfigForm.test.tsx`：
  - 将 "shows validation error when name is empty" 改为 "disables submit button when name is empty"
  - 将 "shows validation error when default_model_id is empty" 改为 "disables submit button when default_model_id is empty"
  - 新增 "enables submit button when form is valid"
  - 新增 running Agent 警告横幅测试（2 个）
  - 新增 API error 展示测试（2 个）

### 后端测试
- `test_agents_api.py`：新增 `test_create_agent_invalid_role`

---

## 测试结果

| 测试套件 | 数量 | 结果 |
|----------|------|------|
| 后端 API 测试 | 22 | ✅ 全部通过 |
| 前端组件测试 | 28 | ✅ 全部通过 |

---

## 未修复项说明

| 问题 | 原因 | 决策 |
|------|------|------|
| Toast 提示 | 无 Toast 基础设施，需额外引入或自建 | P2 中最低优先级，不影响核心验收，延后到 MVP-B |
| default_model_id 硬校验 | Model Router 模块未就绪 | 符合 implementation plan 风险应对，保持软校验 |
| 筛选无结果时"清除筛选"按钮 | 与空列表共用状态，体验影响小 | P3，延后处理 |
