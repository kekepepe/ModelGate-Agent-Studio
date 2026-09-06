 

# ModelGate Agent Studio — 后续开发计划 v2

> 最后更新：2026-07-01
> P0/P1 全部完成 ✅

---

## 一、当前状态速览

### 最新测试结果

| 项目           | 测试数量                   |
| -------------- | -------------------------- |
| Backend        | 187 (新增 15 模型管理 API) |
| Frontend       | 143                        |
| **总计** | **330**              |

### 已完成（8 个阶段 + P0/P1）

| Supervisor Review | 完成 | 4 | 0 |
| Memory/Skill 自进化 | 完成 | 4 | 0 |
| Docker Compose | 完成 | - | - |
| **总计** | | **172** | **145** |

### 执行链路

```
Goal → Router → Quota → Worker → Mock/Real Model → Logs → Quota Record
  → Task/Agent Status → Handoff → Supervisor Review → Memory/Skill Drafts
  → Evolution Review Page → Knowledge Base
```

---

## 二、新发现的前端体验问题（高优先级）

### 问题 1：Agent 创建/编辑页面缺少分步向导

**现状：**

- `AgentRegistryPage` 点击"创建 Agent"后弹出模态框，内嵌 `AgentConfigForm`
- 表单为单页长表单，包含：基本信息 → 模型配置 → 工具权限 → 系统 Prompt → 执行限制
- 所有字段堆叠在一个可滚动区域内，用户需要频繁上下滚动
- 没有明确的"上一步 / 下一步"导航，也没有最终确认步骤
- 保存/取消按钮固定在底部，但在长表单场景下用户可能不知道是否已经填完必填项

**影响：**

- 表单字段多（10+ 个），一次展示全部信息，认知负担大
- 必填项（名称、角色、默认模型）和选填项混在一起，容易遗漏
- 没有分步确认，误操作成本高

**建议方案：**
改为 3 步向导：

```
Step 1: 基本信息（名称、角色、描述）
  → 下一步
Step 2: 模型与工具（默认模型、备用模型、工具权限）
  → 上一步 / 下一步
Step 3: 高级配置与确认（System Prompt、输出格式、Handoff 设置）
  → 上一步 / 创建（或保存）
```

每步底部显示进度指示器（Step 1/3），最后一步展示汇总卡片供用户确认。

---

### 问题 2：前端没有模型管理页面

**现状：**

- 后端 `models` 表已有完整 Schema：`id, provider, model_name, display_name, capability_tags, max_context_tokens, cost_level, speed_level, is_enabled, is_default`
- 但后端**没有模型管理 CRUD API**（仅有路由决策 API `/router/select`）
- 前端 `AgentConfigForm` 中模型列表来自硬编码 `MOCK_MODELS`（`frontend/src/types/agent.ts`）
- `ModelRouterPage` 只有"测试路由"功能，没有"添加/编辑/删除/启用禁用模型"的管理能力
- 用户无法在 UI 上配置新模型（如添加自己的 OpenAI API Key 对应的模型）

**影响：**

- 模型配置与代码耦合，添加新模型必须改代码重新部署
- Agent 创建时选择的模型是前端写死的 mock 数据，与后端真实模型数据不同步
- 无法动态调整模型的 cost_level、speed_level、capability_tags 等影响路由决策的关键参数

**建议方案：**

1. **后端**：新增模型管理 CRUD API
   - `GET /models` — 列表（分页、按 provider 筛选）
   - `GET /models/{id}` — 详情
   - `POST /models` — 创建
   - `PUT /models/{id}` — 更新
   - `DELETE /models/{id}` — 删除
   - `PATCH /models/{id}/toggle` — 启用/禁用
2. **前端**：新增 `ModelManagerPage` 页面
   - 模型列表表格（显示 provider、cost、speed、enabled 状态）
   - 添加/编辑模型表单（provider、model_name、display_name、tags、cost_level、speed_level、max_context_tokens）
   - 启用/禁用开关
3. **前端**：`AgentConfigForm` 中的模型下拉框改为调用 `GET /models` 动态加载
4. **前端**：`ModelRouterPage` 增加"模型配置"入口或 Tab

