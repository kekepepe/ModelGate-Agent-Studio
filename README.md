# ModelGate Agent Studio

> 让多个 AI 模型像团队一样协作，也像人一样积累经验。
> 
> Turn multiple AI models into a coordinated team that remembers, learns, and hands off work.

## 项目简介

ModelGate Agent Studio 是一个面向开发者的**多模型 Agent 协作与自进化知识平台**。它能够接入多个模型 API 和 AI Coding Plan，将不同模型组织成具有不同职责的 Agent 团队，并通过任务拆解、模型路由、额度感知调度、任务交接和 Supervisor 审查，实现复杂开发任务的持续推进。

平台进一步通过本地 Memory、RAG 检索和 Skill 沉淀机制，将每一次项目执行过程中的上下文、经验、错误、解决方案和工作流转化为可复用知识。未来无论接入哪个模型，Agent 都可以读取本地知识库，继承过去的项目经验和用户偏好，从而不断优化自己的任务完成流程。

## 核心定位

ModelGate Agent Studio 不是普通 AI 聊天工具，也不是简单的多 API 聚合器，而是一个用于**组织、调度和监督多个模型 Agent 协作完成复杂目标的工作台**。

## 核心功能

### 🤖 多模型 Agent 协作

- **Agent Station 角色化**：Planner、Coder、Reviewer、Researcher、Summarizer、Supervisor、Knowledge Evolution Agent
- **模型能力路由**：根据任务类型、复杂度、上下文长度和额度状态自动选择合适模型
- **多步执行与状态管理**：完整记录任务执行过程

### 🔄 额度感知与任务交接

- **额度监控**：实时追踪每个模型的调用次数、token 使用量和额度状态
- **Handoff 机制**：额度不足时自动生成结构化交接摘要
- **无缝续接**：接手 Agent 基于 Handoff Summary 继续执行任务

### 🧠 自进化知识库

- **六层 Memory 架构**：Raw Memory → Session Memory → Project Memory → User Memory → Agent Memory → Skill Memory
- **自动知识提炼**：任务完成后自动提取经验、偏好、错误修复和工作流
- **RAG 检索增强**：新任务开始前自动加载相关历史记忆
- **Skill Library**：沉淀可复用任务执行模板

### 🔧 MCP 工具接入层

- 统一工具协议连接外部系统
- 文件系统、GitHub、终端、浏览器、数据库等
- 基于 Agent 角色的权限控制

### 🎨 可视化协作工作区

- **像素工位**：工位表示 Agent 角色，像素小人表示当前 Worker
- **任务卡片流转**：任务在不同 Agent 之间流动
- **状态灯**：实时展示 Agent 工作状态
- **交接动画**：直观展示任务交接过程

## 核心差异化

| 特性 | ModelGate Agent Studio | 其他平台 |
|------|-----------------------|----------|
| 核心定位 | 多模型 Agent 协作工作台 | 单模型聊天 / API 聚合 |
| 调度逻辑 | 额度感知 + 任务级调度 | 手动切换 / 简单路由 |
| 任务连续性 | 结构化 Handoff 交接 | 会话中断即丢失 |
| 知识沉淀 | 自进化本地知识库 | 无记忆 / 简单聊天记录 |
| 可视化 | 像素工位 + 任务卡片流转 | 传统聊天界面 |
| 聚焦场景 | 开发者项目与长期任务 | 泛用问答 / 个人助理 |

## 产品架构

```text
┌─────────────────────────────────────────────────────────┐
│ 1. User Goal Layer                                       │
│    用户目标输入、约束、输出要求                           │
├─────────────────────────────────────────────────────────┤
│ 2. Router Layer                                          │
│    任务类型判断、复杂度评估、多 Agent 判断                │
├─────────────────────────────────────────────────────────┤
│ 3. Planning Layer                                        │
│    任务拆解、任务树生成、依赖设置、完成标准               │
├─────────────────────────────────────────────────────────┤
│ 4. Agent Station Layer                                   │
│    Planner / Coder / Reviewer / Researcher / Supervisor  │
├─────────────────────────────────────────────────────────┤
│ 5. Model Layer                                           │
│    Claude / GPT / DeepSeek / Kimi / GLM / MiniMax ...    │
├─────────────────────────────────────────────────────────┤
│ 6. Runtime Layer                                         │
│    Agent Harness、模型调用、工具调用、Handoff 判断        │
├─────────────────────────────────────────────────────────┤
│ 7. Tool Layer (MCP)                                      │
│    文件 / GitHub / Terminal / Browser / Database         │
├─────────────────────────────────────────────────────────┤
│ 8. Memory Layer                                          │
│    Raw / Session / Project / User / Agent / Skill        │
├─────────────────────────────────────────────────────────┤
│ 9. RAG Layer                                             │
│    Project / Conversation / Skill / Handoff RAG          │
├─────────────────────────────────────────────────────────┤
│ 10. Evolution Layer                                      │
│     Knowledge Evolution Agent、Skill Distiller           │
├─────────────────────────────────────────────────────────┤
│ 11. Visual Workspace Layer                               │
│     像素小人、工位、任务卡片、交接动画                    │
├─────────────────────────────────────────────────────────┤
│ 12. Observability Layer                                  │
│     调用日志、token 统计、额度状态、交接历史              │
└─────────────────────────────────────────────────────────┘
```

