# ModelGate Agent Studio 产品定义文档 v1

## 1. 产品名称

**ModelGate Agent Studio**

中文名称可暂定为：

**ModelGate 多模型 Agent 协作平台**

## 2. 产品一句话定义

ModelGate Agent Studio 是一个面向多 AI Coding Plan 与多模型 API 用户的多模型 Agent 协作平台，支持根据用户目标自动拆解任务、分配给不同能力模型驱动的 Agent，并在持续工作过程中进行状态记录、额度感知调度、任务交接与结果整合。

## 3. 产品核心定位

ModelGate Agent Studio 不是普通 AI 聊天工具，也不是简单的多 API 聚合器，而是一个用于组织、调度和监督多个模型 Agent 协作完成复杂目标的工作台。

它的核心价值是：

1. 让多个模型不再只是被动调用，而是以不同 Agent 角色参与协作。
2. 让不同模型根据自身擅长能力被分配到合适任务。
3. 让复杂任务可以持续推进，而不是一次性问答。
4. 让模型额度、上下文、任务状态可以被统一管理。
5. 当某个模型额度不足或任务无法继续时，系统可以生成交接摘要，让其他 Agent 接手继续完成任务。
6. 用可视化工位和像素小人表达多 Agent 协作过程，让用户直观看到“哪个 Agent 正在做什么”。

## 4. 产品愿景

ModelGate Agent Studio 的长期目标是成为一个“AI 团队调度平台”。

用户不再需要手动判断该用哪个模型，也不需要反复复制粘贴上下文，而是只需要提出一个目标，系统就能自动完成：

* 任务理解
* 任务拆解
* 模型选择
* Agent 分工
* 多步执行
* 状态记录
* 额度监控
* 任务交接
* 最终汇总

最终形成一个可以持续工作的多模型 Agent 协作环境。

## 5. 目标用户

### 5.1 核心用户

1. 拥有多个 AI Coding Plan 的开发者
   例如同时使用 Claude Code、Codex、Cursor、DeepSeek、Kimi、GLM、MiniMax 等工具或 API 的用户。
2. 需要长期处理复杂任务的开发者
   例如开发项目、修复 bug、分析代码库、写技术文档、生成项目报告等。
3. 多模型重度使用者
   这类用户清楚不同模型有不同优势，但目前需要手动切换、手动分配任务、手动管理上下文。
4. AI 工具开发者或研究者
   关注 Agent、Multi-Agent、模型路由、任务编排、上下文压缩和工具调用机制。

### 5.2 次级用户

1. 学生开发者
   用于管理课程项目、作业分析、论文辅助、代码调试和报告生成。
2. 小团队开发者
   用于把复杂任务拆给不同 AI Agent 协助完成。
3. AI 产品经理或独立开发者
   用于验证不同模型在不同任务中的表现，并搭建 Agent 工作流。

## 6. 用户痛点

### 6.1 多模型资源分散

用户可能同时拥有多个模型计划或 API，但这些模型分散在不同平台中，缺乏统一管理和统一调度。

### 6.2 手动切换模型效率低

不同任务适合不同模型，但用户需要自己判断该用谁、复制粘贴上下文、切换平台，操作成本高。

### 6.3 长任务容易中断

复杂任务往往无法一次完成。模型上下文限制、额度限制、会话中断都会导致任务连续性下降。

### 6.4 模型额度不可控

使用 coding plan 时，模型可能因为时间窗口或额度限制突然不可用。用户无法提前规划交接，导致任务中断。

### 6.5 多 Agent 协作不可见

即使底层有多个 Agent 执行任务，用户也很难直观看到任务流转、谁在工作、谁完成了什么、谁正在等待。

### 6.6 缺少结构化交接机制

当一个模型无法继续工作时，当前任务状态、已完成内容、遇到的问题和下一步计划往往没有被结构化保存，导致接手模型需要重新理解上下文。

## 7. 产品核心解决方案

ModelGate Agent Studio 通过“多模型 + 多 Agent + 任务编排 + 可视化工位 + 额度感知交接”的方式解决上述问题。

### 7.1 多模型接入

平台支持接入多个模型和 Provider，包括但不限于：

* OpenAI
* Anthropic
* DeepSeek
* Kimi
* GLM
* MiniMax
* 火山引擎
* 其他兼容 OpenAI API 格式的模型服务

### 7.2 Agent 角色化

平台不直接把模型等同于 Agent，而是将 Agent 定义为：

模型能力 + 角色职责 + 工具权限 + 当前任务状态 + 执行上下文。

例如：

* Planner Agent：负责拆解任务
* Coder Agent：负责写代码
* Reviewer Agent：负责检查结果
* Research Agent：负责搜索与资料整理
* Summarizer Agent：负责上下文压缩与交接摘要
* Supervisor Agent：负责最终判断任务是否完成

### 7.3 模型能力路由

系统根据任务类型、复杂度、上下文长度、成本、速度和额度状态，自动选择合适模型或 Agent。

例如：

* 复杂规划任务优先交给 Claude 或 GPT
* 编码任务交给 Claude Code、Codex 或 DeepSeek Coder
* 长文本阅读交给 Kimi
* 图片理解任务交给 GLM 或视觉模型
* 低成本总结任务交给成本较低的模型

### 7.4 额度感知调度

平台记录每个模型的使用状态，包括：

* 当前任务数
* 最近调用时间
* token 使用量
* 请求次数
* 预估剩余额度
* 是否接近使用限制
* 是否处于冷却期

当系统判断某个模型额度不足时，可以提前触发任务交接流程。

### 7.5 任务交接机制

当某个 Agent 无法继续工作时，平台自动生成 Handoff Summary，内容包括：

* 原始目标
* 当前任务状态
* 已完成内容
* 当前未完成内容
* 关键约束
* 相关文件或上下文
* 已做出的决策
* 遇到的问题
* 下一步建议
* 需要接手 Agent 注意的事项

接手 Agent 加载该交接摘要后，可以继续执行任务。

### 7.6 可视化 Agent 工位

平台使用“AI 办公室 / 像素工位”的视觉隐喻表达 Agent 协作过程：

