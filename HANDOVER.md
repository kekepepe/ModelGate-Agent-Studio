# ModelGate Agent Studio — V1.0 项目交接文档

> 写给"之后接手这个项目的人"。读完这份文档你应该能：
> 1. 一句话说出项目现在能做什么
> 2. 知道每一块代码在哪里、为什么是这样
> 3. 知道下一步该做什么、按什么顺序
>
> 写于 2026-09-15，V1.0 收尾、V1.0.1 尚未启动的时间点。
> 当前 HEAD: `63868dc` (main)。所有 V1.0 进度已 push 到 `origin/main`。

---

## 0. 一句话总结

**ModelGate Agent Studio** 是一个本地可跑的多角色 Agent 协作平台。V1.0 已经完整跑通核心闭环：

```
用户输入 Goal → Planner 拆 Task → Router 选 Station/Model → Worker 执行 → Final Summary
```

一份 `docker compose up` 起来，一条 `bash scripts/e2e-demo.sh` 就能端到端验证。V1.0 不带 Handoff / Quota / 并行，这些都进了 V1.1 / V1.2。

---

## 1. 仓库位置

| 项 | 值 |
|---|---|
| 本地路径 | `/Users/kepeng/codex_project/ModelGate Agent Studio` |
| 远程 | `https://github.com/kekepepe/ModelGate-Agent-Studio.git` |
| 默认分支 | `main` |
| 用户 Git 名 | `kekeppe` |
| 凭证存储 | macOS Keychain (osxkeychain credential helper) — `git push` 不再弹密码 |

⚠️ 路径里有空格，命令行引用时记得加引号：`cd "/Users/kepeng/codex_project/ModelGate Agent Studio"`。

---

## 2. V1.0 已完成的 29 个提交

按时间顺序（oldest → newest），到 HEAD `63868dc`：

### 设计 & 归档

| Commit | 内容 |
|---|---|
| `b93fb39` | `docs(design)`：2026-09-06 平台重设计（**单一权威文档**，11 章，33KB） |
| `56dd1de` | `docs(v1.0-1)`：归档 99 份旧 P0-P7 规划文档到 `docs/_archive_2026/` |

### 后端（V1.0-2 / V1.0-3 / V1.0-4）

| Commit | 内容 |
|---|---|
| `1079a86` | LiteLLM provider + state machine runtime |
| `5c5d083` | Settings 接入 provider_api_*（配置接通 LLM Provider） |
| `59bf1b9` | Station 增 `slug` / `is_builtin` / `handoff_policy` 字段 + Alembic 0010 |
| `440158d` | V1.0-3 清理 + 删除日志 |
| `86d5081` | **删除全部 5 个 P0-P7 CI workflow**（无替代；CI 推迟到 V1.0.1） |
| `8d3bc7d` | Runtime entry 层 + 8 个 V1.0-4 验收测试 |

### 前端（V1.0-5 / V1.0-6）

| Commit | 内容 |
|---|---|
| `d8ba8c5` | shadcn/ui 集成 + 10 个 agent 状态色 token + `AgentStatusBadge` |
| `a08169a` | `ActiveStationsSidebar`（仿 Star-Office-UI 访客列表） |
| `d545009` | TopBar 状态分布徽章（仿控制条） |
| `04bf521` | `ThreeZoneCardFlow` 视图（仿 3 区布局） |
| `64d6947` | `FinalSummaryPanel`（仿 Memo 模式） |

### 集成 & 收尾（V1.0-7 / V1.0-8）

| Commit | 内容 |
|---|---|
| `e3fc444` | docker compose 本地栈 + `scripts/e2e-demo.sh`（已 verified PASS） |
| `36094e0` | 重写根级 `CHANGELOG.md`（V1.0 release notes） |
| `023cb70` | 提交 V1.0-5 的 `package-lock.json` |

### 前端 shadcn 化（P0 / P1 / P2 / P3 — V1.0.1 之前补的活）

| Commit | 内容 |
|---|---|
| `437e5b9` | shadcn 重构 `TaskCard` + `AgentStationCard` + `WorkspacePage` |
| `ac7d848` | SSE 接入 `BottomConsole` + 连接状态徽章 |
| `37af35b` | `GET /api/v1/tasks` 列表接口 + `useTasks` hook + Sidebar current task 行 |
| `7c500f7` | shadcn 重构 5 个 secondary 组件 |
| `de74563` | `GoalInputPanel` 收尾 shadcn 化（剩余 P0-P7 classNames） |
| `63868dc` | shadcn 重构 `PlanOverviewPanel` |