## 产品文档

| 文档 | 说明 |
|------|------|
| [01-产品概述.md](./01-产品概述.md) | 产品概述、定位、愿景 |
| [02-产品设计.md](./02-产品设计.md) | 核心功能、用户流程、页面结构、数据设计 |
| [03-技术架构与差异化.md](./03-技术架构与差异化.md) | 技术架构、自进化机制、差异化定位 |
| [ModelGate Agent Studio 产品定义文档 v1.md](./ModelGate%20Agent%20Studio%20产品定义文档%20v1.md) | 完整产品定义文档 |
| [ModelGate Agent Studio — Workspace 双视图页面设计方案 v1.md](./ModelGate%20Agent%20Studio%20—%20Workspace%20双视图页面设计方案%20v1.md) | Workspace 页面详细设计方案 |

## 项目亮点

1. **多模型 Agent 编排架构**：将不同模型组织为角色化 Agent 团队
2. **模型能力路由**：基于任务特性和额度状态的智能调度
3. **额度感知调度机制**：提前触发任务交接，避免任务中断
4. **结构化 Handoff Summary**：让任务交接可追溯、可复用
5. **六层 Memory 体系**：从原始记录到可复用 Skill 的完整记忆链
6. **自进化知识库机制**：每次任务都能沉淀为未来能力
7. **Skill Library**：代码审查、项目理解、Bug 修复等可复用技能
8. **MCP 工具接入层**：安全可控的外部工具调用
9. **RAG 检索增强**：任务开始前自动加载相关历史经验
10. **像素工位可视化**：将抽象的 Agent 协作过程直观呈现

## 核心价值

- **让多个模型不再只是被动调用，而是以不同 Agent 角色参与协作**
- **让不同模型根据自身擅长能力被分配到合适任务**
- **让复杂任务可以持续推进，而不是一次性问答**
- **让模型额度、上下文、任务状态可以被统一管理**
- **让模型可以换，但经验不能丢；让项目可以变，但方法可以继承**

## 本地运行

### 前置条件

- Python 3.9+
- Node.js 20+
- npm

### 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 编辑配置
.venv/bin/python -m uvicorn src.main:app --reload
```

### 前端

```bash
cd frontend
cp .env.example .env  # 编辑配置
npm install
npm run dev
```

访问 http://localhost:5173

### 切换 Provider

```bash
# 默认 Mock Provider（无需 API key）
export MODEL_PROVIDER=mock

# 真实 OpenAI-compatible Provider
export MODEL_PROVIDER=openai
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_API_KEY=sk-xxx
```

## Docker 一键启动

### 前置条件

- Docker
- Docker Compose

### 启动

```bash
# 1. 复制环境变量模板（可选，默认使用 Mock Provider）
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 2. 构建并启动
docker-compose up --build

# 3. 打开浏览器
open http://localhost
```

### 创建 Demo 数据

```bash
# 在容器内运行 seed 脚本
docker exec -it modelgate-backend python seed_demo_data.py
```

### 切换 Provider（Docker）

```bash
# Mock（默认）
MODEL_PROVIDER=mock docker-compose up

# 真实 OpenAI API
MODEL_PROVIDER=openai OPENAI_API_KEY=sk-xxx docker-compose up
```

### 停止

```bash
docker-compose down
# 保留数据库数据
docker-compose down -v
```

### 开发模式（代码热重载）

修改代码后自动刷新，无需手动重启：

```bash
docker-compose -f docker-compose.dev.yml up --build
```

| 模式 | 前端地址 | 后端地址 | 代码变更 |
|------|---------|---------|---------|
| 生产 | http://localhost | 内部 8000 | 需重新 build |
| 开发 | http://localhost:5173 | http://localhost:8000 | 自动热重载 |

## 当前开发状态

| 阶段 | 状态 | 后端 | 前端 | 总计 |
|------|------|------|------|------|
| MVP-A Control Plane | ✅ | 127 | 145 | 272 |
| MVP-B Runtime | ✅ | 37 | 0 | 37 |
| Supervisor Review | ✅ | 4 | 0 | 4 |
| Memory / Skill 自进化 | ✅ | 4 | 0 | 4 |
| **总计** | | **172** | **145** | **317** |

**执行链路：** Goal → Router → Quota → Worker → Mock/Real Model → Logs → Quota Record → Task/Agent Status → Handoff → Supervisor Review → Memory Drafts → Skill Drafts

**模块：** Agent Registry | Model Router | Quota Manager | Handoff Manager | Logs/Observability | Agent Workspace | Runtime Engine | Supervisor Review | Memory/Skill Evolution

## License

MIT License