* 工位代表 Agent 角色
* 像素小人代表当前执行者
* 小人工牌显示绑定模型
* 任务卡片在不同工位之间流转
* 额度不足时触发交接动画
* 交接时显示任务文件夹或交接单
* Supervisor 工位负责最终验收

## 8. 核心概念定义

### 8.1 Goal

Goal 是用户输入的最终目标。

例如：

“帮我把 ModelGate 做成一个多模型 Agent 协作平台。”

Goal 是整个系统运行的起点。

### 8.2 Task

Task 是从 Goal 中拆解出来的具体任务。

例如：

* 设计 Agent 数据结构
* 实现任务调度器
* 实现模型路由逻辑
* 实现前端工位视图
* 实现任务交接摘要
* 测试整体流程

### 8.3 Agent Station

Agent Station 指一个固定职责的 Agent 工位。

例如：

* Planner Station
* Coder Station
* Reviewer Station
* Research Station
* Summarizer Station
* Supervisor Station

Agent Station 更像是岗位，不等同于具体模型。

### 8.4 Worker

Worker 是当前在某个工位上执行任务的工作实例。

一个 Worker 可以由某个模型驱动。

例如：

Claude Worker 当前坐在 Planner Station 上进行任务拆解。

### 8.5 Model

Model 是底层能力来源。

例如：

* Claude
* GPT
* DeepSeek
* Kimi
* GLM
* MiniMax

模型本身不是 Agent。只有当模型被绑定到某个角色、任务、工具和状态时，才成为 Agent 执行者的一部分。

### 8.6 Handoff

Handoff 是任务交接过程。

当一个 Worker 不能继续工作时，系统生成交接摘要，并将任务状态转移给另一个 Worker。

### 8.7 Supervisor

Supervisor 是监督 Agent，负责判断：

* 任务是否完成
* 输出是否符合目标
* 是否存在遗漏
* 是否需要返工
* 是否需要调用新的 Agent

## 9. 产品核心模块

### 9.1 Goal Input 模块

用户输入目标，系统记录目标内容、任务类型、期望输出和约束条件。

功能包括：

* 输入目标
* 选择任务模式
* 设置优先级
* 设置是否允许多 Agent 协作
* 设置是否允许自动切换模型
* 设置是否允许自动执行工具

### 9.2 Router Agent 模块

Router Agent 负责分析用户目标，并判断应该如何处理。

功能包括：

* 判断任务类型
* 判断任务复杂度
* 判断是否需要多 Agent
* 判断是否需要工具
* 判断适合的模型类型
* 生成初始任务分配方案

### 9.3 Planner Agent 模块

Planner Agent 负责将 Goal 拆解成多个 Task。

功能包括：

* 任务拆解
* 子任务排序
* 依赖关系判断
* 任务优先级设定
* 任务完成标准定义

### 9.4 Agent Registry 模块

Agent Registry 用于管理平台中的所有 Agent 角色和 Worker。

功能包括：

* 创建 Agent Station
* 配置 Agent 职责
* 绑定默认模型
* 设置可用工具
* 设置优先使用模型
* 设置备用模型
* 设置上下文长度偏好
* 设置成本和速度偏好

### 9.5 Model Router 模块

Model Router 用于根据任务需求选择模型。

功能包括：

* 根据任务类型选择模型
* 根据模型能力选择模型
* 根据额度状态选择模型
* 根据成本选择模型
* 根据上下文长度选择模型
* 根据用户偏好选择模型

### 9.6 Agent Runtime 模块

Agent Runtime 是 Agent 执行任务的核心运行环境。

功能包括：

* 加载任务
* 加载上下文
* 调用模型
* 调用工具
* 保存执行记录
* 更新任务状态
* 输出中间结果
* 判断是否继续执行

### 9.7 Quota Manager 模块

Quota Manager 用于管理不同模型的额度与使用情况。

功能包括：

* 记录模型使用次数
* 记录 token 使用量
* 记录调用时间
* 记录错误和限额提示
* 预估剩余额度
* 判断是否接近额度限制
* 触发交接或切换模型

### 9.8 Handoff Manager 模块

Handoff Manager 负责生成和执行任务交接。

功能包括：

* 检测是否需要交接
* 生成交接摘要
* 保存当前上下文
* 选择接手 Agent
* 将任务状态传递给接手 Agent
* 记录交接历史

### 9.9 Supervisor 模块

Supervisor 负责检查任务最终结果。

功能包括：

* 检查任务是否完成
* 检查输出质量
* 检查是否符合约束
* 检查是否需要补充任务
* 决定是否结束整个 Goal
* 生成最终报告

### 9.10 Visual Workspace 模块

Visual Workspace 是用户看到的可视化工作区。

功能包括：

* 展示 Agent 工位
* 展示像素小人
* 展示当前工作状态
* 展示任务流转
* 展示交接动画
* 展示模型额度状态
* 展示任务完成进度

## 10. 可视化设计原则

### 10.1 工位代表 Agent 角色

每个工位不是模型，而是一个 Agent 职责。

例如：

* 规划工位
* 编码工位
* 审查工位
* 搜索工位
* 总结工位
* 监督工位

### 10.2 像素小人代表当前 Worker

像素小人是当前被派驻到该工位的执行者。

小人头顶或工牌显示模型名称，例如：

* Claude
* GPT
* DeepSeek
* Kimi
* GLM

### 10.3 任务以卡片形式流转

用户目标被拆成多个任务卡片。任务卡片可以在不同工位之间流动。

### 10.4 交接以文件夹形式表达

当某个模型额度不足或任务需要转移时，像素小人将任务文件夹交给另一个小人，代表上下文交接。

### 10.5 状态灯表达工作状态

每个工位可以有状态灯：

* 灰色：空闲
* 蓝色：工作中
* 黄色：等待或额度不足
* 红色：出错
* 绿色：完成
* 紫色：交接中

## 11. 核心用户流程

### 11.1 标准任务流程

1. 用户输入一个 Goal。
2. Router Agent 分析任务类型。
3. Planner Agent 拆解任务。
4. 系统生成任务树。
5. Model Router 为每个任务选择合适模型。
6. 不同 Agent Station 被激活。
7. 对应 Worker 进入工位开始工作。
8. 各 Agent 输出中间结果。
9. Supervisor 检查结果。
10. 如有问题，任务返回对应工位修正。
11. 如无问题，系统生成最终结果。