---

## 三、遗留 P1 / P2 任务

### P1-1：Docker Compose CI/CD Pipeline

**现状：** Docker Compose 已可本地一键启动，但缺少 CI 验证

**待完成：**

- GitHub Actions workflow：
  - 每次 push/PR 时自动 `docker-compose build`
  - 运行后端测试容器化版本
  - 运行前端 build 验证
- `docker-compose.prod.yml` 生产版本（非热重载、nginx 静态文件缓存）

### P2-1：MCP / Tool Layer MVP

**现状：** 工具列表硬编码在 `MOCK_TOOLS` 中，没有真实工具调用能力

**待完成：**

- Tool Registry 后端（Tool 定义、权限策略、调用日志）
- File Read / File Search / Git Diff / Test Runner 最小工具集
- Tool Call Log 表与 API
- Agent 工具权限在 Runtime 中实际生效
- Workspace 展示工具调用记录

### P2-2：可视化与统计增强

**现状：** 基础页面已存在，但缺少数据可视化

**待完成：**

- Token 统计聚合面板（按 Goal / Agent / Model 聚合）
- Quota 使用趋势图表（折线图/柱状图）
- Agent 执行成功率统计
- Handoff 前后对比视图
- Usage Trend 图表（有真实调用数据后）
- Router Rules 可视化编辑页面
- 完整像素办公室动画（Agent 小人走动、任务交接动画）

---

## 四、P0/P1 完成状态

|    优先级    | 任务                                 |  状态  |
| :----------: | ------------------------------------ | :-----: |
| **P0** | 模型管理 CRUD（后端 API + 前端页面） | ✅ 完成 |
| **P0** | Agent 创建向导式表单重构             | ✅ 完成 |
| **P0** | AgentConfigForm 动态加载模型列表     | ✅ 完成 |
| **P1** | GitHub Actions CI/CD                 | ✅ 完成 |
| **P2** | MCP Tool Layer MVP                   |  延后  |
| **P2** | 可视化统计增强                       |  延后  |

### 本次交付

| 类别  | 新增文件                                                                                      | 修改文件                                                                                           |
| ----- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| 后端  | `schemas/model.py`, `routes/models.py`, `tests/test_models_api.py`                      | `main.py`                                                                                        |
| 前端  | `types/model.ts`, `api/models.ts`, `hooks/useModels.ts`, `pages/ModelManagerPage.tsx` | `App.tsx`, `components/AgentConfigForm.tsx`, `components/__tests__/AgentConfigForm.test.tsx` |
| CI/CD | `.github/workflows/ci.yml`                                                                  | -                                                                                                  |
| 工程  | `backend/requirements.txt`, `Dockerfile`, `docker-compose.yml` 等                       | -                                                                                                  |

---

## 五、P0 详细任务拆分

### 5.1 模型管理 CRUD

#### 后端

| 文件                                 | 动作 | 说明                                                            |
| ------------------------------------ | ---- | --------------------------------------------------------------- |
| `backend/src/schemas/model.py`     | 新建 | `ModelCreate`, `ModelUpdate`, `ModelOut` Pydantic schemas |
| `backend/src/routes/models.py`     | 新建 | `GET/POST/PUT/DELETE/PATCH` 路由                              |
| `backend/src/main.py`              | 修改 | 注册`models` router                                           |
| `backend/tests/test_models_api.py` | 新建 | 5-6 个 API 测试                                                 |

#### 前端

| 文件                                            | 动作      | 说明                                           |
| ----------------------------------------------- | --------- | ---------------------------------------------- |
| `frontend/src/types/model.ts`                 | 新建/修改 | `Model` interface，移除/替换 `MOCK_MODELS` |
| `frontend/src/api/models.ts`                  | 新建      | Axios CRUD 客户端                              |
| `frontend/src/hooks/useModels.ts`             | 新建      | TanStack Query hooks                           |
| `frontend/src/pages/ModelManagerPage.tsx`     | 新建      | 模型列表 + 添加/编辑/删除                      |
| `frontend/src/App.tsx`                        | 修改      | 添加`/models` 路由                           |
| `frontend/src/components/AgentConfigForm.tsx` | 修改      | 模型下拉框改为调用`useModels`                |

