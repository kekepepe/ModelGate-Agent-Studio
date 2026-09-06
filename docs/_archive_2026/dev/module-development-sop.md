# ModelGate Agent Studio 模块开发 SOP：PRD / Story / Task / UI Spec → Claude Code 实现

> 适用阶段：第七步，把产品文档交给 Claude Code 开发。  
> 使用方式：每次只指定一个模块和一个轮次，让 Claude Code 读取本文件后严格执行对应轮次。  
> 核心原则：不要一次性说“开发一个大功能”，而是基于文档、限定模块、限定轮次、限定文件范围来推进。

---

## 0. 这份 SOP 的用途

这份文件用于规范 ModelGate Agent Studio 每个模块的开发流程。

每个模块必须基于以下四类文档开发：

```text
docs/prd/{{module_slug}}-prd.md
docs/stories/{{module_slug}}-stories.md
docs/tasks/{{module_slug}}-tasks.md
docs/ui/{{module_slug}}-ui-spec.md
```

其中：

| 文件 | 作用 |
|---|---|
| PRD | 定义模块为什么做、做什么、不做什么 |
| Stories | 定义用户视角下的功能场景与验收标准 |
| Tasks | 定义可以交给 Claude Code 执行的开发任务 |
| UI Spec | 定义页面结构、状态、交互和视觉风格 |

第七步只负责把这些文档变成代码，不重新发散产品方向。

---

## 1. Claude Code 调用模板

以后每次进入 Claude Code，只需要复制下面这个模板，并替换模块名称、模块 slug 和执行轮次。

```text
请阅读并严格遵守：

docs/dev/module-development-sop.md

本次开发模块：{{module_name}}
模块 slug：{{module_slug}}
本次执行轮次：第 {{round_number}} 轮：{{round_name}}

本模块对应文档：
1. docs/prd/{{module_slug}}-prd.md
2. docs/stories/{{module_slug}}-stories.md
3. docs/tasks/{{module_slug}}-tasks.md
4. docs/ui/{{module_slug}}-ui-spec.md

要求：
1. 只执行本次指定轮次
2. 只处理本次指定模块
3. 不要扩展无关功能
4. 不要重构无关模块
5. 严格按 SOP 输出结果
6. 完成后停止，等待我确认
```

示例：

```text
请阅读并严格遵守：

docs/dev/module-development-sop.md

本次开发模块：Handoff Manager
模块 slug：handoff-manager
本次执行轮次：第 1 轮：implementation plan

本模块对应文档：
1. docs/prd/handoff-manager-prd.md
2. docs/stories/handoff-manager-stories.md
3. docs/tasks/handoff-manager-tasks.md
4. docs/ui/handoff-manager-ui-spec.md

要求：
1. 只执行本次指定轮次
2. 只处理本次指定模块
3. 不要扩展无关功能
4. 不要重构无关模块
5. 严格按 SOP 输出结果
6. 完成后停止，等待我确认
```

---

## 2. 推荐模块开发顺序

标准工程顺序：

```text
1. Agent Registry
2. Model Router
3. Quota Manager
4. Handoff Manager
5. Logs / Observability
6. Agent Workspace
```

原因：

```text
Agent Registry 定义 Agent
↓
Model Router 选择模型
↓
Quota Manager 判断额度风险
↓
Handoff Manager 处理任务交接
↓
Logs / Observability 记录全过程
↓
Agent Workspace 把状态展示出来
```

如果要快速出 Demo，可以改成：

```text
1. Agent Workspace mock
2. Handoff Manager mock
3. Agent Registry
4. Model Router
5. Quota Manager
6. Logs / Observability
```

但 Demo 顺序会带来更多 mock，后面需要替换为真实接口。标准开发更建议先完整跑通 Handoff Manager，作为第一个样板模块。

---

## 3. 模块命名与路径规范