### 11.2 额度不足交接流程

1. 某个 Worker 正在执行任务。
2. Quota Manager 检测到模型额度接近限制。
3. 系统暂停新任务分配。
4. Handoff Manager 生成交接摘要。
5. 当前 Worker 将任务文件夹交给接手 Worker。
6. 接手 Worker 加载交接摘要和任务上下文。
7. 接手 Worker 继续执行任务。
8. 系统记录交接历史。

### 11.3 问题路由流程

1. 用户输入一个问题。
2. Router Agent 判断问题类型。
3. 系统判断是否需要直接回答、单 Agent 处理或多 Agent 协作。
4. 如果是简单问题，交给最合适模型直接回答。
5. 如果是复杂问题，拆成多个子任务。
6. 多个 Agent 分别处理。
7. Supervisor 整合最终答案。

## 12. MVP 功能范围

### 12.1 MVP 必须包含

1. 多模型 API 接入
2. 模型能力标签管理
3. Agent 角色配置
4. 用户 Goal 输入
5. 简单 Router Agent
6. 简单任务拆解
7. 任务分配给不同 Agent
8. Agent 执行状态记录
9. 基础 Handoff Summary 生成
10. 模型使用记录
11. 基础工位可视化页面
12. 最终结果汇总

### 12.2 MVP 可以暂缓

1. 复杂动画
2. 完整像素办公室
3. 多人协作账号系统
4. 自动读取所有 coding plan 的真实额度
5. 高级工具调用
6. 自动修改本地项目文件
7. 完整插件市场
8. 复杂工作流编辑器

### 12.3 MVP 不做

1. 不做普通 ChatGPT 克隆
2. 不做单纯 API Key 管理工具
3. 不做只展示模型列表的工具
4. 不做没有任务状态的聊天集合
5. 不做无 Agent 逻辑的纯动画界面

## 13. 页面结构

### 13.1 Dashboard 首页

展示：

* 当前活跃 Goal
* 正在工作的 Agent
* 模型额度概览
* 最近任务
* 最近交接记录
* 成功完成的任务数

### 13.2 Agent Workspace 工作区

核心页面。

包括：

* 左侧 Goal 输入区
* 中间可视化工位区
* 右侧任务详情区
* 底部执行日志区

### 13.3 Agent Registry 页面

用于管理 Agent。

包括：

* Agent 名称
* Agent 职责
* 默认模型
* 备用模型
* 可用工具
* 输出格式要求
* 最大执行步数
* 是否允许交接

### 13.4 Models 页面

用于管理模型和 Provider。

包括：

* Provider 名称
* API Key 状态
* 模型列表
* 模型能力标签
* 成本信息
* 上下文长度
* 是否支持视觉
* 是否支持代码
* 是否支持工具调用

### 13.5 Quota 页面

用于查看使用量与额度。

包括：

* 每个模型调用次数
* token 使用量
* 最近使用时间
* 预估剩余额度
* 限额状态
* 交接触发记录

### 13.6 Handoff 页面

用于查看交接历史。

包括：

* 原 Agent
* 接手 Agent
* 交接原因
* 交接摘要
* 交接时间
* 接手后结果

### 13.7 Logs 页面

用于查看详细执行日志。

包括：

* 每次模型调用
* 输入内容
* 输出内容
* 错误信息
* 工具调用
* 任务状态变化

## 14. 数据对象设计

### 14.1 Model

字段示例：

* model_id
* provider
* model_name
* capability_tags
* context_window
* cost_level
* speed_level
* supports_vision
* supports_code
* supports_tool_calling
* quota_status

### 14.2 AgentStation

字段示例：

* agent_id
* agent_name
* role
* description
* default_model_id
* backup_model_ids
* allowed_tools
* system_prompt
* output_format
* max_steps
* handoff_enabled

### 14.3 WorkerSession

字段示例：

* worker_id
* agent_id
* model_id
* goal_id
* task_id
* status
* started_at
* ended_at
* current_context
* execution_logs

### 14.4 Goal

字段示例：

* goal_id
* title
* original_prompt
* user_constraints
* status
* created_at
* completed_at
* final_output

### 14.5 Task

字段示例：

* task_id
* goal_id
* parent_task_id
* title
* description
* assigned_agent_id
* status
* priority
* dependencies
* output
* completion_criteria

### 14.6 HandoffRecord

字段示例：

* handoff_id
* goal_id
* task_id
* from_agent_id
* from_model_id
* to_agent_id
* to_model_id
* reason
* handoff_summary
* created_at
* result_after_handoff

## 15. 核心差异化

### 15.1 多模型不是简单切换，而是任务级调度

平台不是让用户手动选模型，而是根据任务自动判断最合适的模型和 Agent。

### 15.2 Agent 不是聊天角色，而是可执行工作单元

每个 Agent 有职责、工具、状态、任务和输出要求。

### 15.3 支持任务交接

当模型额度不足、任务超时或质量不足时，平台可以将任务交接给其他 Agent。

### 15.4 支持持续性工作

平台保存目标、任务、上下文、执行记录和交接历史，让复杂任务可以持续推进。

### 15.5 可视化表达 Agent 协作

通过像素小人和工位，让用户直观看到 AI 团队如何协作。

## 16. 产品边界

### 16.1 当前阶段重点

当前阶段重点不是做一个万能 Agent，而是先做一个清晰可控的多模型 Agent 协作工作台。

优先解决：

* 多模型接入
* Agent 角色管理
* 任务分配
* 状态记录
* 交接摘要
* 可视化表达

### 16.2 当前阶段不追求

当前阶段不追求：

* 完全自动化开发大型项目
* 完全无人监督
* 完全准确读取所有第三方 coding plan 额度
* 复杂插件生态
* 企业级权限管理
* 大规模团队协作

## 17. 成功指标

### 17.1 功能指标

1. 用户可以创建一个 Goal。
2. 系统可以自动拆解至少 3 个子任务。
3. 系统可以将不同任务分配给不同 Agent。
4. 每个 Agent 的执行过程可以被记录。
5. 系统可以生成 Handoff Summary。
6. 接手 Agent 可以基于 Handoff Summary 继续工作。
7. 用户可以在可视化工作区看到 Agent 状态变化。