---

## 3. 当前可运行状态（实测数字）

> 2026-09-15 V1.0.1/V1.1 收尾后更新；逐项进度见 `V1.0.1-V1.1-plan.md`。

| 项 | 数值 |
|---|---:|
| 后端 pytest | **428 passed, 1 skipped, 0 failures**（V1.0 末态 411） |
| 前端测试 | **180 passed / 37 文件**（V1.0 末态实际有 16 个失败测试被 vitest 别名缺失掩盖，已修复） |
| 前端 typecheck / build / lint | **0 errors** |
| `scripts/e2e-demo.sh` | **PASS**（V1.0-7 验证；本阶段未改动其流程） |
| `scripts/e2e-handoff.sh` | **PASS**（V1.1 验收：quota 耗尽 → auto-handoff → accept → 恢复 → completed，本地 mock 后端实测） |
| CI（GitHub Actions） | **暂缓**（用户决定；恢复路径见 `docs/_archive_2026/v1.0_deletions_log.md` §6） |
| Working tree | **干净** |
| V1.0.1/V1.1 期间新增 commit | 10（`c4e8f91` → B14） |

---

## 4. 技术栈（已定型，不要轻易换）

### 后端
- **Python 3.12** + FastAPI + SQLAlchemy 2 async + Pydantic v2
- **LiteLLM** 统一 LLM Provider 抽象（业务代码不直接 import litellm）
- **arq**（已加但 V1.0 未启用，留给 V1.3+ 多 Worker 并行）
- **Alembic** 做迁移（V1.0 末态是 `0010_station_design_fields`）
- **SQLite** 默认；docker compose 可切 Postgres

### 前端
- **React 19** + **Vite**
- **react-router-dom v7**（声明式 `<Routes>`，定义在 `src/App.tsx`）+ **TanStack Query**
- **shadcn/ui**（new-york preset，slate base，**copy-paste 模式不是 npm 依赖**）
- **Tailwind v4** + 10 个 agent 状态色 CSS 变量
- **Zustand**（shadcn 配套引入）
- **Radix UI**（shadcn 底层）+ **lucide-react**（图标）

### Agent 模型（产品决策）
- **多角色 Station**（Planner / Coder / Reviewer / Researcher / Summarizer / Supervisor）+ 用户可扩展
- ❌ **不是**单个动态 Agent
- ❌ **不是**完全用户自定义

### UI 设计参考
- **Star-Office-UI**（`ringhyacinth/star-office-ui`，7K+ stars）作为**设计模式参考**
- 借鉴了 4 个模式：访客列表 / 控制条 / 3 区布局 / Memo 面板
- ❌ **没有**安装它的 Python+Phaser 代码
- ❌ **没有**作为 skill 引入
- 详细设计：见 `docs/design/2026-09-06-platform-redesign.md` §5

---

## 5. 关键文件索引（接手者必看）

### 文档（按重要性）

| 文件 | 作用 |
|---|---|
| `docs/design/2026-09-06-platform-redesign.md` | **单一权威设计**，11 章，定义 V1.0–V1.4 phasing |
| `HANDOVER.md`（本文档） | 交接 |
| `CHANGELOG.md` | V1.0 release notes |
| `V1.0-7-e2e.md` | docker compose + e2e 操作指南 |
| `V1.0-frontend-plan.md` | P0/P1/P2/P3 实施计划（已完成） |
| `docs/_archive_2026/v1.0_deletions_log.md` | **每个删除/保留决定都有记录**，删东西前必看 |
| `docs/_archive_2026/` | 99 份旧规划文档，**不是源码依赖**，参考用 |
| `docs/README.md` | 指向新设计文档 |

### 后端核心模块