| 模块名称 | 推荐 slug | PRD | Stories | Tasks | UI Spec | Implementation Plan |
|---|---|---|---|---|---|---|
| Agent Registry | agent-registry | docs/prd/agent-registry-prd.md | docs/stories/agent-registry-stories.md | docs/tasks/agent-registry-tasks.md | docs/ui/agent-registry-ui-spec.md | docs/dev/agent-registry-implementation-plan.md |
| Model Router | model-router | docs/prd/model-router-prd.md | docs/stories/model-router-stories.md | docs/tasks/model-router-tasks.md | docs/ui/model-router-ui-spec.md | docs/dev/model-router-implementation-plan.md |
| Quota Manager | quota-manager | docs/prd/quota-manager-prd.md | docs/stories/quota-manager-stories.md | docs/tasks/quota-manager-tasks.md | docs/ui/quota-manager-ui-spec.md | docs/dev/quota-manager-implementation-plan.md |
| Handoff Manager | handoff-manager | docs/prd/handoff-manager-prd.md | docs/stories/handoff-manager-stories.md | docs/tasks/handoff-manager-tasks.md | docs/ui/handoff-manager-ui-spec.md | docs/dev/handoff-manager-implementation-plan.md |
| Logs / Observability | logs-observability | docs/prd/logs-observability-prd.md | docs/stories/logs-observability-stories.md | docs/tasks/logs-observability-tasks.md | docs/ui/logs-observability-ui-spec.md | docs/dev/logs-observability-implementation-plan.md |
| Agent Workspace | agent-workspace | docs/prd/agent-workspace-prd.md | docs/stories/agent-workspace-stories.md | docs/tasks/agent-workspace-tasks.md | docs/ui/agent-workspace-ui-spec.md | docs/dev/agent-workspace-implementation-plan.md |

---

## 4. 每个模块的 7 轮标准流程

每个模块都按 7 轮推进：

```text
第 1 轮：制定 implementation plan，不改代码
第 2 轮：实现数据结构和后端接口
第 3 轮：实现前端页面
第 4 轮：补基础测试
第 5 轮：自查实现结果，不修代码
第 6 轮：根据自查报告修问题
第 7 轮：生成 implementation log
```

必须遵守的开发原则：

1. 先计划，再开发。
2. 先后端，再前端。
3. 先核心功能，再视觉细节。
4. 先测试核心路径，再补完整测试。
5. 先自查，再修复。
6. 每个模块完成后必须更新 `docs/dev/implementation-log.md`。
7. 不要在一个轮次里顺手做其他轮次的事。

---

# 第 1 轮：制定 implementation plan，不改代码

## 1.1 本轮目标

让 Claude Code 先读文档、分析项目结构、判断实现范围，并生成开发计划。

本轮只生成计划，不允许改代码。

## 1.2 Claude Code 提示词

```text
请先不要写代码。

请阅读以下文件：

1. docs/prd/{{module_slug}}-prd.md
2. docs/stories/{{module_slug}}-stories.md
3. docs/tasks/{{module_slug}}-tasks.md
4. docs/ui/{{module_slug}}-ui-spec.md

然后请完成以下事情：

1. 分析当前项目结构
2. 判断 {{module_name}} 应该放在哪些前端和后端目录
3. 列出需要新增或修改的文件
4. 列出开发顺序
5. 标出哪些任务可以先用 mock 数据实现
6. 标出哪些任务依赖真实后端接口
7. 标出可能影响现有功能的风险点
8. 标出本模块与其他模块的依赖关系
9. 标出本模块的 P0 story / P0 task
10. 不要改动任何代码
11. 最后生成 implementation plan

请将计划保存为：

docs/dev/{{module_slug}}-implementation-plan.md
```

## 1.3 本轮输出要求

Claude Code 完成后必须输出：

```text
1. 已阅读的文档
2. 当前项目结构判断
3. 计划新增文件
4. 计划修改文件
5. 后端实现顺序
6. 前端实现顺序
7. 测试实现顺序
8. mock 数据说明
9. 真实接口依赖
10. 风险点
11. implementation plan 文件路径
```

## 1.4 本轮检查清单

完成后你要检查：