### 17.2 体验指标

1. 用户能在 1 分钟内理解当前有哪些 Agent 正在工作。
2. 用户能清楚看到任务当前进度。
3. 用户能看懂为什么某个任务被交给某个模型。
4. 用户能看懂为什么发生交接。
5. 用户能查看每次交接前后的上下文变化。

### 17.3 产品指标

1. 多模型调用效率提升。
2. 用户手动复制粘贴上下文次数减少。
3. 长任务中断率降低。
4. 模型额度使用更加可控。
5. 用户对不同模型能力的利用率提高。

## 18. 产品口号（v1 阶段）

### 中文口号

让多个 AI 像团队一样协作。

### 英文口号

Turn multiple AI models into one coordinated agent team.

## 19. 项目简介版本

ModelGate Agent Studio 是一个多模型 Agent 协作平台，面向拥有多个 AI Coding Plan 和 API 资源的开发者。平台能够根据用户目标自动拆解任务，将任务分配给不同能力模型驱动的 Agent，并通过状态记录、额度感知调度和任务交接机制，实现复杂任务的持续推进。产品使用可视化工位和像素小人呈现 Agent 协作过程，让用户直观看到每个 Agent 的职责、状态、进度和交接行为。

## 20. 自进化扩展目标

本次扩展主要补充 ModelGate Agent Studio 在原有“多模型 Agent 协作平台”定位上的进一步进化方向。

原始产品定位是：

> ModelGate Agent Studio 是一个面向多 AI Coding Plan 与多模型 API 用户的多模型 Agent 协作平台，支持根据用户目标自动拆解任务、分配给不同能力模型驱动的 Agent，并在持续工作过程中进行状态记录、额度感知调度、任务交接与结果整合。

本次扩展后，产品将进一步加入：

1. 自进化 Memory 机制
2. 本地知识库机制
3. Skill 自动沉淀机制
4. MCP 工具接入层
5. RAG 项目检索层
6. Agent Runtime / Harness
7. 多模型长期协作经验积累
8. 与 OpenClaw、Hermes Agent、Dify、CrewAI、LangGraph 等成熟平台的差异化定位

最终目标是让 ModelGate Agent Studio 不只是一个“多模型调用平台”，而是一个能够在使用过程中不断积累经验、沉淀知识、优化流程的本地化多模型 Agent 协作系统。

## 21. 自进化阶段核心定位

ModelGate Agent Studio 的新定位可以升级为：

> 一个面向开发者的多模型 Agent 协作与自进化知识平台。它能够将不同 AI 模型组织成协作式 Agent 团队，并在每次任务执行后，把上下文、经验、错误、解决方案和流程方法沉淀为本地知识库与可复用 Skill，使未来接入的任何模型都能读取这些知识，并持续优化项目完成流程。

更简洁的定义：

> ModelGate Agent Studio 是一个能让多个 AI 模型像开发团队一样分工、接班、记忆和进化的本地 Agent 工作台。

## 22. 核心概念：自进化知识库

### 22.1 什么是自进化知识库

自进化知识库不是普通的聊天记录保存，也不是简单的 RAG 文档库。

它的核心逻辑是：

> 每一次用户与 Agent 的交互、每一次项目执行、每一次错误修复、每一次任务交接，都可以被系统整理成可复用的经验、规则、流程、偏好或 Skill，并写入本地知识库。

也就是说，平台会从每次任务中提炼出：

* 用户偏好
* 项目经验
* 技术决策
* 常见错误
* 解决方案
* Agent 分工经验
* 模型选择经验
* 交接经验
* 可复用工作流
* 可复用 Skill

这些内容会被保存到本地知识库中。未来无论用户接入 Claude、GPT、DeepSeek、Kimi、GLM、MiniMax 或其他模型，只要模型能够读取本地知识库，就可以继承之前积累的经验。

### 22.2 为什么这个机制重要

普通 AI 工具的问题是：

1. 每次新会话都像重新开始。
2. 用户要反复解释自己的项目。
3. 用户要反复告诉模型自己的偏好。
4. 模型无法系统性积累经验。
5. 旧项目经验很难迁移到新项目。
6. 换模型后，之前积累的上下文和经验容易丢失。

自进化知识库要解决的问题是：

> 让模型可以换，但经验不能丢。
> 让项目可以变，但方法可以继承。
> 让每一次任务都不是一次性消耗，而是能沉淀为未来能力的一部分。

## 23. 自进化机制的核心流程

每次完成一次任务后，系统不应该只是保存聊天记录，而应该启动一次“经验整理流程”。

### 23.1 标准流程

```text
用户提出目标
↓
Agent 协作完成任务
↓
系统保存完整上下文
↓
Memory Curator Agent 分析本次任务
↓
提取经验、偏好、错误、流程、决策
↓
判断是否可以形成 Skill
↓
写入本地知识库
↓
未来任务中通过 RAG 或 Memory 检索调用
```

### 23.2 任务结束后应自动提取的内容

每次任务结束后，系统可以自动生成以下内容：

1. 本次任务目标
2. 最终完成结果
3. 任务拆解方式
4. 哪些 Agent 被调用
5. 哪些模型表现较好
6. 哪些模型表现一般
7. 哪些工具被使用
8. 遇到了哪些错误
9. 错误是如何解决的
10. 哪些步骤可以复用
11. 哪些提示词效果较好
12. 哪些流程可以变成 Skill
13. 哪些信息应该写入项目记忆
14. 哪些信息应该写入用户偏好
15. 哪些信息应该写入模型路由规则
16. 哪些信息应该写入交接规则

## 24. Memory 分层设计

为了避免记忆混乱，Memory 不能只做成一个大数据库。建议分成六层。

### 24.1 Raw Memory：原始记忆

保存最原始的数据。

包括：

* 原始聊天记录
* Agent 输出
* 工具调用日志
* 文件修改记录
* 任务执行记录
* 错误日志
* Handoff 记录

Raw Memory 的作用是保留完整证据，但不直接作为高质量知识使用。

### 24.2 Session Memory：会话记忆

保存当前任务或当前会话中需要持续使用的信息。

包括：

* 当前 Goal
* 当前 Task
* 当前任务树
* 当前 Agent 状态
* 当前上下文摘要
* 当前未完成事项