| 路径 | 作用 |
|---|---|
| `backend/src/main.py` | FastAPI 入口 |
| `backend/src/runtime/__init__.py` | **V1.0-4 entry 层**，对外 re-export `execute_goal_pipeline` / `get_runtime_status` 等 |
| `backend/src/services/runtime_service.py` | Runtime 主实现（1550 行，**V1.0 没改这个文件**，走 re-export） |
| `backend/src/services/orchestrator_service.py` | 编排（457 行） |
| `backend/src/providers/{base,literal_moved,litellm_provider,mock_provider}.py` | LLM Provider 抽象 |
| `backend/src/services/state_machine_service.py` | Goal / Task 状态机（原路径，被 `src.runtime` re-export） |
| `backend/src/services/task_service.py::list_tasks` | V1.0-P1-2 列表筛选 helper |
| `backend/src/routes/tasks.py::GET /api/v1/tasks` | V1.0-P1-2 endpoint（**必须在 `GET /tasks/{task_id}` 之前注册**避免路径遮蔽） |
| `backend/alembic/versions/0010_station_design_fields.py` | Station.slug/is_builtin/handoff_policy 迁移 |
| `backend/requirements.txt` | `httpx>=0.27,<0.29`（宽 pin，见 §7） |

### 前端核心模块

| 路径 | 作用 |
|---|---|
| `frontend/components.json` | shadcn new-york preset 配置 |
| `frontend/src/index.css` | Tailwind v4 + shadcn 主题 + **10 个状态色 CSS 变量** |
| `frontend/src/lib/utils.ts` | `cn()` 工具 |
| `frontend/src/components/ui/agent-status-badge.tsx` | **共享状态徽章**，映射 30+ 状态枚举到 V1.0-5 颜色 |
| `frontend/src/components/ui/{avatar,badge,button,card,input,scroll-area,separator,tabs,textarea,tooltip}.tsx` | 10 个 shadcn 基础组件（commit 进库） |
| `frontend/src/components/ui/select.tsx` | Radix Select 封装；**已被 LogFilters / GoalInputPanel 引用，V1.0.1 已提交**（见 §7.1 修订） |
| `frontend/src/hooks/useRuntimeEvents.ts` | SSE 事件流 hook（P1-1 修了 listener 泄漏） |
| `frontend/src/hooks/useTasks.ts` | `/api/v1/tasks` 数据 hook（V1.0-P1-2） |
| `frontend/src/api/tasks.ts` | `/api/v1/tasks` axios wrapper |
| `frontend/src/components/app-shell/ActiveStationsSidebar.tsx` | Star-Office-UI 访客列表模式 |
| `frontend/src/components/BottomConsole.tsx` | SSE 驱动，10s polling fallback |
| `frontend/src/components/PlanOverviewPanel.tsx` | V1.0 末位完成 shadcn 化 |
| `frontend/src/components/{WorkerBadge,LogListItem,LogFilters,GoalInputPanel,TaskTree}.tsx` | P2 shadcn 化 5 个 secondary 组件 |
| `frontend/src/components/{TopStatusBar,WorkspaceModeSwitch,CardFlowRenderer,ThreeZoneCardFlow,PixelOfficeRenderer}.tsx` | **故意没 shadcn 化**（含自定义布局：flow connectors、pixel canvas、tinted zone headers） |

### 操作脚本

| 文件 | 作用 |
|---|---|
| `scripts/e2e-demo.sh` | 端到端 smoke test（mock 模式） |
| `docker-compose.dev.yml` | 本地开发栈 |

---

## 6. 接手者验证清单

按顺序跑一遍，5 分钟确认接手的代码状态：

```bash
cd "/Users/kepeng/codex_project/ModelGate Agent Studio"

# 1. git 状态
git status -sb          # 应该只有 ?? frontend/src/components/ui/select.tsx 一项
git log --oneline -5    # HEAD 应该是 63868dc

# 2. 后端测试
cd backend && pytest -q && cd ..     # 应该输出 411 passed, 1 skipped

# 3. 前端构建
cd frontend && npm run typecheck     # 0 errors
npm run build                        # 197ms 通过
cd ..

# 4. 端到端（可选，需要 docker）
EXECUTION_MODE=mock docker compose -f docker-compose.dev.yml up -d --build
sleep 15
bash scripts/e2e-demo.sh             # PASS
docker compose -f docker-compose.dev.yml down
```

任何一步失败，**先看 §7 已知怪癖**。

---

## 7. 已知怪癖 / 坑

接手者大概率会踩，提前打预防针：

### 7.1 shadcn CLI 的 alias bug
`npx shadcn@latest add <component>` 会把文件写到字面意义的 `./@/components/ui/` 目录，**不解析 Vite 的 `@/` alias**。每次都得手动 `mv` 修复。建议脚本化：