```text
1. 是否没有改代码
2. 是否生成 docs/dev/{{module_slug}}-implementation-plan.md
3. 是否明确前端目录
4. 是否明确后端目录
5. 是否明确新增文件和修改文件
6. 是否区分 mock 和真实接口
7. 是否列出开发顺序
8. 是否识别 P0 story / P0 task
9. 是否说明风险点
10. 是否没有扩展无关功能
```

未通过则让 Claude Code 重新生成 plan，不要进入第 2 轮。

---

# 第 2 轮：实现数据结构和后端接口

## 2.1 本轮目标

基于 implementation plan，实现本模块的数据结构、schema、service、API、后端状态逻辑。

本轮只做后端，不做前端页面。

## 2.2 Claude Code 提示词

```text
请基于 docs/dev/{{module_slug}}-implementation-plan.md，先实现 {{module_name}} 的数据结构和后端接口。

要求：

1. 只实现 backend / API / schema / service 相关内容
2. 不要实现前端页面
3. 不要改动无关模块
4. 不要重构现有项目结构
5. 优先沿用当前项目已有的后端风格、命名方式和测试方式
6. 字段命名必须与 PRD / Tasks / UI Spec 保持一致
7. status 枚举必须前后端可复用或清晰约定
8. 如果需要 mock 数据，只能放在明确的 mock / seed / fixture 位置，并标注用途

请根据以下文档确认本轮后端范围：

1. docs/prd/{{module_slug}}-prd.md
2. docs/stories/{{module_slug}}-stories.md
3. docs/tasks/{{module_slug}}-tasks.md
4. docs/ui/{{module_slug}}-ui-spec.md
5. docs/dev/{{module_slug}}-implementation-plan.md

需要实现：

1. 本模块核心数据对象
2. 本模块核心 schema / type
3. 本模块 service 层逻辑
4. 本模块 API 路由
5. 基础错误处理
6. 基础状态更新逻辑
7. 与现有模块必要的最小集成

完成后请输出：

1. 修改了哪些文件
2. 新增了哪些文件
3. 新增了哪些接口
4. 核心数据对象字段
5. 每个接口的请求方式和路径
6. 每个接口的请求参数和响应结构
7. 如何手动测试这些接口
8. 是否还有 mock 数据
9. 是否有未完成项
10. 是否影响已有功能
```

## 2.3 常见后端能力清单

不同模块按自己的 PRD / Tasks 取舍，不要机械全做。

### Agent Registry

```text
1. 创建 Agent Station
2. 查询 Agent Station 列表
3. 查询 Agent Station 详情
4. 更新 Agent Station
5. 启用 / 禁用 Agent Station
6. 配置默认模型
7. 配置备用模型
8. 配置 allowed_tools
9. 配置 handoff_enabled
```

核心字段参考：

```text
agent_id
agent_name
role
description
default_model_id
backup_model_ids
allowed_tools
system_prompt
output_format
max_steps
handoff_enabled
status
created_at
updated_at
```

### Model Router

```text
1. 注册可用模型能力
2. 查询模型能力列表
3. 根据 task_type 推荐模型
4. 根据 capability_tags 推荐模型
5. 根据 quota_status 过滤模型
6. 返回推荐理由
7. 记录一次路由决策
```

核心字段参考：

```text
route_id
task_id
task_type
candidate_model_ids
selected_model_id
selected_agent_id
reason
capability_match_score
quota_status
cost_level
speed_level
created_at
```

### Quota Manager

```text
1. 记录模型调用次数
2. 记录 token 使用量
3. 记录最近调用时间
4. 查询模型额度状态
5. 更新模型额度状态
6. 判断是否接近额度限制
7. 生成 quota warning
8. 为 Handoff Manager 提供触发依据
```

核心字段参考：

```text
quota_id
model_id
provider
used_tokens
used_requests
estimated_remaining_tokens
estimated_remaining_requests
quota_status
reset_at
last_used_at
warning_reason
created_at
updated_at
```

### Handoff Manager