Session Memory 用于支持当前任务不中断。

### 24.3 Project Memory：项目记忆

保存某个项目长期有效的信息。

例如：

* 项目名称
* 技术栈
* 目录结构
* 启动方式
* API 设计
* 数据库设计
* UI 偏好
* 已做过的功能
* 已否定的方案
* 重要设计决策
* 常见 bug 和修复方式

对于 ModelGate 项目，Project Memory 可以保存：

* 前端使用 Next.js / TypeScript
* 后端使用 FastAPI
* 项目定位是多模型 Agent 协作平台
* 不做普通 ChatGPT clone
* 偏好低饱和、非深色、类 Claude 的 UI 风格
* 视觉方向是像素小人和 Agent 工位
* 核心差异化是额度感知调度和任务交接

### 24.4 User Memory：用户偏好记忆

保存用户长期稳定的偏好。

例如：

* 用户喜欢直接、详细、可落地的分析
* 用户更重视项目能否用于实习展示
* 用户喜欢把复杂概念整理成文档
* 用户偏好中文解释
* 用户关注 AI 应用、Agent、多模型协作、全栈项目
* 用户希望项目有差异化，而不是普通 API 聚合器

User Memory 的作用是让未来任何模型接入后，都能快速理解用户偏好。

### 24.5 Agent Memory：Agent 工作记忆

保存不同 Agent 的工作经验。

例如：

* Coder Agent 擅长哪些类型任务
* Reviewer Agent 常发现哪些问题
* Planner Agent 的拆解方式是否有效
* Research Agent 检索效果如何
* Summarizer Agent 生成的交接摘要是否足够清晰
* 某个模型在某类任务中的表现如何

Agent Memory 的作用是让 Agent 不断变得更稳定。

### 24.6 Skill Memory：技能记忆

保存从经验中沉淀出来的可复用技能。

例如：

* Code Review Skill
* Bug Fix Skill
* Handoff Skill
* Project Onboarding Skill
* UI Optimization Skill
* API Integration Skill
* Report Writing Skill
* Reference Checking Skill
* Rubric Grading Skill

Skill Memory 是自进化机制的核心产物之一。

## 25. Skill 机制设计

### 25.1 Skill 的定义

在 ModelGate Agent Studio 中，Skill 指的是：

> 从历史任务中沉淀出来的可复用任务执行方法。

Skill 不是模型本身，也不是单纯的 prompt，而是一个结构化的任务执行模板。

一个 Skill 应该包含：

1. Skill 名称
2. 适用场景
3. 输入要求
4. 执行步骤
5. 推荐 Agent
6. 推荐模型
7. 可用工具
8. 输出格式
9. 成功标准
10. 历史成功案例
11. 常见失败原因
12. 注意事项
13. 版本记录

### 25.2 Skill 示例：Handoff Skill

```text
Skill 名称：
Handoff Summary Skill

适用场景：
当某个模型额度不足、任务中断、需要切换 Agent 或需要长期任务续接时使用。

输入：
- 当前 Goal
- 当前 Task
- 已完成内容
- 未完成内容
- Agent 执行记录
- 工具调用记录
- 错误日志
- 当前约束

执行步骤：
1. 总结原始目标
2. 总结当前进度
3. 列出已完成内容
4. 列出未完成内容
5. 提取关键约束
6. 总结已经做出的决策
7. 标记当前风险
8. 给出接手 Agent 的下一步建议

输出：
结构化 Handoff Summary

成功标准：
接手 Agent 读取后可以不重新询问用户，直接继续任务。
```

### 25.3 Skill 示例：Project Onboarding Skill

```text
Skill 名称：
Project Onboarding Skill

适用场景：
当 Agent 第一次接触一个项目，或需要快速恢复项目上下文时使用。

输入：
- 项目目录
- README
- package.json
- 后端入口文件
- 前端页面结构
- 历史项目记忆

执行步骤：
1. 分析项目定位
2. 识别技术栈
3. 梳理目录结构
4. 找出核心模块
5. 总结启动方式
6. 总结开发注意事项
7. 写入 Project Memory

输出：
项目理解报告

成功标准：
新的 Agent 可以基于报告快速理解项目。
```

### 25.4 Skill 示例：Code Review Skill

```text
Skill 名称：
Code Review Skill

适用场景：
检查代码修改、PR、bug 修复或功能实现质量。

输入：
- 修改文件
- diff
- 相关需求
- 项目规范
- 测试结果

执行步骤：
1. 理解需求
2. 检查逻辑正确性
3. 检查类型问题
4. 检查安全风险
5. 检查代码风格
6. 检查是否影响已有功能
7. 给出修改建议

输出：
代码审查报告

成功标准：
报告指出具体问题、位置、原因和修复建议。
```

### 25.5 Skill 生成方式

Skill 可以通过三种方式生成：

#### 方式一：手动创建

用户或开发者手动定义 Skill。

适合早期 MVP。

#### 方式二：任务后自动建议

任务完成后，系统自动判断是否值得生成 Skill，并询问用户是否保存。

例如：

“本次任务中形成了一个可复用的 UI 优化流程，是否保存为 Skill？”

#### 方式三：自动沉淀

系统在高置信度情况下自动保存 Skill 草稿，但需要用户审核后启用。

推荐早期使用“自动建议 + 用户确认”的方式，避免知识库污染。

## 26. Knowledge Evolution Agent 设计

为了实现自进化，需要引入一个新的核心 Agent：

> Knowledge Evolution Agent

也可以叫：

* Memory Curator Agent
* Skill Distiller Agent
* Experience Extractor Agent

### 26.1 作用

Knowledge Evolution Agent 负责在任务结束后，对本次任务进行复盘和知识提炼。

它不是直接完成用户任务的 Agent，而是负责让系统变得更聪明。

### 26.2 输入

* 本次 Goal
* 任务树
* Agent 执行记录
* 模型调用记录
* 工具调用记录
* Handoff 记录
* 最终输出
* 用户反馈
* 错误日志

### 26.3 输出

* 新增 Project Memory
* 新增 User Memory
* 新增 Agent Memory
* 新增 Skill 草稿
* 新增模型路由规则
* 新增交接规则
* 新增失败案例
* 新增优化建议

