# ModelGate Agent Studio

> 让多个 AI 模型像团队一样协作，也像人一样积累经验。
>
> Turn multiple AI models into a coordinated team that remembers, learns, and hands off work.

ModelGate Agent Studio 是一个本地可跑的**多模型 Agent 协作平台**：把不同 LLM 组织成角色化 Station（Planner / Coder / Reviewer / Researcher / Summarizer / Supervisor），通过任务拆解、模型路由、额度感知调度和结构化 Handoff 推进复杂目标；再通过本地 Memory、RAG 检索和 Skill 沉淀，把每一次执行的上下文、经验、错误、解决方案和工作流变成可复用知识——**模型可以换，经验不能丢**。

## 当前能力（全部实测验证）

### 核心执行闭环（V1.0）

```text
用户输入 Goal → Planner 拆解 Task → Router 选择 Station/Model
→ Worker 执行（工具调用 + 资源预算）→ 完成门禁验证 → Final Summary
```

- FastAPI + SQLAlchemy + Alembic 后端，React 19 + Vite + shadcn/ui 前端
- 6 个内置 Station 种子、模型注册与健康检查、混合检索知识源
- `docker compose up` 一键起栈，`bash scripts/e2e-demo.sh` 端到端验证

### Handoff 完整业务流（V1.1）

```text
错误 / 配额耗尽 / 验证失败 → 自动触发交接 → LLM 生成结构化交接摘要
（generated_by 溯源，模板兜底）→ Workspace 任务卡交接状态条
→ 用户接受 → 新 Worker 继承上下文继续执行 → 结果写回 → Logs 事件链
```

- Station 级 `handoff_policy` 管控全部自动触发点（can_initiate /
  on_provider_error / on_quota_exhausted / on_quality_issue）
- 交接摘要携带 changed_files 校验和，接手时做工作区一致性校验
- 配额页展示每模型触发交接次数；`scripts/e2e-handoff.sh` 验收通过

### 本地 Memory / RAG / Skill 沉淀（V1.2）

- **Memory**：执行完成后自动沉淀项目 / Agent / 经验记忆；错误自动变成
  「经验记忆」（稳定错误签名 + 解决方案叙事，同类合并计数）
- **偏好**：显式用户偏好 born-approved，无条件注入之后每一次执行的上下文
- **RAG**：记忆 / 技能 / 工作区文档统一进入混合检索（关键词 + 余弦），
  嵌入后端可插拔（本地 hash 兜底，任意 OpenAI-compatible provider 可升级），
  换模型不锁知识
- **Skill**：验证通过的执行自动蒸馏为技能草稿，人工审批后入库；
  成功率参与排序（失败技能降权），规划期推荐相关技能，
  上下文内渐进披露（摘要 + ≤3 步，全量走详情接口）
- **可溯源**：检索候选逐条落库（retrieval_runs / retrieved_context_items /
  context_package_snapshots），知识到证据全程可审计
- Evolution 页提供记忆/技能审批、偏好创建、成功率可视化

## 快速开始（Mock 模式，无需 API Key）

前置：Docker 24+ 与 Compose v2。详细操作见 [docs/e2e-docker-stack.md](./docs/e2e-docker-stack.md)。

```bash
# 1. 起栈（mock 模式，代码热重载）
EXECUTION_MODE=mock docker compose -f docker-compose.dev.yml up -d --build

# 2. 灌入演示数据（6 个 Station + 6 个模型）
docker exec modelgate-backend-dev python seed_demo_data.py

# 3. 端到端验收（两条都要 PASS）
bash scripts/e2e-demo.sh      # 核心闭环：Goal → Final Summary
bash scripts/e2e-handoff.sh   # V1.1：配额耗尽 → 自动交接 → 接受 → 恢复

# 4. 打开前端
open http://localhost:5173

# 5. 收工
docker compose -f docker-compose.dev.yml down
```

### 接入真实 Provider

默认执行模式是 `live`：没有密钥会明确失败，**不会静默退回 Mock**。