```text
1. 创建 HandoffRecord
2. 查询 Handoff 列表
3. 查询 Handoff 详情
4. 手动触发 Handoff
5. 更新 Handoff 状态
6. 保存 Handoff Summary
7. 保存接手后结果
```

核心字段参考：

```text
handoff_id
goal_id
task_id
from_agent_id
from_model_id
to_agent_id
to_model_id
reason
handoff_summary
status
created_at
updated_at
result_after_handoff
```

### Logs / Observability

```text
1. 记录模型调用日志
2. 记录 Agent 输出日志
3. 记录工具调用日志
4. 记录任务状态变化
5. 记录错误信息
6. 查询日志列表
7. 查询日志详情
8. 支持按 goal_id / task_id / agent_id / model_id 过滤
```

核心字段参考：

```text
log_id
goal_id
task_id
agent_id
model_id
log_type
input_summary
output_summary
error_message
tool_name
tool_status
token_usage
created_at
metadata
```

### Agent Workspace

```text
1. 查询当前活跃 Goal
2. 查询任务树
3. 查询 Agent Station 状态
4. 查询 Worker 状态
5. 查询最近执行日志
6. 查询最近 Handoff 记录
7. 聚合 Workspace Snapshot
8. 为前端可视化提供统一数据结构
```

核心字段参考：

```text
workspace_snapshot_id
goal
active_tasks
agent_stations
worker_sessions
handoff_records
quota_overview
execution_logs
updated_at
```

## 2.4 本轮检查清单

```text
1. 后端是否能单独运行
2. API 路径是否清晰
3. 字段是否和 PRD / Tasks / UI Spec 一致
4. status 枚举是否清楚
5. 是否没有实现前端页面
6. 是否没有改动无关模块
7. 是否有基础错误处理
8. 是否说明 mock 数据位置
9. 是否能手动测试接口
10. 是否输出未完成项
```

---

# 第 3 轮：实现前端页面

## 3.1 本轮目标

基于 UI Spec 和第 2 轮后端接口，实现本模块前端页面。

本轮只做本模块前端相关内容。

## 3.2 Claude Code 提示词

```text
请基于以下文件实现 {{module_name}} 前端页面：

1. docs/prd/{{module_slug}}-prd.md
2. docs/stories/{{module_slug}}-stories.md
3. docs/tasks/{{module_slug}}-tasks.md
4. docs/ui/{{module_slug}}-ui-spec.md
5. docs/dev/{{module_slug}}-implementation-plan.md

要求：

1. 只实现 {{module_name}} 前端相关内容
2. 使用第 2 轮已经完成的后端接口
3. 如果接口暂时不可用，可以保留清晰的 mock fallback，但必须标注出来
4. 不要改动无关页面
5. 不要加入复杂动画
6. 优先保证信息结构清晰、状态清楚、交互可测试
7. 保持低饱和、非深色、类 Claude 风格
8. 必须实现空状态、加载状态、失败状态
9. 页面字段必须与后端返回字段一致
10. 不要为了视觉效果重构业务逻辑

页面至少需要包含：

1. 本模块主列表或主面板
2. 本模块详情区、详情页或详情抽屉
3. 核心状态标签
4. 核心时间信息
5. 核心关联对象信息
6. 空状态
7. 加载状态
8. 失败状态
9. 基础筛选或刷新能力，如 UI Spec 要求
10. 清晰的页面入口

完成后请输出：

1. 修改了哪些文件
2. 新增了哪些文件
3. 页面入口在哪里
4. 调用了哪些接口
5. 哪些数据来自真实接口
6. 哪些数据仍然是 mock
7. 空状态如何触发
8. 失败状态如何触发
9. 如何手动测试页面
10. 是否影响已有页面
```

## 3.3 各模块前端重点

### Agent Registry

```text
1. Agent Station 列表
2. Agent 详情抽屉 / 详情页
3. Agent 职责说明
4. 默认模型 / 备用模型
5. allowed_tools 展示
6. handoff_enabled 状态
7. 启用 / 禁用状态
8. 空状态 / 加载状态 / 失败状态
```