### 26.4 工作流程

```text
任务完成
↓
Knowledge Evolution Agent 读取任务全过程
↓
识别可沉淀信息
↓
区分事实、偏好、流程、错误、Skill
↓
生成结构化记忆
↓
判断是否需要用户确认
↓
写入本地知识库
↓
未来任务中被 RAG 和 Memory 调用
```

## 27. 本地知识库设计

### 27.1 本地知识库的定位

本地知识库是 ModelGate Agent Studio 的长期大脑。

它不依赖某一个模型。无论未来用户接入哪个模型，只要该模型能读取知识库，就可以继承之前积累的经验。

这意味着：

> 模型可以换，知识库不换。
> API 可以换，项目经验不丢。
> Agent 可以换，工作方法保留。

### 27.2 本地知识库内容分类

本地知识库可以分成以下几类：

1. 用户偏好库
2. 项目经验库
3. 任务历史库
4. Agent 表现库
5. Skill 库
6. Handoff 库
7. 工具使用经验库
8. 模型路由经验库
9. 错误与修复库
10. Prompt 模板库

### 27.3 本地知识库的数据形式

每条知识可以包含：

* id
* type
* title
* content
* tags
* source_task_id
* source_agent_id
* confidence
* created_at
* updated_at
* usage_count
* last_used_at
* related_project
* related_skill
* embedding
* human_approved

### 27.4 知识类型示例

```text
type: user_preference
content: 用户偏好低饱和、非深色、类 Claude 的 UI 风格。

type: project_decision
content: ModelGate 不做普通 ChatGPT clone，而是定位为多模型 Agent 协作平台。

type: workflow_experience
content: 多模型任务应先由 Router Agent 判断复杂度，再决定使用单 Agent、Router + One Agent 或 Multi-Agent 模式。

type: model_routing_rule
content: 长文档理解任务优先考虑 Kimi Reader Agent，复杂架构设计任务优先考虑 Claude Architect Agent。

type: handoff_rule
content: 当模型额度接近限制时，必须先生成结构化 Handoff Summary，再转交给备用模型。
```

## 28. RAG 与 Memory 的关系

### 28.1 RAG 的作用

RAG 负责“从知识库中检索相关信息”。

Memory 负责“保存和组织经验”。

二者关系是：

```text
Memory 负责存
RAG 负责找
Agent 负责用
Skill 负责复用
```

### 28.2 Agent 工作时的知识调用流程

```text
用户输入新任务
↓
Router Agent 分析任务类型
↓
RAG 检索相关 Project Memory / User Memory / Skill Memory
↓
Planner Agent 基于历史经验拆任务
↓
Model Router 根据历史表现选择模型
↓
Agent 执行任务
↓
任务结束后 Knowledge Evolution Agent 继续沉淀经验
```

### 28.3 RAG 检索范围

不同任务应检索不同知识库。

#### 新项目任务

检索：

* User Memory
* Skill Memory
* 通用项目经验
* 模型路由经验

#### 老项目任务

检索：

* Project Memory
* 任务历史
* 文件修改记录
* 错误修复记录
* Handoff 记录

#### 代码任务

检索：

* Project RAG
* Code Review Skill
* Debug Skill
* 相关代码文件
* 历史 bug 记录

#### 文档任务

检索：

* Writing Skill
* 用户写作偏好
* 历史文档模板
* 项目背景资料

## 29. MCP 在平台中的设计

### 29.1 MCP 的定位

MCP 是工具连接层。

它负责让 Agent 连接外部系统，例如：

* 文件系统
* GitHub
* 数据库
* 浏览器
* 日历
* 邮件
* Notion
* Slack
* 终端
* 本地项目目录

在 ModelGate Agent Studio 中，MCP 应作为 Tool Layer 的核心协议。

### 29.2 MCP 模块设计

平台应包含：

1. MCP Server Registry
2. MCP Client
3. Tool Permission Policy
4. Tool Call Logs
5. Tool Approval Flow
6. Tool Sandbox
7. Tool Presets

### 29.3 MCP 权限设计

不同 Agent 只能访问与自己职责相关的工具。

例如：

#### Coder Agent

允许：

* 读取文件
* 修改代码
* 运行测试
* 查看 git diff

不默认允许：

* 删除项目
* 访问用户隐私目录
* 执行高风险 shell 命令

#### Research Agent

允许：

* 搜索网页
* 读取 PDF
* 查询知识库

不默认允许：

* 修改本地文件
* 发送邮件
* 执行命令

#### Supervisor Agent

允许：

* 查看所有 Agent 输出
* 查看测试结果
* 查看 Handoff 记录

不默认允许：

* 直接改代码
* 直接执行系统命令

## 30. Agent Runtime / Harness 设计

### 30.1 Agent Runtime 的作用

Agent Runtime 是 Agent 真正运行的地方。

它负责：

* 加载 Agent 配置
* 加载模型
* 加载上下文
* 加载 Memory
* 加载 Tools
* 执行任务
* 调用模型
* 调用工具
* 保存日志
* 处理错误
* 判断是否需要 Handoff
* 判断是否需要 Supervisor 审查

### 30.2 Runtime 标准流程

```text
接收 Task
↓
加载 Agent Profile
↓
读取相关 Memory / RAG
↓
选择模型
↓
选择工具
↓
执行模型调用
↓
执行工具调用
↓
保存中间结果
↓
判断是否完成
↓
未完成则继续
↓
额度不足则 Handoff
↓
完成后进入 Supervisor 审查
```

### 30.3 Runtime 需要记录的内容

* task_id
* agent_id
* model_id
* prompt
* retrieved_memory
* tool_calls
* intermediate_outputs
* errors
* token_usage
* quota_status
* handoff_status
* final_output

## 31. 与成熟平台的差异化定位

### 31.1 不直接对标 OpenClaw

OpenClaw 更偏个人助理、本地自动化和外部服务操作。

ModelGate Agent Studio 不应该一开始去做：

* 邮件管理
* 日历管理
* 航班值机
* 全设备控制
* 高权限个人助理

这些方向会增加安全复杂度，也容易与成熟平台正面竞争。

ModelGate Agent Studio 应聚焦：

