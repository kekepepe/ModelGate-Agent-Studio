# ModelGate Agent Studio 文档中心

> 本文档是 ModelGate Agent Studio 所有技术文档和产品文档的入口索引。
>
> **原则**：以 `prd/` 目录下的技术型 PRD 为唯一权威需求来源。与 PRD 冲突的早期文档已归档至 `_archive/`，不再维护。

---

## 阅读顺序

如果你是第一次接触本项目，建议按以下顺序阅读：

1. **[product/overview.md](product/overview.md)** — 产品定位、愿景、目标用户（5 分钟）
2. **[roadmap.md](roadmap.md)** — V0 → MVP → V1 的产品路线图（5 分钟）
3. **[mvp/MVP-功能优先级裁剪.md](mvp/MVP-功能优先级裁剪.md)** — MVP 范围与 MoSCoW 优先级（10 分钟）
4. **[prd/agent-workspace-prd.md](prd/agent-workspace-prd.md)** — 核心页面：Workspace 状态可视化（20 分钟）
5. **[prd/handoff-manager-prd.md](prd/handoff-manager-prd.md)** — 核心能力：Handoff 交接（15 分钟）
6. **[architecture/数据结构与数据库Schema.md](architecture/数据结构与数据库Schema.md)** — 权威数据结构总览（10 分钟）

之后按需阅读其他 PRD：

- **Model Router** → [prd/model-router-prd.md](prd/model-router-prd.md)
- **Quota Manager** → [prd/quota-manager-prd.md](prd/quota-manager-prd.md)
- **Agent Registry** → [prd/agent-registry-prd.md](prd/agent-registry-prd.md)
- **Logs / Observability** → [prd/logs-observability-prd.md](prd/logs-observability-prd.md)

---

## 目录说明

### `prd/` — 产品需求文档（当前有效，唯一权威）

| 文件 | 说明 | 阶段 |
|------|------|------|
| [agent-workspace-prd.md](prd/agent-workspace-prd.md) | Workspace 页面：状态可视化、布局、组件、状态机 | MVP-A/B |
| [handoff-manager-prd.md](prd/handoff-manager-prd.md) | Handoff Manager：交接流程、Summary、状态流转 | MVP-A/B |
| [model-router-prd.md](prd/model-router-prd.md) | Model Router：规则评分路由、风险标记 | MVP-A/B |
| [quota-manager-prd.md](prd/quota-manager-prd.md) | Quota Manager：额度记录、估算、风险状态 | MVP-A/B |
| [agent-registry-prd.md](prd/agent-registry-prd.md) | Agent Registry：Agent Station CRUD、模板 | MVP-A/B |
| [logs-observability-prd.md](prd/logs-observability-prd.md) | Logs：全链路可观测性、10 种日志类型 | MVP-A/B |

**规则**：所有数据对象定义、状态枚举、接口设计以 PRD 为准。

### `stories/` — 用户故事（可转测试）

| 文件 | 说明 | 状态 |
|------|------|------|
| [handoff-manager-stories.md](stories/handoff-manager-stories.md) | Handoff Manager 用户故事与验收标准 | 已完成 |

**待补齐**：agent-workspace、model-router、quota-manager、logs-observability、agent-registry。

### `architecture/` — 架构与接口

| 文件 | 说明 |
|------|------|
| [API-Contract.md](architecture/API-Contract.md) | 前后端接口通用约定（Base URL、响应格式、分页） |
| [数据结构与数据库Schema.md](architecture/数据结构与数据库Schema.md) | **权威数据结构总览**：从所有 PRD 提取的统一对象定义和状态枚举 |

**注意**：`数据结构与数据库Schema.md` 已按 PRD 重写。如与 PRD 冲突，以 PRD 为准，Schema 文档会同步更新。

### `runtime/` — 执行层规范

| 文件 | 说明 |
|------|------|
| [Agent-Runtime规则.md](runtime/Agent-Runtime规则.md) | Agent 执行标准流程、Task 调度、Worker 池 |
| [Prompt模板文档.md](runtime/Prompt模板文档.md) | 各 Agent 的 Prompt 模板设计原则 |

### `ui/` — UI 规范

| 文件 | 说明 |
|------|------|
| [UI状态与交互动效规则.md](ui/UI状态与交互动效规则.md) | 状态颜色系统、Task 卡片状态、动效规则 |

### `mvp/` — 范围与规划

| 文件 | 说明 |
|------|------|
| [MVP-功能优先级裁剪.md](mvp/MVP-功能优先级裁剪.md) | MoSCoW 优先级分析，MVP-A/B/C 范围定义 |
| [roadmap.md](../roadmap.md) | 产品路线图：V0 → MVP → V1 |

### `product/` — 产品概述（对外用）

| 文件 | 说明 |
|------|------|
| [overview.md](product/overview.md) | 产品名称、定位、愿景、核心价值、亮点 |

### `demo/` — Demo 与验收

| 文件 | 说明 |
|------|------|
| [Demo-Script与测试用例.md](demo/Demo-Script与测试用例.md) | 标准 Demo 流程和测试用例 |

### `_archive/` — 归档历史文档（不再维护）

| 文件 | 归档原因 |
|------|----------|
| `02-产品设计.md` | 内容被 `prd/` 各模块 PRD 覆盖 |
| `03-技术架构与差异化.md` | 内容被 `prd/` 和 `runtime/` 覆盖 |
| `v0.1-mvp-冻结文档.md` | 与 `roadmap.md` + `MVP-功能优先级裁剪.md` 重复 |
| `未来开发方向与路线图.md` | 与 `roadmap.md` 重复 |
| `核心用户流程.md` | 内容被各 PRD 中的用户流程章节覆盖 |

---

## 术语速查

| 术语 | 定义 |
|------|------|
| **Goal** | 用户输入的顶层目标，系统将其拆解为多个 Task |
| **Task** | Goal 拆解后的子任务，有状态、优先级、分配 Agent |
| **Agent Station** | Agent 工位，代表一个角色（Planner / Coder / Reviewer 等），不等于模型 |
| **Worker** | 绑定到 Agent Station 的模型实例，执行具体 Task |
| **Model** | 底层模型能力（gpt-4o / claude-3-5 等），被 Worker 调用 |
| **Handoff** | 任务交接：当前 Worker 无法继续时，结构化传递上下文给新 Worker |
| **Routing** | 模型路由：根据 Task 特征选择最合适的模型 |
| **Quota** | 模型额度：调用次数、token 使用量、剩余估算 |

完整术语表见 [architecture/数据结构与数据库Schema.md](architecture/数据结构与数据库Schema.md) 第 1 节。

---

## 文档维护规则

1. **PRD 优先**：任何数据对象、状态枚举、接口定义的冲突，以 `prd/` 目录下的 PRD 为准。
2. **变更同步**：修改 PRD 中的数据对象后，同步更新 `architecture/数据结构与数据库Schema.md`。
3. **归档不删**：`_archive/` 中的文档保留历史，但不再维护。新开发不引用归档文档。
4. **用户故事驱动**：每个 PRD 模块应配套 `stories/` 下的用户故事文档，作为开发验收依据。

---

> 最后更新：2026-06-25