### Model Router

```text
1. 模型路由规则列表
2. 路由测试面板
3. 输入 task_type / capability_tags
4. 推荐模型结果
5. 推荐理由
6. quota_status 提示
7. 历史路由记录
8. 空状态 / 加载状态 / 失败状态
```

### Quota Manager

```text
1. 模型额度概览
2. 每个模型调用次数
3. token 使用量
4. 预估剩余额度
5. quota_status 标签
6. warning_reason 展示
7. reset_at / last_used_at
8. 接近额度限制的提示
9. 空状态 / 加载状态 / 失败状态
```

### Handoff Manager

```text
1. Handoff 列表
2. Handoff 详情抽屉
3. 交接原因
4. 原 Agent / 接手 Agent
5. 原模型 / 接手模型
6. Handoff Summary
7. 交接状态标签
8. 交接时间
9. 接手后结果
10. 空状态 / 加载状态 / 失败状态
```

### Logs / Observability

```text
1. 日志列表
2. 日志详情抽屉
3. log_type 标签
4. goal_id / task_id / agent_id / model_id
5. 输入摘要 / 输出摘要
6. 错误信息
7. token_usage
8. 工具调用状态
9. 筛选与刷新
10. 空状态 / 加载状态 / 失败状态
```

### Agent Workspace

```text
1. 左侧 Goal 输入区
2. 中间 Agent 工位区
3. 任务卡片区
4. 右侧任务详情区
5. 底部执行日志区
6. Agent 状态灯
7. Worker / Model 显示
8. 最近 Handoff 记录
9. Quota 状态提示
10. 卡片网格视图优先
11. 像素办公室视图可以先 mock 或暂缓
12. 空状态 / 加载状态 / 失败状态
```

## 3.4 本轮检查清单

```text
1. 页面是否能进入
2. 主列表或主面板是否能展示
3. 详情区是否能打开
4. 字段是否和后端一致
5. 空状态是否存在
6. 加载状态是否存在
7. 失败状态是否存在
8. 状态标签是否清楚
9. 是否没有复杂动画
10. 是否符合低饱和、非深色、类 Claude 风格
11. 是否没有改动无关页面
12. mock fallback 是否明确标注
```

---

# 第 4 轮：补基础测试

## 4.1 本轮目标

为本模块补充基础测试，覆盖核心后端接口和核心前端状态。

本轮重点不是追求覆盖率很高，而是确保核心路径不会完全失控。

## 4.2 Claude Code 提示词

```text
请为刚才实现的 {{module_name}} 补充基础测试。

要求：

1. 如果当前项目已有测试框架，请沿用现有测试框架
2. 不要引入新的大型测试框架
3. 不要为了测试大改业务代码
4. 优先覆盖 P0 story 和 P0 task
5. 优先覆盖后端核心接口
6. 优先覆盖前端核心展示状态
7. 测试字段必须和实际 schema / API 一致
8. 测试失败时，先说明原因，不要大范围重构

后端测试至少检查：

1. 是否能创建本模块核心记录
2. 是否能查询本模块列表
3. 是否能查询本模块详情
4. 是否能更新本模块核心状态
5. 是否能处理非法参数或不存在记录

前端测试至少检查：

1. 页面是否能渲染
2. 主列表或主面板是否能展示
3. 详情区是否能打开
4. 空状态是否能展示
5. 失败状态是否能展示
6. 关键状态标签是否能展示

测试完成后请运行相关测试，并输出：

1. 新增了哪些测试文件
2. 修改了哪些测试文件
3. 测试覆盖了哪些功能
4. 测试命令
5. 测试结果
6. 是否有失败项
7. 如果有失败项，请说明原因
8. 是否还有未覆盖但应该后续补充的测试
```

## 4.3 各模块测试重点

### Agent Registry

```text
1. 创建 Agent Station
2. 查询 Agent Station 列表
3. 查询 Agent Station 详情
4. 更新 Agent Station
5. 前端展示 Agent 列表
6. 前端展示 Agent 详情
7. 前端展示启用 / 禁用状态
```