* 多模型开发任务
* 多 Agent 协作
* Coding Plan 额度调度
* 项目记忆
* 任务交接
* 开发流程沉淀
* 本地知识库自进化

### 31.2 不直接复制 Hermes Agent

Hermes Agent 的强项是记忆、自进化、skills 和长期用户模型。

ModelGate Agent Studio 可以借鉴这个机制，但不应只做一个“会记忆的个人 Agent”。

更适合的方向是：

> 把自进化机制应用在多模型 Agent 协作和开发项目完成流程上。

也就是说，ModelGate 的自进化不是为了让一个 Agent 变聪明，而是为了让整个多模型 Agent 团队变得更会协作。

### 31.3 不做普通 Dify 类 Workflow Builder

Dify 这类平台已经在 workflow、RAG、Agent 应用构建上很成熟。

ModelGate Agent Studio 不应只做节点画布，而应强调：

* AI 工位
* 像素 Worker
* Agent 协作状态
* 任务卡片流转
* 模型额度调度
* Agent 接班交接
* 本地知识库进化

### 31.4 不做纯 AutoGen / CrewAI 框架包装

AutoGen、CrewAI 这类框架偏开发者编排框架。

ModelGate Agent Studio 应做成更产品化的工作台：

* 用户可以看到 Agent 怎么协作
* 用户可以看到模型怎么被调度
* 用户可以看到交接怎么发生
* 用户可以看到知识怎么沉淀
* 用户可以手动管理 Skill 和 Memory

## 32. 核心优势总结

ModelGate Agent Studio 的优势可以总结为六点。

### 32.1 多模型资源调度优势

面向拥有多个模型 API 或 Coding Plan 的用户，帮助用户把分散的模型资源组织成一个协作团队。

### 32.2 额度感知优势

不是简单记录 token，而是围绕“模型额度快用完时如何不中断任务”设计调度和交接机制。

### 32.3 任务交接优势

把 Handoff 做成核心能力，而不是附属功能。

### 32.4 自进化知识库优势

每次任务都能沉淀经验，未来所有模型都能读取这些知识继续优化工作流程。

### 32.5 可视化协作优势

通过像素小人、工位、任务卡片、交接动画，让多 Agent 协作过程变得直观。

### 32.6 开发者场景聚焦优势

不做泛个人助理，而是聚焦开发项目、代码任务、文档生成、项目理解和长期任务推进。

## 33. 产品架构综合版

```text
ModelGate Agent Studio

1. User Goal Layer
- 用户输入目标
- 用户约束
- 输出要求

2. Router Layer
- 判断任务类型
- 判断复杂度
- 判断是否需要多 Agent
- 判断是否需要工具

3. Planning Layer
- 拆解任务
- 生成任务树
- 设置任务依赖
- 设置完成标准

4. Agent Station Layer
- Planner Station
- Coder Station
- Reviewer Station
- Research Station
- Summarizer Station
- Supervisor Station
- Knowledge Evolution Station

5. Model Layer
- Claude
- GPT
- DeepSeek
- Kimi
- GLM
- MiniMax
- 其他兼容 API 模型

6. Runtime Layer
- Agent Harness
- 模型调用
- 工具调用
- 状态保存
- 错误处理
- Handoff 判断

7. Tool Layer
- MCP Client
- MCP Server Registry
- 本地文件
- GitHub
- Terminal
- Browser
- Database
- API tools

8. Memory Layer
- Raw Memory
- Session Memory
- Project Memory
- User Memory
- Agent Memory
- Skill Memory
- Handoff Memory

9. RAG Layer
- Project RAG
- Conversation RAG
- Skill RAG
- Handoff RAG
- Error Fix RAG

10. Evolution Layer
- Knowledge Evolution Agent
- Skill Distiller
- Memory Curator
- Experience Extractor

11. Visual Workspace Layer
- 像素小人
- Agent 工位
- 任务卡片
- 状态灯
- 交接动画
- 知识沉淀提示

12. Observability Layer
- 调用日志
- token 统计
- 额度状态
- 工具调用记录
- Agent 输出记录
- 交接历史
- Skill 使用记录
```

## 34. 新增页面

### 34.1 Knowledge Base 页面

用于查看和管理本地知识库。

功能包括：

* 查看用户记忆
* 查看项目记忆
* 查看 Agent 记忆
* 查看错误修复记录
* 查看历史经验
* 编辑或删除错误记忆
* 手动添加知识
* 审核系统自动生成的知识

### 34.2 Skill Library 页面

用于管理 Skill。

功能包括：

* 查看已有 Skill
* 新建 Skill
* 编辑 Skill
* 启用 / 禁用 Skill
* 查看 Skill 使用次数
* 查看 Skill 成功率
* 查看 Skill 版本
* 查看由任务自动生成的 Skill 草稿

### 34.3 Evolution Review 页面

用于审核系统从任务中提取出来的新知识。

功能包括：

* 查看本次任务可沉淀内容
* 确认写入 User Memory
* 确认写入 Project Memory
* 确认保存为 Skill
* 拒绝无用内容
* 修改内容后保存

### 34.4 Handoff Memory 页面

用于查看所有任务交接记录。

功能包括：

* 查看交接原因
* 查看交接前状态
* 查看交接摘要
* 查看接手模型
* 查看接手后是否成功
* 将成功交接经验保存为 Handoff Skill

### 34.5 Model Performance 页面

用于记录不同模型在不同任务中的表现。

功能包括：

* 模型任务成功率
* 模型适合的任务类型
* 模型失败案例
* 平均响应速度
* 平均成本
* 平均上下文保持能力
* 用户手动评分
* 系统自动评价

## 35. 用户流程：任务后的知识进化流程

### 35.1 标准流程

```text
任务完成
↓
系统生成最终输出
↓
Supervisor Agent 判断是否达标
↓
Knowledge Evolution Agent 复盘任务
↓
系统提出可沉淀内容
↓
用户审核
↓
写入本地知识库
↓
必要时生成 Skill
↓
未来任务自动调用
```

### 35.2 示例

用户完成一次“优化前端 UI 排版”的任务后，系统自动总结：