```bash
npx shadcn@latest add select --yes
mkdir -p src/components/ui
mv -f ./@/components/ui/select.tsx src/components/ui/select.tsx 2>/dev/null
rm -rf "./@"
```

**这就是 `select.tsx` 起初没 commit 的原因。** ⚠️ 修订（V1.0.1）：交接时"没被任何文件 import"的判断是**错的** —— P2/P3 提交的 `LogFilters.tsx` 和 `GoalInputPanel.tsx` 实际引用了它，新 clone 会构建失败。已在 V1.0.1 提交修复（`c4e8f91`）。shadcn CLI 的 alias bug 本身依然存在，脚本化绕过方式如上。

### 7.2 `httpx==0.28.1` 被宽 pin 成 `httpx>=0.27,<0.29`
Docker build 时与 `litellm 1.55.0` 的 `httpx<0.28.0` 冲突；本地 venv 之前静默用的是 0.27.2。**改 httpx 版本时记得检查 litellm 约束**，别简单 bump 到最新。

### 7.3 `useRuntimeEvents` 的 listener 泄漏
V1.0-2 初版 hook **没调用 `removeEventListener`**，P1-1 接入 BottomConsole 时修复。改这个 hook 时记得 unmount 路径。

### 7.4 5 个组件**故意**不 shadcn 化
`TopStatusBar` / `WorkspaceModeSwitch` / `CardFlowRenderer` / `ThreeZoneCardFlow` / `PixelOfficeRenderer` —— 这些有自定义布局（flow connectors / pixel canvas / tinted zone headers），不打算走 shadcn。**不要把"还没 shadcn 化"等同于"技术债"**。

### 7.5 `paused` 不是合法的 `TaskStatus` enum
前端类型里没这个值。P1-2 Sidebar 筛选时专门去掉了，避免 TS error。

### 7.6 `AgentStatusBadge` 的 `label` prop 是 `label?: string`
调用时 `null` 必须用 `?? undefined` 转，不能用 `||`（strict mode 下 React 会抱怨）。P2 修过 WorkerBadge。

### 7.7 旧 P0-P7 classNames 残留在大部分 `frontend/src/components/*.tsx`
V1.0-P0/P1/P2/P3 只重构了 11 个高频组件。其余 30+ 组件（`AgentDetailModal`、`HandoffList`、`TaskDetailPanel` 等）**仍是 P0-P7 风格**。这不是 bug，是计划内 —— 全面重构是 V1.0.1+ 的活。

### 7.8 `.github/workflows/` 当前是空的
V1.0-3.7 删除了全部 5 个 P0-P7 workflow。V1.0 故意"无 CI 推送"。**V1.0.1 的第一个 commit 应该补齐最小 CI**（backend pytest + frontend build）。

---

## 8. 未来计划（按设计文档 V1.0 → V1.4）

> ⚠️ 2026-09-15 起，V1.0.1 / V1.1 的**执行计划与进度跟踪已迁移到 [`V1.0.1-V1.1-plan.md`](./V1.0.1-V1.1-plan.md)**（根目录，含设计决策 D1-D7 与 checkbox）。下面保留原始路线图供总览。本节全部来自 `docs/design/2026-09-06-platform-redesign.md` §8。

### V1.0.1 — 补齐 V1.0 短板（最近期，1-2 周）

| # | 任务 | 说明 |
|---|---|---|
| 1 | **补 V1.0 CI**（最优先） | `.github/workflows/backend-ci.yml`（pytest）+ `frontend-ci.yml`（build + typecheck）。设计稿在 `docs/_archive_2026/v1.0_deletions_log.md` §6 |
| 2 | **真实 Provider smoke** | `scripts/e2e-real-provider.sh`，需要 OpenAI-compatible key + 5-10 分钟预算。环境变量同 `docker-compose.dev.yml` 真实模式 |
| 3 | **剩余 30+ 组件 shadcn 化** | 优先 `AgentDetailModal` / `TaskDetailPanel` / `HandoffList` / `QuotaAlertBanner` / `ModelUsagePieChart` 等高频页面相关组件 |
| 4 | **清理孤儿 `select.tsx`** | 要么 commit 要么删（"uncertain AND simple/reproducible → 删"原则） |