### Model Router

```text
1. 根据 task_type 返回推荐模型
2. 根据 capability_tags 返回推荐模型
3. quota_status 影响路由结果
4. 返回推荐理由
5. 前端展示推荐结果
6. 前端展示路由历史
```

### Quota Manager

```text
1. 记录 token 使用量
2. 查询额度状态
3. 更新额度状态
4. 判断接近额度限制
5. 前端展示 quota_status
6. 前端展示 warning_reason
```

### Handoff Manager

```text
1. 创建 HandoffRecord
2. 查询 Handoff 列表
3. 查询 Handoff 详情
4. 更新 Handoff 状态
5. 前端展示 Handoff 列表
6. 前端打开详情抽屉
7. 前端展示 Handoff Summary
```

### Logs / Observability

```text
1. 创建日志记录
2. 查询日志列表
3. 查询日志详情
4. 按 goal_id / task_id / agent_id / model_id 过滤
5. 前端展示日志列表
6. 前端展示错误日志
7. 前端展示工具调用日志
```

### Agent Workspace

```text
1. 获取 workspace snapshot
2. 展示 Agent Station 状态
3. 展示任务卡片
4. 展示最近日志
5. 展示最近 Handoff
6. 展示空 workspace
7. 展示接口失败状态
```

## 4.4 本轮检查清单

```text
1. 是否新增了测试文件
2. 是否覆盖后端核心接口
3. 是否覆盖前端核心页面
4. 是否覆盖空状态
5. 是否覆盖失败状态
6. 是否沿用现有测试框架
7. 是否没有引入大型新框架
8. 是否没有为了测试大改业务代码
9. 测试命令是否清楚
10. 测试结果是否明确
```

---

# 第 5 轮：自查实现结果，不修代码

## 5.1 本轮目标

让 Claude Code 对本模块做一次实现质量自查，输出检查报告。

本轮只检查，不修代码。

## 5.2 Claude Code 提示词

```text
请根据以下文件，对 {{module_name}} 的实现做一次自查：

1. docs/prd/{{module_slug}}-prd.md
2. docs/stories/{{module_slug}}-stories.md
3. docs/tasks/{{module_slug}}-tasks.md
4. docs/ui/{{module_slug}}-ui-spec.md
5. docs/dev/{{module_slug}}-implementation-plan.md

请检查：

1. 是否完成所有 P0 story
2. 是否完成所有 P0 task
3. 是否遗漏任何验收标准
4. 是否存在无关改动
5. 是否有前后端字段不一致
6. 是否有接口路径和前端调用不一致
7. 是否有 status 枚举不一致
8. 是否有状态未覆盖
9. 是否有页面空状态缺失
10. 是否有页面加载状态缺失
11. 是否有页面错误状态缺失
12. 是否有 mock 数据未标注
13. 是否还有需要补的测试
14. 是否影响已有功能
15. 是否有安全、权限或数据污染风险

只输出检查报告，先不要改代码。

检查报告请按以下结构输出：

- 总体结论
- 已完成项
- 未完成项
- 风险项
- 无关改动检查
- 字段一致性检查
- API 一致性检查
- 状态覆盖检查
- UI 状态检查
- Mock 数据检查
- 测试覆盖检查
- 建议修复顺序
```

## 5.3 本轮检查清单

你要重点看：

```text
1. P0 story 是否全部完成
2. P0 task 是否全部完成
3. 接口字段是否统一
4. status 枚举是否前后端一致
5. 空状态 / 加载状态 / 错误状态是否真的有
6. mock 是否还混在正式逻辑里
7. 是否出现无关改动
8. 是否影响已有功能
9. 测试是否真的跑过
10. 修复顺序是否合理
```

如果 Claude Code 说“没有问题”，也不要完全相信，至少人工看一次字段、状态、mock、测试结果。

---

# 第 6 轮：根据自查报告修问题

## 6.1 本轮目标

只修复第 5 轮自查报告中发现的问题。

本轮不新增无关功能，不重构无关模块。