```text
本次任务可沉淀经验：

1. 用户偏好低饱和、非深色、类 Claude 的 UI 风格。
2. UI 优化时应先检查布局层级，再检查字体、间距、卡片边界和交互状态。
3. 当前项目使用 Next.js + Tailwind，后续 UI 修改应遵守该技术栈。
4. 本次形成了一个可复用的 UI Optimization Skill。
```

用户确认后，系统写入：

* User Memory
* Project Memory
* Skill Memory

未来用户再次要求“优化页面”，Agent 会自动调用这些经验。

## 36. MVP 规划（自进化阶段）

### 36.1 MVP 原有重点

* 多模型接入
* Agent 角色管理
* 任务拆解
* 模型路由
* 任务交接
* 可视化工位

### 36.2 MVP 新增重点

建议加入以下自进化相关功能：

1. 任务完成后自动生成 Memory Draft
2. 用户确认后写入本地知识库
3. 支持 Project Memory
4. 支持 User Preference Memory
5. 支持 Handoff Summary 保存
6. 支持 Skill 草稿生成
7. 支持基于本地知识库的 RAG 检索
8. 支持在新任务开始前自动加载相关记忆

### 36.3 暂缓功能

以下功能可以后期再做：

1. 自动生成复杂 Skill
2. Skill Marketplace
3. 完全自动记忆写入
4. 多端同步
5. 团队共享知识库
6. 企业权限管理
7. 自动执行高风险本地操作
8. 完整浏览器自动化

## 37. 自进化机制的安全与质量控制

自进化知识库如果设计不好，会带来问题：

* 错误经验被保存
* 过期知识被重复调用
* 用户临时想法被误认为长期偏好
* Agent 自己生成的错误结论污染知识库
* Skill 越积越多但质量不高
* 模型路由规则被错误经验影响

因此需要加入控制机制。

### 37.1 人工确认

早期所有长期记忆都建议经过用户确认后保存。

### 37.2 置信度评分

系统为每条记忆打分：

* 高置信度：明确事实或用户明确表达的偏好
* 中置信度：从多次任务中归纳出的习惯
* 低置信度：单次任务中推测出的结论

### 37.3 记忆过期机制

部分记忆需要过期或定期复查。

例如：

* API 版本
* 项目技术栈
* 模型表现
* 第三方平台限制
* 用户短期任务偏好

### 37.4 记忆来源可追溯

每条记忆都应该能追溯到来源任务或对话。

### 37.5 用户可编辑

用户必须能编辑、删除、禁用某条记忆。

## 38. 产品定位综合版

ModelGate Agent Studio 是一个面向开发者的多模型 Agent 协作与自进化知识平台。它能够接入多个模型 API 和 AI Coding Plan，将不同模型组织成具有不同职责的 Agent 团队，并通过任务拆解、模型路由、额度感知调度、任务交接和 Supervisor 审查，实现复杂开发任务的持续推进。

平台进一步通过本地 Memory、RAG 检索和 Skill 沉淀机制，将每一次项目执行过程中的上下文、经验、错误、解决方案和工作流转化为可复用知识。未来无论接入哪个模型，Agent 都可以读取本地知识库，继承过去的项目经验和用户偏好，从而不断优化自己的任务完成流程。

产品通过像素小人、Agent 工位、任务卡片和交接动画，将多 Agent 协作过程可视化，让用户直观看到每个 Agent 的职责、状态、模型来源、任务进度和知识沉淀过程。

## 39. 产品口号（自进化阶段）

### 中文口号

让多个 AI 模型像团队一样协作，也像人一样积累经验。

### 英文口号

Turn multiple AI models into a coordinated team that remembers, learns, and hands off work.

## 40. 简历项目描述

开发 ModelGate Agent Studio 多模型 Agent 协作与自进化知识平台，面向多 AI Coding Plan 与多 Provider API 场景，支持 Goal 解析、任务拆解、模型能力路由、Agent 角色分配、额度感知调度、Handoff Summary 任务交接、本地 Memory、RAG 检索与 Skill 沉淀机制。平台能够将每次任务执行中的上下文、项目经验、错误修复和工作流程沉淀为本地知识库，使未来接入的不同模型均可读取并复用历史经验，实现多模型 Agent 团队的持续协作与自我优化。

## 41. 项目亮点

1. 设计多模型 Agent 编排架构，将不同模型组织为 Planner、Coder、Reviewer、Researcher、Summarizer、Supervisor 等角色化 Agent。
2. 实现模型能力路由，根据任务类型、模型能力、上下文长度和额度状态自动选择合适模型。
3. 设计额度感知调度机制，在模型额度不足时自动生成 Handoff Summary，并将任务交接给其他 Agent。
4. 构建本地 Memory 体系，支持 Session Memory、Project Memory、User Memory、Agent Memory、Skill Memory 和 Handoff Memory。
5. 设计自进化知识库机制，在任务完成后自动提取经验、偏好、错误修复和工作流，并沉淀为可复用知识。
6. 设计 Skill Library，将高频任务流程沉淀为可复用 Skill，例如代码审查、项目理解、Bug 修复、任务交接和文档生成。
7. 规划 MCP 工具接入层，使 Agent 能够安全调用文件、GitHub、终端、浏览器、数据库等外部工具。
8. 设计 RAG 检索层，使 Agent 在新任务开始前自动检索相关项目记忆、历史经验、Skill 和交接记录。
9. 设计像素工位可视化工作区，用工位表示 Agent 角色，用像素小人表示当前 Worker，用任务卡片和交接动画展示协作过程。
10. 形成区别于普通多 API 工具、通用个人助理和传统 Workflow Builder 的开发者向多模型 Agent 工作台定位。

## 42. 核心产品判断

ModelGate Agent Studio 的核心不是“接入很多模型”，而是：

> 把不同模型的能力组织起来，让它们围绕同一个目标持续协作。

ModelGate Agent Studio 的长期价值也不是“每次帮用户回答一个问题”，而是：

> 每次完成任务后，都能把经验沉淀下来，让下一次任务完成得更好。

因此，ModelGate Agent Studio 的真正核心可以概括为：

```text
多模型协作
+
额度感知调度
+
任务交接
+
本地记忆
+
RAG 检索
+
Skill 沉淀
+
持续自进化
```

最终形成一个可以长期陪伴用户完成项目的 AI Agent 工作台。