---

### 5.2 Agent 创建向导式表单

#### 前端

| 文件                                             | 动作         | 说明                                  |
| ------------------------------------------------ | ------------ | ------------------------------------- |
| `frontend/src/components/AgentConfigForm.tsx`  | 重写         | 改为 3 步向导 + 进度指示器 + 汇总确认 |
| `frontend/src/components/AgentWizardStep1.tsx` | 新建（可选） | 基本信息步骤（如拆分组件）            |
| `frontend/src/components/AgentWizardStep2.tsx` | 新建（可选） | 模型与工具步骤                        |
| `frontend/src/components/AgentWizardStep3.tsx` | 新建（可选） | 高级配置与确认步骤                    |

#### 建议的 3 步结构

```
Step 1: 基本信息
  - 名称 * (text)
  - 角色 * (select)
  - 描述 (textarea)
  [取消] [下一步 >]

Step 2: 模型与工具
  - 默认模型 * (select, 动态加载)
  - 备用模型 (checkbox group)
  - 工具权限 (checkbox group)
  [< 上一步] [下一步 >]

Step 3: 高级配置与确认
  - 系统 Prompt (textarea)
  - 输出格式 (select)
  - 最大执行步数 (number)
  - 允许 Handoff (toggle)
  - Handoff 阈值 (number, conditional)
  ---
  汇总卡片：
    名称: xxx | 角色: coder
    默认模型: Claude 3 Opus
    备用模型: GPT-4 Turbo, DeepSeek Coder
    工具权限: file_read, diff_view
  [< 上一步] [创建 Agent]
```

---

## 六、验收标准

### 模型管理

1. `GET /models` 返回所有模型（分页）
2. `POST /models` 可创建新模型，数据写入数据库
3. `PUT /models/{id}` 可更新模型配置
4. `DELETE /models/{id}` 可删除模型
5. 前端 `/models` 页面可查看、添加、编辑、删除模型
6. `AgentConfigForm` 中的模型列表来自 API，不再使用 `MOCK_MODELS`
7. 所有现有测试保持通过

### Agent 向导

1. 点击"创建 Agent"后进入 3 步向导
2. 每步有进度指示器（Step X/3）
3. Step 1 必填项未填时"下一步"禁用
4. Step 3 展示汇总信息供确认
5. 点击"创建"后提交表单，成功后关闭弹窗并刷新列表
6. 编辑 Agent 时同样使用向导，但数据预填充

---

## 七、下一步建议

**立即开始：模型管理 CRUD（P0）**

原因：

- 它是功能缺口，直接影响"多模型"核心卖点的完整性
- 完成后 `AgentConfigForm` 的动态加载才有数据基础
- 工程量适中（2-3 天），收益明显

**然后：Agent 向导重构（P0）**

原因：

- 依赖模型管理完成（Step 2 需要动态模型列表）
- 纯前端改动，工程量可控

**之后：按 P1 → P2 顺序推进**

---

## 八、文档索引

| 文档                              | 路径                                                      |
| --------------------------------- | --------------------------------------------------------- |
| 原 8 阶段 Roadmap                 | `docs/roadmap/modelgate-next-step-full-plan.md`         |
| Runtime MVP 实施日志              | `docs/implementation/runtime-mvp-implementation-log.md` |
| Phase 1 E2E Demo                  | `docs/implementation/phase1-summary.md`                 |
| Phase 2 Provider                  | `docs/implementation/phase2-provider-summary.md`        |
| Phase 3 Supervisor                | `docs/implementation/phase3-supervisor-summary.md`      |
| Phase 4 Memory/Skill              | `docs/implementation/phase4-memory-skill-summary.md`    |
| Phase 7 Deployment                | `docs/implementation/phase7-deployment-summary.md`      |
| **本文件：后续开发计划 v2** | `docs/roadmap/modelgate-next-steps-v2.md`               |