## 6.2 Claude Code 提示词

```text
请根据刚才的 {{module_name}} 自查报告修复问题。

要求：

1. 只修复自查报告中列出的问题
2. 不要新增无关功能
3. 不要重构无关模块
4. 优先修复 P0 story 和验收标准相关问题
5. 优先修复字段不一致问题
6. 优先修复 API 路径和前端调用不一致问题
7. 优先修复 status 枚举不一致问题
8. 优先补齐空状态、加载状态、错误状态
9. 优先补齐缺失测试
10. 修复后运行相关测试

完成后请输出：

1. 修复了哪些问题
2. 修改了哪些文件
3. 是否还有未解决问题
4. 测试命令
5. 测试结果
6. 是否引入了新的 mock
7. 是否影响已有功能
```

## 6.3 本轮检查清单

```text
1. 是否只修自查报告里的问题
2. 是否没有扩展新需求
3. 是否没有重构无关模块
4. P0 story 问题是否修复
5. 字段不一致是否修复
6. API 不一致是否修复
7. 状态缺失是否修复
8. 测试缺失是否修复
9. 测试是否重新运行
10. 是否还有未解决问题
```

---

# 第 7 轮：生成 implementation log

## 7.1 本轮目标

把本模块实现过程写入 `docs/dev/implementation-log.md`，作为后续 Memory / Skill / Project Knowledge 的原始素材。

本轮只追加日志，不覆盖旧内容。

## 7.2 Claude Code 提示词

```text
请为本次 {{module_name}} 实现生成 implementation log，并追加到：

docs/dev/implementation-log.md

要求记录：

1. 本次实现的模块
2. 本次实现日期
3. 完成了哪些 story_id
4. 完成了哪些 task_id
5. 修改了哪些文件
6. 新增了哪些文件
7. 新增了哪些接口
8. 新增了哪些数据对象或字段
9. 当前还有哪些未完成
10. 当前还有哪些 mock 数据
11. 发现了哪些问题
12. 已修复哪些问题
13. 测试命令
14. 测试结果
15. 是否影响已有功能
16. 下一步建议

请只追加日志，不要覆盖已有内容。
```

## 7.3 推荐 log 格式

```markdown
## {{YYYY-MM-DD}} — {{module_name}} Implementation Log

### 1. Module

- module_name: {{module_name}}
- module_slug: {{module_slug}}

### 2. Completed Stories

- {{story_id}}: {{story_title}}

### 3. Completed Tasks

- {{task_id}}: {{task_title}}

### 4. Files Changed

#### Added

- {{file_path}}

#### Modified

- {{file_path}}

### 5. APIs Added or Updated

| Method | Path | Description |
|---|---|---|
| GET | /api/... | ... |

### 6. Data Objects / Fields

```text
{{object_name}}
- field_a
- field_b
- field_c
```

### 7. Mock Data

- {{mock_item}}: {{reason}}

### 8. Known Issues

- {{issue}}

### 9. Fixes Completed

- {{fix}}

### 10. Test Result

```text
{{test_command}}
{{test_result}}
```

### 11. Next Step

- {{next_step}}
```

## 7.4 本轮检查清单

```text
1. 是否追加到 docs/dev/implementation-log.md
2. 是否没有覆盖旧日志
3. 是否记录 story_id
4. 是否记录 task_id
5. 是否记录修改文件
6. 是否记录新增接口
7. 是否记录数据对象字段
8. 是否记录 mock 数据
9. 是否记录测试结果
10. 是否记录下一步建议
```

---

# 5. 一个模块完成后的总验收清单

每个模块完整跑完 7 轮后，至少检查以下 15 项：

```text
1. PRD 中的 P0 功能是否完成
2. Stories 中的 P0 story 是否完成
3. Tasks 中的 P0 task 是否完成
4. UI Spec 中的核心页面结构是否实现
5. 后端字段和前端字段是否一致
6. status 枚举是否一致
7. API 路径是否清晰
8. 页面入口是否存在
9. 空状态是否有
10. 加载状态是否有
11. 错误状态是否有
12. 测试是否能跑
13. 是否还有未标注 mock
14. 是否没有无关改动
15. implementation-log.md 是否更新
```