### V1.1 — Handoff + Quota（+1-2 周）

来自设计 §8 V1.1：

- Handoff 状态机 + Summary 生成（LLM 优先，fallback 模板）
- Quota 记录 + 状态机 + 拦截（数据模型 V1.0 已经有了）
- Workspace Task Card 上的 Handoff 状态条
- **Quota Overview 页**（V1.0 已删掉 `/api/v1/dashboard`，这里需要重建）

**验收**：模拟 quota 耗尽，能看到 auto-handoff，Logs 能看到 Handoff 事件链。

### V1.2 — 实时 + 打磨（+1 周）

- ✅ SSE 已接入 BottomConsole（V1.0-P1-1）—— 这部分**提前完成了**
- Workspace 状态恢复（URL 刷新继续看）
- Task Detail 侧栏（Router 决策 / Token / Context / Logs tab）
- Pixel Office 简化版（可选）
- 全局错误处理 / Toast / 加载态

### V1.3 — 自定义 Station + MCP（+2 周）

- Agents 页（编辑 / 克隆 / 试运行）
- Models 页（注册 / 测试连接 / 启禁用）
- Tools 页（MCP tool 列表 / 权限）
- Station 试运行（独立小窗口）
- **启用 arq + Redis 做多 Worker 并行**（V1.0 已加依赖，未启用）

### V1.4 — 进阶（按需）

- 有限并行 Task（V1.0 一个 Goal 同一时刻只能 1 个 active Task；V1.4 引入并行）
- Goal 复制 / 模板
- Export Final Summary
- Nightly Provider Benchmark runner
- Postgres + Redis 切换

### V2.0+（设计中不做，备忘）
- Memory / Skill / 自进化

---

## 9. 接手者的工作约定（必须遵守）

来自 `docs/design/2026-09-06-platform-redesign.md` §11 与用户约定：

### 9.1 Commit hygiene
- ✅ **每个子任务 = 1 个 commit + 1 个 push**，绝不攒批
- ✅ Commit 信息包含阶段标签：`[V1.0]` / `[V1.0.1]` / `[V1.1]` 等
- ✅ 格式：`<type>(<scope>): <subject>`（feat / fix / refactor / docs / test / chore）
- ✅ 不创建 Release Tag（V1.0 之前不发版）

### 9.2 删除原则（用户原话）
- **保留**一切后续可能用到的东西（记录下来）
- **删除**仅当 "uncertain AND simple/reproducible"（不确定且容易重新生成）
- 每次删除/保留决定都更新 `docs/_archive_2026/v1.0_deletions_log.md`

### 9.3 决策模式
- 用户偏好："我定你执行" + "你推荐我拍板"
- 默认推进，**只在用户必须决定时提问**（一次问完，不要反复确认）

### 9.4 沟通风格
- 中文为主
- 简短状态报告，不要复述情绪
- 一句话能说完的不写一段

### 9.5 文件操作
- 不要 `rm -rf` session workspace（沙箱会拦）
- 删具体子路径可以；删整树不行

---

## 10. 我现在没做、要立刻决定的事

> ✅ V1.0.1 全部落定（2026-09-15），原始决策与理由保留如下：

1. **`frontend/src/components/ui/select.tsx` 未 commit**
   - ✅ **决定：提交**。交接时的"没被任何文件 import"判断有误（LogFilters / GoalInputPanel 引用了它），删除会弄坏新 clone。已提交（`c4e8f91`）。
2. **`V1.0-frontend-plan.md` 没归档**
   - ✅ **决定：归档**到 `docs/_archive_2026/`（已实施完毕的 P0-P3 历史记录，保留但移出根目录）。
3. **`HANDOVER.md`（本文档）是否归档**
   - ✅ **决定：留在根目录**，与 `CHANGELOG.md` / `CLAUDE.md` 同级作为长期参考。

---

## 11. 联系方式 / 上下文

- 用户：solo developer，工作模式"我定你执行"
- 当前主语言：中文
- 平台：macOS
- AI 助手：Mavis（MiniMax Code 内的 coding agent）
- 邮箱：3522651528@qq.com（不在 commit 历史里，仅供联系）

---

> 文档结束。下一次变更请直接修改本文档；如果发生结构性变化（比如 V1.0.1 完成），把"未来计划"段重新组织，把已完成的从清单里挪到"已完成"。