```bash
export MODEL_GATE_EXECUTION_MODE=live
export PROVIDER_API_BASE=https://api.openai.com/v1
export PROVIDER_API_KEY=sk-xxx
# 可选：RAG 嵌入升级（默认本地 64 维 hash，零依赖）
export EMBEDDING_BACKEND=real
export EMBEDDING_MODEL_NAME=text-embedding-3-small
```

生产栈与开发栈的完整说明见 [docs/e2e-docker-stack.md](./docs/e2e-docker-stack.md)。

## 本地开发与测试

```bash
# 后端（Python 3.12，venv 或 docker verify profile）
cd backend
./.venv/bin/python -m pytest tests/ -q          # 451 passed, 1 skipped

# 前端（Node 22，见 .nvmrc）
cd frontend
npm ci
npm run typecheck                                # tsc -b
npm run test                                     # vitest，183 tests
npm run lint                                     # oxlint
npm run build                                    # tsc + vite build
```

后端也可以完全在容器里验证（宿主机无需 Python）：

```bash
docker compose --profile verify build backend-verify
docker compose --profile verify run --rm backend-verify
```

## 仓库结构

```text
├── backend/                 # FastAPI + SQLAlchemy + Alembic（src/{models,services,routes,runtime}）
├── frontend/                # React 19 + Vite + Tailwind v4 + shadcn/ui
├── docs/
│   ├── design/              # 2026-09-06 平台重设计 —— 唯一权威设计文档
│   ├── e2e-docker-stack.md  # Docker / e2e 运维指南
│   ├── README.md            # 文档入口与使用规则
│   └── _archive_2026/       # 历史规划文档与已完成阶段计划（只读考古）
├── scripts/                 # e2e-demo.sh / e2e-handoff.sh / api-smoke.sh / wait-for-services.sh
├── docker-compose*.yml      # 生产栈 / 开发热重载栈 / Postgres 栈
├── CHANGELOG.md             # 版本发布记录（V1.0 → V1.2）
├── CLAUDE.md                # AI 编码代理的项目上下文说明
└── HANDOVER.md              # 交接文档：进度、已知坑、路线图
```

## 文档索引

| 文档 | 说明 |
|------|------|
| [docs/design/2026-09-06-platform-redesign.md](./docs/design/2026-09-06-platform-redesign.md) | **唯一权威设计文档**（架构 / Station 模型 / 数据 / V1.0–V1.4 阶段） |
| [CHANGELOG.md](./CHANGELOG.md) | V1.0 / V1.0.1 / V1.1 / V1.2 发布记录 |
| [HANDOVER.md](./HANDOVER.md) | 交接文档：实测数字、已知怪癖、后续计划 |
| [docs/e2e-docker-stack.md](./docs/e2e-docker-stack.md) | Docker 栈启动 / e2e 验收操作指南 |
| [docs/README.md](./docs/README.md) | 文档目录与变更规则（架构变更先改设计文档） |
| docs/_archive_2026/ | 旧规划文档 + 已完成阶段计划（V1.0.1-V1.1、V1.2），只读 |

## 路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| V1.0 | 核心执行闭环 | ✅ 完成 |
| V1.0.1 | 修复批（构建 / 测试 / 文档） | ✅ 完成 |
| V1.1 | Handoff 完整业务流 + 配额可视化 | ✅ 完成 |
| V1.2 | 本地 Memory / RAG / Skill 沉淀 | ✅ 完成 |
| V1.2.1 | Architecture Alignment + CI + Product Acceptance | ⏳ 进行中 |
| V1.3 | Real Multi-Provider + MCP | 待立项 |
| V1.4 / V1.5 / V2.0 | Parallel Runtime / Evolution 2.0 / Developer Agent OS | 待立项 |

完整阶段定义（P0–P6）与版本边界见 [ROADMAP.md](./ROADMAP.md)；当前阶段执行计划见 [V1.2.1-plan.md](./V1.2.1-plan.md)。真实 Provider smoke 并入 V1.3 Real Multi-Provider。

## License

MIT License