如果这 15 项没过，不要进入下一个模块。

---

# 6. 模块完成判定标准

一个模块可以进入下一个模块的最低标准：

```text
1. 核心数据对象已定义
2. 核心 API 已实现
3. 前端主页面能访问
4. 详情区能展示
5. 空 / 加载 / 失败状态存在
6. P0 story 已完成
7. P0 task 已完成
8. 基础测试已补
9. 自查问题已修
10. implementation log 已追加
```

不要求一次做到：

```text
1. 完整复杂动画
2. 完整像素办公室
3. 企业级权限
4. 完整插件生态
5. 完全自动读取真实 coding plan 额度
6. 大规模团队协作
```

---

# 7. 特别注意：不要把模块做成普通后台

ModelGate Agent Studio 的核心不是普通 CRUD。

开发任何模块时，都要保留以下产品特征：

```text
1. 多模型协作
2. Agent 角色分工
3. 任务状态可见
4. 额度感知调度
5. 结构化 Handoff
6. 执行记录可追踪
7. 未来可沉淀 Memory / Skill
8. 低饱和、非深色、类 Claude 的 UI 风格
9. Agent 工位 / 任务卡片 / 状态灯的可视化方向
```

MVP 阶段可以暂缓复杂动画和完整像素办公室，但不能把页面做成没有 Agent 逻辑、没有任务状态、没有交接记录的普通管理表格。

---

# 8. 推荐首次执行模块

建议第一个完整跑通：

```text
Handoff Manager
```

原因：

```text
1. 它直接体现 ModelGate 的核心差异化
2. 它连接 Quota Manager、Agent Registry、Model Router、Logs、Workspace
3. 它能验证“额度不足不中断任务，而是生成 Handoff Summary 接力完成”的核心体验
4. 它的 implementation log 可以直接成为后续 Handoff Skill / Project Memory 的素材
```

Handoff Manager 完整跑通后，再复制同一流程开发 Agent Workspace。

---

# 9. Handoff Manager 示例调用

## 第 1 轮示例

```text
请阅读并严格遵守：

docs/dev/module-development-sop.md

本次开发模块：Handoff Manager
模块 slug：handoff-manager
本次执行轮次：第 1 轮：implementation plan

本模块对应文档：
1. docs/prd/handoff-manager-prd.md
2. docs/stories/handoff-manager-stories.md
3. docs/tasks/handoff-manager-tasks.md
4. docs/ui/handoff-manager-ui-spec.md

要求：
1. 只执行本次指定轮次
2. 只处理本次指定模块
3. 不要扩展无关功能
4. 不要重构无关模块
5. 严格按 SOP 输出结果
6. 完成后停止，等待我确认
```

## 第 2 轮示例

```text
请阅读并严格遵守：

docs/dev/module-development-sop.md

本次开发模块：Handoff Manager
模块 slug：handoff-manager
本次执行轮次：第 2 轮：实现数据结构和后端接口

本模块对应文档：
1. docs/prd/handoff-manager-prd.md
2. docs/stories/handoff-manager-stories.md
3. docs/tasks/handoff-manager-tasks.md
4. docs/ui/handoff-manager-ui-spec.md

要求：
1. 只执行本次指定轮次
2. 只处理本次指定模块
3. 不要扩展无关功能
4. 不要重构无关模块
5. 严格按 SOP 输出结果
6. 完成后停止，等待我确认
```

## 后续轮次只改这一行

```text
本次执行轮次：第 {{round_number}} 轮：{{round_name}}
```

---

# 10. 最重要的控制句

每次让 Claude Code 执行前，都可以加上这句话：

```text
请把自己当成一个严格执行文档的工程实现者，而不是重新设计产品的产品经理。不要发散需求，不要顺手重构，不要跨模块开发。本轮只完成指定模块、指定轮次、指定范围。
```
