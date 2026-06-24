# Agent Registry 技术型 PRD

> 所属产品：ModelGate Agent Studio
>
> 所属阶段：MVP-A / MVP-B 核心模块
>
> 文档定位：Agent Registry 的产品与技术需求说明，用于 Agent Station 的创建、配置、管理和调用。

---

## 1. 功能背景

在 ModelGate Agent Studio 中，Agent 不是普通聊天角色，也不是单个模型。Agent 的定义是：

```text
Agent = 角色职责 + 默认模型 + 备用模型 + 工具权限 + 输出格式 + 最大执行步数 + 是否允许 Handoff
```

Agent Registry 是管理平台中所有 Agent Station 的核心模块。每个 Agent Station 代表一个固定职责的工位，例如 Planner、Coder、Reviewer、Researcher、Summarizer、Supervisor。

模型只是 Agent 的能力来源。一个 Agent Station 可以绑定默认模型，当默认模型不可用时，系统可以自动切换到备用模型。Worker 是模型在工位上的执行实例。

```text
Agent Station（工位）
├── role：固定职责
├── default_model_id：默认模型
├── backup_model_ids：备用模型列表
├── allowed_tools：可用工具
├── system_prompt：角色 Prompt
├── output_format：输出格式要求
├── max_steps_per_task：最大执行步数
└── handoff_enabled：是否允许交接
```

Agent Registry 提供以下能力：

1. 查看所有 Agent Station。
2. 创建新的 Agent Station。
3. 编辑 Agent Station 的配置。
4. 启用 / 禁用 Agent Station。
5. 绑定默认模型和备用模型。
6. 配置工具权限。
7. 设置输出格式和最大执行步数。
8. 控制是否允许 Handoff。
9. 查看 Agent Station 的当前状态和历史表现。

Agent Registry 的配置直接影响 Runtime 的任务分配、Model Router 的模型选择、Handoff Manager 的交接策略和 Workspace 的可视化展示。

---

## 2. 用户问题

### 2.1 主要用户

- 多模型重度使用的开发者
- AI 工具开发者或研究者
- AI 产品经理或独立开发者

### 2.2 用户痛点

#### 痛点一：Agent 和模型混为一谈

当前很多工具把 Agent 等同于模型选择器，用户只能看到 "GPT Agent"、"Claude Agent"，而不是 "Planner Agent"、"Coder Agent"。

结果：

- 无法按角色组织多 Agent 协作。
- 无法为不同角色配置不同 Prompt 和工具。
- 模型切换时丢失角色上下文。

#### 痛点二：模型失败时没有备用方案

用户配置了某个模型作为 Agent，但该模型额度不足、服务中断或输出质量不足时，系统无法自动切换到其他模型。

结果：

- 任务中断。
- 需要手动重新配置。
- 上下文丢失。

#### 痛点三：Agent 能力不可控

用户无法限制某个 Agent 能使用什么工具、输出什么格式、最多执行多少步。

结果：

- Agent 可能调用不该调用的工具。
- 输出格式不统一，后续处理困难。
- 任务陷入无限循环。

#### 痛点四：Handoff 策略不可配置

用户无法控制哪些 Agent 可以交接、哪些不能，以及交接的触发条件。

结果：

- 不该交接的 Agent 被交接（如 Supervisor）。
- 该交接的 Agent 没有交接能力。
- 交接阈值不合理。

### 2.3 核心问题

Agent Registry 要回答的问题是：

> 用户如何定义、配置和管理一组角色化 Agent Station，使每个 Agent 都有明确的职责、合适的模型、受控的工具权限和清晰的交接策略？

---

## 3. 产品目标

### 3.1 核心目标

1. 提供 Agent Station 的创建、查看、编辑、启用、禁用能力。
2. 每个 Agent Station 必须绑定角色职责（role）。
3. 每个 Agent Station 必须绑定默认模型和备用模型。
4. 每个 Agent Station 可以配置可用工具列表。
5. 每个 Agent Station 可以配置系统 Prompt 和输出格式要求。
6. 每个 Agent Station 可以设置最大执行步数。
7. 每个 Agent Station 可以设置是否允许 Handoff 和交接阈值。
8. Agent Station 的配置可以被 Runtime、Model Router、Handoff Manager 和 Workspace 实时调用。
9. 提供默认 Agent 模板，降低用户配置成本。
10. 展示 Agent Station 的当前状态和历史表现统计。

### 3.2 非目标

当前阶段不追求：

- 自动生成 Agent 配置。
- Agent 自动优化自己的 Prompt。
- Agent 市场或第三方 Agent 导入。
- 复杂 Agent 权限分级（企业级 RBAC）。
- Agent 动态角色切换。
- Agent 自动发现最佳模型组合。

### 3.3 成功判断

Agent Registry 成功的标志：

> 用户可以在 Agent Registry 中查看、创建和编辑 Agent Station，为每个 Agent 配置角色、模型、工具、输出格式和 Handoff 策略，并且这些配置能被 Runtime 正确调用，使多 Agent 协作按预期工作。

---

## 4. 核心用户流程

### 4.1 查看 Agent 列表

```text
1. 用户进入 Agent Registry 页面。
2. 页面展示所有 Agent Station 列表。
3. 列表显示：Agent 名称、角色、当前状态、默认模型、是否允许 Handoff、完成任务数。
4. 用户可以通过角色、状态、模型筛选 Agent。
5. 用户点击某个 Agent，进入详情/编辑页。
```

### 4.2 创建 Agent Station

```text
1. 用户点击「创建 Agent」。
2. 系统提供默认模板选择（Planner、Coder、Reviewer 等）。
3. 用户选择模板或选择「自定义」。
4. 系统预填充模板配置。
5. 用户编辑 Agent 名称、角色、描述。
6. 用户选择默认模型。
7. 用户选择备用模型（可选多个）。
8. 用户配置允许使用的工具。
9. 用户编辑 System Prompt。
10. 用户设置输出格式要求。
11. 用户设置最大执行步数。
12. 用户设置是否允许 Handoff 和阈值。
13. 用户点击保存。
14. 系统校验配置（模型是否存在、Prompt 是否为空）。
15. 系统创建 AgentStation，返回成功。
16. Workspace 和 Runtime 可以立即使用该 Agent。
```

### 4.3 编辑 Agent Station

```text
1. 用户在列表中点击某个 Agent。
2. 进入 Agent 详情/编辑页。
3. 用户可以修改除 role 外的所有字段（role 修改需谨慎，可限制）。
4. 修改默认模型时，系统提示是否影响进行中任务。
5. 修改备用模型时，系统更新 Model Router 的备用策略。
6. 修改 handoff_enabled 时，系统更新 Handoff Manager 策略。
7. 用户点击保存，系统更新 AgentStation。
8. 更新后的配置立即生效（对后续任务生效，进行中任务不受影响）。
```

### 4.4 启用 / 禁用 Agent Station

```text
1. 用户在列表中找到某个 Agent。
2. 点击开关或按钮启用/禁用。
3. 禁用前系统检查：该 Agent 是否有进行中任务。
4. 如果有进行中任务，提示用户先完成任务或 Handoff。
5. 如果没有进行中任务，Agent 状态变为 disabled。
6. 禁用后，Runtime 不再分配任务给该 Agent。
7. Workspace 中该 Agent Station 显示为禁用状态（灰色）。
```

### 4.5 查看 Agent 详情

```text
1. 用户点击 Agent 列表中的某一行。
2. 页面展示 Agent 详情：
   - 基本信息（名称、角色、描述、状态）
   - 模型配置（默认模型、备用模型）
   - 工具权限
   - System Prompt
   - 输出格式
   - 执行限制（max_steps、handoff_enabled、阈值）
   - 当前状态（空闲/执行中/交接中）
   - 历史统计（完成任务数、交接次数、平均 token、成功率）
   - 最近任务列表
```

---

## 5. 页面结构

```text
Agent Registry 页面
├── Top Bar
│   ├── 页面标题：Agent Registry
│   └── 创建 Agent 按钮
├── Filter Bar
│   ├── 角色筛选（Planner / Coder / Reviewer / ...）
│   ├── 状态筛选（idle / running / disabled）
│   ├── 模型筛选
│   └── 搜索框
├── AgentList（主列表）
│   ├── Agent 卡片 / 行
│   │   ├── Agent 名称
│   │   ├── 角色标签
│   │   ├── 状态指示灯
│   │   ├── 默认模型
│   │   ├── Handoff 开关状态
│   │   └── 操作按钮（编辑 / 启用禁用）
│   └── 空状态
└── AgentDetail / AgentConfigForm（详情/编辑区）
    ├── 基本信息 Tab
    ├── 模型配置 Tab
    ├── 工具与 Prompt Tab
    ├── 执行限制 Tab
    └── 历史统计 Tab
```

---

## 6. Agent 创建流程

### 6.1 创建入口

- Agent Registry 页面顶部「创建 Agent」按钮。
- Workspace 中 Agent Station 区域的「添加 Agent」快捷入口（MVP-B）。

### 6.2 创建步骤

```text
Step 1: 选择模板
- 系统提供默认模板列表
- 用户选择模板或「自定义」

Step 2: 基本信息
- Agent 名称（必填）
- 角色（role，选择或输入）
- 描述（description）

Step 3: 模型配置
- 默认模型（default_model_id，下拉选择已配置模型）
- 备用模型（backup_model_ids，多选已配置模型）

Step 4: 工具与 Prompt
- 允许使用的工具（allowed_tools，多选）
- System Prompt（文本框，支持模板变量）
- 输出格式要求（output_format，选择或输入）

Step 5: 执行限制
- 最大执行步数（max_steps_per_task，数字输入）
- 是否允许 Handoff（handoff_enabled，Switch）
- Handoff 触发阈值（handoff_threshold_tokens，数字输入，可选）

Step 6: 确认与保存
- 预览配置摘要
- 点击保存
- 系统校验并创建
```

### 6.3 校验规则

- Agent 名称不能为空，不能重复。
- Role 不能为空，必须是系统支持的角色之一（或自定义）。
- Default_model_id 必须指向一个已启用模型。
- Backup_model_ids 中的模型必须已启用，且不能与 default_model_id 相同。
- System_prompt 不能为空（至少提供模板默认值）。
- Max_steps_per_task 必须为正整数，建议范围 1-50。
- Handoff_threshold_tokens 必须为正整数，建议范围 1000-100000。

---

## 7. Agent 编辑流程

### 7.1 编辑入口

- Agent List 中每行的「编辑」按钮。
- Agent Detail 页面中的「编辑」模式切换。

### 7.2 可编辑字段

| 字段 | 是否可编辑 | 影响范围 |
|------|-----------|----------|
| name | 是 | 展示名称 |
| description | 是 | 展示描述 |
| role | 建议限制（谨慎编辑） | 角色职责变化可能影响历史任务理解 |
| default_model_id | 是 | 后续任务使用新模型 |
| backup_model_ids | 是 | Model Router 备用策略 |
| allowed_tools | 是 | 后续任务的工具权限 |
| system_prompt | 是 | 后续任务的 Prompt |
| output_format | 是 | 后续任务的输出要求 |
| max_steps_per_task | 是 | 后续任务的执行限制 |
| handoff_enabled | 是 | Handoff Manager 策略 |
| handoff_threshold_tokens | 是 | Handoff 触发条件 |

### 7.3 编辑约束

1. 编辑 role 时，系统提示"修改角色可能影响该 Agent 的历史任务和统计"。
2. 编辑 default_model_id 时，系统提示"修改后仅影响新任务，进行中任务继续使用原模型"。
3. 编辑 handoff_enabled 为 false 时，系统提示"禁用后该 Agent 将无法触发 Handoff"。
4. 如果 Agent 当前有 running 任务，禁止禁用该 Agent，但允许编辑其他配置。

---

## 8. Agent 启用 / 禁用流程

### 8.1 启用

1. 用户点击禁用状态的 Agent 的「启用」按钮。
2. Agent 状态从 disabled 变为 idle。
3. Runtime 可以再次分配任务给该 Agent。
4. Workspace 中该 Agent Station 恢复正常显示。

### 8.2 禁用

1. 用户点击启用状态的 Agent 的「禁用」按钮。
2. 系统检查该 Agent 是否有 running 任务。
3. 如果有 running 任务：
   - 提示用户"该 Agent 有进行中任务，请先完成任务或 Handoff"。
   - 提供「查看任务」和「强制禁用」选项。
   - 强制禁用时，running 任务标记为 failed 或触发 Handoff。
4. 如果没有 running 任务：
   - Agent 状态从 idle 变为 disabled。
   - Runtime 不再分配新任务。
   - Workspace 中该 Agent Station 显示为灰色禁用状态。

### 8.3 删除

MVP 阶段建议只支持禁用，不支持删除。删除会破坏历史任务和 Handoff 记录的关联。

---

## 9. 默认 Agent 模板

系统预置以下默认 Agent 模板，降低用户配置成本。

### 9.1 Planner Agent

```yaml
name: Planner Agent
role: planner
description: 负责将用户 Goal 拆解为可执行的 Task 列表
default_model_id: claude-3-opus
backup_model_ids:
  - gpt-4-turbo
  - deepseek-chat
allowed_tools: []
system_prompt: |
  你是一个任务规划专家。你的职责是将用户的目标拆解为清晰、可执行的任务列表。
  每个任务必须包含：标题、描述、完成标准、预估复杂度。
  任务之间如果有依赖关系，请明确指出。
output_format: json
max_steps_per_task: 5
handoff_enabled: false
handoff_threshold_tokens: 0
```

### 9.2 Coder Agent

```yaml
name: Coder Agent
role: coder
description: 负责编写代码、修改文件、实现功能
default_model_id: deepseek-coder
backup_model_ids:
  - claude-3-opus
  - gpt-4-turbo
allowed_tools:
  - file_read
  - file_write
  - terminal_execute
system_prompt: |
  你是一个资深开发工程师。你的职责是根据任务描述编写高质量代码。
  请遵循项目的技术栈和代码规范。
  如果需要修改现有文件，请先读取文件内容，再生成修改方案。
output_format: markdown
max_steps_per_task: 20
handoff_enabled: true
handoff_threshold_tokens: 80000
```

### 9.3 Reviewer Agent

```yaml
name: Reviewer Agent
role: reviewer
description: 负责审查代码、检查质量、发现 bug
default_model_id: gpt-4-turbo
backup_model_ids:
  - claude-3-opus
allowed_tools:
  - file_read
  - diff_view
system_prompt: |
  你是一个代码审查专家。你的职责是审查代码修改，检查逻辑正确性、安全性、性能和代码风格。
  请给出具体的修改建议，指出问题所在行号和原因。
output_format: markdown
max_steps_per_task: 10
handoff_enabled: true
handoff_threshold_tokens: 60000
```

### 9.4 Research Agent

```yaml
name: Research Agent
role: researcher
description: 负责搜索信息、整理资料、提供技术调研
default_model_id: kimi-long-context
backup_model_ids:
  - claude-3-opus
  - gpt-4-turbo
allowed_tools:
  - web_search
  - file_read
system_prompt: |
  你是一个技术研究员。你的职责是根据任务需求搜索和整理相关信息。
  请提供来源、关键结论和行动建议。
output_format: markdown
max_steps_per_task: 15
handoff_enabled: true
handoff_threshold_tokens: 100000
```

### 9.5 Summarizer Agent

```yaml
name: Summarizer Agent
role: summarizer
description: 负责压缩上下文、生成交接摘要、总结执行结果
default_model_id: claude-3-haiku
backup_model_ids:
  - gpt-3.5-turbo
  - deepseek-chat
allowed_tools: []
system_prompt: |
  你是一个摘要生成专家。你的职责是将复杂的执行过程和上下文压缩为清晰的交接摘要。
  摘要必须包含：已完成工作、未完成工作、关键约束、已做决策、风险和下一步建议。
output_format: json
max_steps_per_task: 3
handoff_enabled: false
handoff_threshold_tokens: 0
```

### 9.6 Supervisor Agent

```yaml
name: Supervisor Agent
role: supervisor
description: 负责最终审查、判断是否完成任务、生成最终汇总
default_model_id: claude-3-opus
backup_model_ids:
  - gpt-4-turbo
allowed_tools:
  - file_read
system_prompt: |
  你是一个项目监督者。你的职责是审查所有任务的完成质量，判断 Goal 是否达成。
  如果存在问题，请指出具体缺陷和改进建议。
  如果 Goal 达成，请生成结构化的最终汇总报告。
output_format: markdown
max_steps_per_task: 5
handoff_enabled: false
handoff_threshold_tokens: 0
```

### 9.7 模板使用规则

1. 创建 Agent 时，用户选择模板后，系统预填充上述配置。
2. 用户可以基于模板修改任何字段。
3. 模板中的 default_model_id 如果当前未配置，系统提示用户先配置模型。
4. 模板中的 allowed_tools 如果当前未接入，系统提示工具不可用。

---

## 10. 前端组件设计

### 10.1 AgentList

**职责**：展示所有 Agent Station 的列表或卡片网格。

**Props**：

```typescript
interface AgentListProps {
  agents: AgentStation[];
  models: Model[];
  filters: AgentFilter;
  onSelect: (agentId: string) => void;
  onToggleStatus: (agentId: string, enabled: boolean) => void;
  onCreate: () => void;
}

interface AgentFilter {
  role?: string;
  status?: 'idle' | 'running' | 'disabled';
  modelId?: string;
  search?: string;
}
```

**展示内容**：

```text
┌─────────────────────────────────────────┐
│ 🤖 Planner Agent              [编辑]   │
│ Role: planner    Status: ● idle        │
│ Model: Claude 3 Opus                   │
│ Handoff: OFF   Tasks: 156 completed    │
└─────────────────────────────────────────┘
```

**行为**：

1. 根据 filters 筛选和排序 Agent。
2. 点击 Agent 卡片触发 `onSelect`。
3. 点击状态开关触发 `onToggleStatus`。
4. 禁用状态的 Agent 显示为灰色。
5. running 状态的 Agent 显示蓝色状态灯。

---

### 10.2 AgentConfigForm

**职责**：Agent Station 的创建和编辑表单。

**Props**：

```typescript
interface AgentConfigFormProps {
  agent?: AgentStation; // 编辑时传入，创建时为 undefined
  models: Model[];
  tools: Tool[];
  templates: AgentTemplate[];
  onSave: (config: AgentConfig) => void;
  onCancel: () => void;
  onSelectTemplate: (templateId: string) => void;
}

interface AgentConfig {
  name: string;
  role: string;
  description: string;
  default_model_id: string;
  backup_model_ids: string[];
  allowed_tools: string[];
  system_prompt: string;
  output_format: string;
  max_steps_per_task: number;
  handoff_enabled: boolean;
  handoff_threshold_tokens?: number;
}
```

**表单结构**：

```text
AgentConfigForm
├── 模板选择（创建时显示）
├── 基本信息
│   ├── 名称输入
│   ├── 角色选择（下拉 + 自定义输入）
│   └── 描述文本框
├── 模型配置
│   ├── 默认模型选择（单选下拉）
│   └── 备用模型选择（多选下拉）
├── 工具与 Prompt
│   ├── 工具权限多选
│   ├── System Prompt 编辑器
│   └── 输出格式选择
├── 执行限制
│   ├── 最大执行步数（数字输入）
│   ├── Handoff 开关
│   └── Handoff 阈值（数字输入，handoff_enabled 为 true 时显示）
└── 操作按钮
    ├── 保存
    ├── 取消
    └── 预览 Prompt
```

**行为**：

1. 创建时显示模板选择，选择后预填充表单。
2. 实时校验必填字段。
3. default_model_id 和 backup_model_ids 互斥校验。
4. handoff_enabled 为 false 时，隐藏 handoff_threshold_tokens。
5. 保存前展示配置摘要确认。

---

### 10.3 ModelBindingSelector

**职责**：选择默认模型和备用模型。

**Props**：

```typescript
interface ModelBindingSelectorProps {
  models: Model[];
  defaultModelId: string;
  backupModelIds: string[];
  onDefaultChange: (modelId: string) => void;
  onBackupChange: (modelIds: string[]) => void;
}
```

**展示内容**：

```text
默认模型
[Claude 3 Opus ▼]

备用模型
[☑ GPT-4 Turbo]
[☑ DeepSeek Chat]
[☐ Claude 3 Haiku]
```

**行为**：

1. 只展示已启用的模型。
2. 默认模型改变时，自动从备用模型中移除冲突项。
3. 备用模型中包含默认模型时，自动去重。
4. 每个模型旁展示能力标签（code、planning 等）。

---

### 10.4 ToolPermissionSelector

**职责**：选择 Agent 允许使用的工具。

**Props**：

```typescript
interface ToolPermissionSelectorProps {
  tools: Tool[];
  allowedTools: string[];
  onChange: (toolIds: string[]) => void;
}

interface Tool {
  id: string;
  name: string;
  description: string;
  category: string;
  risk_level: 'low' | 'medium' | 'high';
}
```

**展示内容**：

```text
工具权限

文件操作
[☑] file_read    - 读取文件内容
[☑] file_write   - 写入文件内容
[☐] file_delete  - 删除文件

终端
[☑] terminal_execute - 执行终端命令

网络
[☐] web_search   - 网络搜索
```

**行为**：

1. 按类别分组展示工具。
2. 高风险工具（如 file_delete、terminal_execute）用红色警告标识。
3. 鼠标悬停显示工具描述和风险说明。
4. 选择高风险工具时，二次确认提示。

---

### 10.5 OutputFormatEditor

**职责**：设置 Agent 的输出格式要求。

**Props**：

```typescript
interface OutputFormatEditorProps {
  value: string;
  onChange: (format: string) => void;
}
```

**选项**：

- markdown
- json
- code
- text
- custom（自定义输入）

**行为**：

1. 提供预设选项快速选择。
2. 选择 custom 时显示文本输入框。
3. 如果 role 是 summarizer 或 planner，默认推荐 json。
4. 如果 role 是 coder，默认推荐 code。

---

### 10.6 HandoffToggle

**职责**：控制 Agent 是否允许 Handoff 和设置阈值。

**Props**：

```typescript
interface HandoffToggleProps {
  enabled: boolean;
  thresholdTokens?: number;
  onEnabledChange: (enabled: boolean) => void;
  onThresholdChange: (tokens: number) => void;
}
```

**展示内容**：

```text
允许 Handoff  [Switch ON/OFF]

Handoff 触发阈值（token）
[80000]

说明：当该 Agent 使用的 token 达到此阈值时，系统建议生成交接摘要。
```

**行为**：

1. Switch 控制 enabled。
2. enabled 为 true 时，显示 threshold 输入框。
3. enabled 为 false 时，隐藏 threshold 输入框。
4. threshold 建议范围：1000 - 100000。
5. 对 Supervisor、Planner 等角色，默认建议关闭 Handoff。

---

## 11. 后端接口设计

接口遵循现有 API 约定：

```text
Base URL: /api/v1
Response: { success: boolean, data?: object, error?: object }
```

### 11.1 获取 Agent 列表

```http
GET /agents?role=planner&status=idle&model_id=xxx&page=1&page_size=20
```

响应：

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "agent-uuid",
        "name": "Coder Agent",
        "role": "coder",
        "description": "负责编写代码和实现功能",
        "status": "idle",
        "default_model_id": "model-1",
        "default_model_name": "DeepSeek Coder",
        "backup_model_ids": ["model-2", "model-3"],
        "handoff_enabled": true,
        "total_tasks_completed": 156,
        "created_at": "2026-06-24T12:00:00Z"
      }
    ],
    "total": 6,
    "page": 1,
    "page_size": 20
  }
}
```

### 11.2 获取 Agent 详情

```http
GET /agents/:agentId
```

响应：

```json
{
  "success": true,
  "data": {
    "id": "agent-uuid",
    "name": "Coder Agent",
    "role": "coder",
    "description": "负责编写代码和实现功能",
    "status": "idle",
    "current_task_id": null,
    "default_model_id": "model-1",
    "backup_model_ids": ["model-2", "model-3"],
    "allowed_tools": ["file_read", "file_write", "terminal_execute"],
    "system_prompt": "你是一个资深开发工程师...",
    "output_format": "markdown",
    "max_steps_per_task": 20,
    "allow_handoff": true,
    "handoff_threshold_tokens": 80000,
    "total_tasks_completed": 156,
    "total_handoffs_initiated": 12,
    "average_tokens_per_task": 4500,
    "created_at": "2026-06-24T12:00:00Z",
    "updated_at": "2026-06-24T12:00:00Z"
  }
}
```

### 11.3 创建 Agent

```http
POST /agents
```

请求体：

```json
{
  "name": "自定义 Coder Agent",
  "role": "coder",
  "description": "负责前端组件开发",
  "default_model_id": "model-1",
  "backup_model_ids": ["model-2"],
  "allowed_tools": ["file_read", "file_write"],
  "system_prompt": "你是一个前端开发工程师...",
  "output_format": "code",
  "max_steps_per_task": 15,
  "allow_handoff": true,
  "handoff_threshold_tokens": 60000
}
```

响应：201 Created

```json
{
  "success": true,
  "data": {
    "id": "agent-uuid",
    "name": "自定义 Coder Agent",
    "role": "coder",
    "status": "idle",
    "created_at": "2026-06-24T12:00:00Z"
  }
}
```

### 11.4 更新 Agent

```http
PATCH /agents/:agentId
```

请求体（只传要更新的字段）：

```json
{
  "name": "新名称",
  "default_model_id": "new-model-uuid",
  "handoff_enabled": false
}
```

响应：

```json
{
  "success": true,
  "data": {
    "id": "agent-uuid",
    "updated_at": "2026-06-24T12:00:00Z"
  }
}
```

### 11.5 启用 / 禁用 Agent

```http
PATCH /agents/:agentId/status
```

请求体：

```json
{
  "status": "disabled"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "id": "agent-uuid",
    "status": "disabled"
  }
}
```

### 11.6 获取 Agent 模板列表

```http
GET /agents/templates
```

响应：

```json
{
  "success": true,
  "data": [
    {
      "id": "template-planner",
      "name": "Planner Agent",
      "role": "planner",
      "description": "任务规划专家",
      "default_config": { ... }
    }
  ]
}
```

### 11.7 获取 Agent 历史统计

```http
GET /agents/:agentId/stats
```

响应：

```json
{
  "success": true,
  "data": {
    "total_tasks_completed": 156,
    "total_handoffs_initiated": 12,
    "average_tokens_per_task": 4500,
    "average_duration_ms": 32000,
    "success_rate": 0.92,
    "recent_tasks": [
      {
        "task_id": "task-1",
        "title": "实现登录页面",
        "status": "completed",
        "completed_at": "2026-06-24T12:00:00Z"
      }
    ]
  }
}
```

---

## 12. 数据对象设计

### 12.1 AgentStation

```typescript
interface AgentStation {
  id: string;
  name: string;
  role: 'planner' | 'coder' | 'reviewer' | 'research' | 'summarizer' | 'supervisor' | string;
  description: string;

  status: 'idle' | 'running' | 'handoff' | 'blocked' | 'error' | 'disabled';
  current_task_id?: string;

  default_model_id: string;
  backup_model_ids: string[];

  allowed_tools: string[];
  max_tool_calls_per_task: number;

  system_prompt: string;
  output_format_requirement?: string;

  max_steps_per_task: number;
  allow_handoff: boolean;
  handoff_threshold_tokens: number;

  total_tasks_completed: number;
  total_handoffs_initiated: number;
  average_tokens_per_task: number;

  created_at: Date;
  updated_at: Date;
}
```

### 12.2 AgentTemplate

```typescript
interface AgentTemplate {
  id: string;
  name: string;
  role: string;
  description: string;
  default_config: AgentConfig;
  is_builtin: boolean;
  created_at: Date;
}
```

### 12.3 与 Runtime 的调用关系

```text
Runtime 执行任务时：
1. 根据 task.assigned_agent_id 查询 AgentStation。
2. 获取 AgentStation.system_prompt 作为 System Prompt。
3. 获取 AgentStation.default_model_id，通过 Model Router 选择模型。
4. 获取 AgentStation.allowed_tools，限制工具调用范围。
5. 获取 AgentStation.max_steps_per_task，限制执行步数。
6. 获取 AgentStation.output_format_requirement，校验输出格式。
7. 获取 AgentStation.allow_handoff，判断是否允许触发 Handoff。
8. 获取 AgentStation.handoff_threshold_tokens，判断 Handoff 触发条件。
```

### 12.4 与 Workspace 的调用关系

```text
Workspace 渲染时：
1. 查询 AgentStation 列表，渲染 Agent Station 卡片。
2. 获取 AgentStation.status，渲染状态灯。
3. 获取 AgentStation.current_task_id，绑定当前 TaskCard。
4. 获取 AgentStation.default_model_id，查询 Model 渲染 WorkerBadge。
5. 获取 AgentStation.handoff_enabled，判断是否显示 Handoff 操作。
```

### 12.5 与 Handoff Manager 的调用关系

```text
Handoff Manager 判断时：
1. 查询 from_agent.allow_handoff，判断原 Agent 是否允许交接。
2. 查询 to_agent 的配置，判断接手 Agent 是否可用。
3. 查询 from_agent.handoff_threshold_tokens，判断是否达到触发阈值。
```

---

## 13. 权限与安全规则

### 13.1 当前阶段（本地单用户）

MVP 阶段为本地单用户，不做复杂权限系统：

1. 所有用户都可以查看、创建、编辑、启用、禁用 Agent。
2. 没有角色分级（admin / user / viewer）。
3. 没有审批流程。

### 13.2 安全约束

1. **高风险工具限制**：
   - file_delete、terminal_execute 等高风险工具默认不允许。
   - 用户启用高风险工具时，二次确认。
   - 高风险工具在 AgentDetail 中用红色标识。

2. **模型绑定校验**：
   - default_model_id 必须指向已启用模型。
   - backup_model_ids 只能包含已启用模型。
   - 不允许绑定 disabled 模型。

3. **Prompt 安全检查**：
   - System Prompt 不能为空。
   - System Prompt 长度限制：建议不超过 4000 tokens。
   - 不允许在 Prompt 中硬编码 API Key 或敏感信息。

4. **执行限制**：
   - max_steps_per_task 上限建议 50，防止无限循环。
   - max_tool_calls_per_task 上限建议 20，防止工具滥用。

5. **禁用保护**：
   - 有 running 任务的 Agent 不建议禁用。
   - 强制禁用时，running 任务标记为 failed 或触发 Handoff。

### 13.3 配置变更生效规则

1. **立即生效**：name、description、status（启用/禁用）。
2. **对新任务生效**：default_model_id、backup_model_ids、allowed_tools、system_prompt、output_format、max_steps、handoff 配置。
3. **不影响进行中任务**：进行中任务继续使用创建时的配置。

---

## 14. MVP 范围

### 14.1 MVP-A 必须实现

| 功能 | 说明 |
|------|------|
| Agent 列表 | 展示所有 Agent Station，支持筛选 |
| Agent 详情 | 查看 Agent 完整配置和状态 |
| 默认 Agent 模板 | 预置 Planner、Coder、Reviewer、Summarizer、Supervisor 模板 |
| 模型绑定 | 设置默认模型和备用模型 |
| 工具权限 | 选择允许使用的工具 |
| System Prompt | 编辑角色系统 Prompt |
| 输出格式 | 设置输出格式要求 |
| 最大执行步数 | 设置 max_steps_per_task |
| Handoff 开关 | 设置是否允许 Handoff |
| 启用/禁用 | 控制 Agent 是否可用 |

### 14.2 MVP-B 建议实现

| 功能 | 说明 |
|------|------|
| 自定义 Agent 创建 | 基于模板或完全自定义创建新 Agent |
| Handoff 阈值 | 设置 handoff_threshold_tokens |
| Agent 历史统计 | 展示完成任务数、交接次数、平均 token |
| 模板扩展 | 增加 Research Agent 模板 |
| 配置导入导出 | 导出 Agent 配置为 YAML/JSON |
| 批量操作 | 批量启用/禁用 |

---

## 15. 暂缓范围

当前阶段明确不做：

1. **Agent 自动生成**：不做 AI 自动创建 Agent 配置。
2. **Agent 自动优化 Prompt**：不做元学习自动改 Prompt。
3. **Agent 市场**：不做第三方 Agent 导入或分享。
4. **企业级 RBAC**：不做多用户权限分级。
5. **动态角色切换**：Agent 创建后 role 建议固定。
6. **自动模型组合发现**：不做自动测试最佳模型组合。
7. **Agent 版本管理**：暂不支持配置版本历史。
8. **Agent 克隆**：暂不支持复制现有 Agent。
9. **Agent 性能 A/B 测试**：暂不支持对比不同配置的表现。
10. **团队协作审批**：单用户场景不需要审批流。

---

## 16. 验收标准

### 16.1 功能验收

1. Agent Registry 页面可以展示所有 Agent Station 列表。
2. 列表显示 Agent 名称、角色、状态、默认模型、Handoff 开关状态。
3. 用户可以查看 Agent 详情，包括完整配置和历史统计。
4. 系统预置 Planner、Coder、Reviewer、Summarizer、Supervisor 默认模板。
5. 用户可以为 Agent 设置默认模型和备用模型。
6. 用户可以为 Agent 配置允许使用的工具列表。
7. 用户可以为 Agent 编辑 System Prompt。
8. 用户可以为 Agent 设置输出格式。
9. 用户可以为 Agent 设置最大执行步数。
10. 用户可以为 Agent 开启或关闭 Handoff。
11. 用户可以启用或禁用 Agent。
12. 禁用 Agent 前，系统检查是否有 running 任务。

### 16.2 前端验收

1. AgentList 组件可以正确渲染所有 Agent。
2. AgentConfigForm 组件可以正确展示和编辑 Agent 配置。
3. ModelBindingSelector 组件可以正确选择默认模型和备用模型。
4. ToolPermissionSelector 组件可以正确选择工具权限。
5. HandoffToggle 组件可以正确控制 Handoff 开关和阈值。
6. 禁用状态的 Agent 在列表中显示为灰色。
7. running 状态的 Agent 显示蓝色状态灯。

### 16.3 后端验收

1. `GET /agents` 返回 Agent 列表。
2. `GET /agents/:agentId` 返回 Agent 详情。
3. `POST /agents` 可以创建新 Agent。
4. `PATCH /agents/:agentId` 可以更新 Agent 配置。
5. `PATCH /agents/:agentId/status` 可以启用/禁用 Agent。
6. `GET /agents/templates` 返回默认模板列表。
7. 创建 Agent 时，系统校验必填字段和模型可用性。
8. 更新 Agent 的 handoff_enabled 时，不影响进行中任务。

### 16.4 数据验收

1. AgentStation 数据对象包含所有必填字段。
2. default_model_id 关联的模型必须存在且已启用。
3. backup_model_ids 中的模型必须存在且已启用，且不与 default_model_id 重复。
4. allowed_tools 中的工具必须在系统工具列表中。
5. role 字段不能为空，且符合系统支持的角色类型。

### 16.5 集成验收

1. Runtime 执行任务时，可以正确读取 AgentStation 配置。
2. Model Router 可以根据 AgentStation.default_model_id 和 backup_model_ids 选择模型。
3. Handoff Manager 可以根据 AgentStation.allow_handoff 判断是否允许交接。
4. Workspace 可以根据 AgentStation 列表渲染 Agent Station 卡片。
5. Task 分配时，系统根据 AgentStation.status 判断是否可分配。

### 16.6 Demo 验收

必须能稳定演示以下流程：

```text
1. 用户进入 Agent Registry 页面。
2. 看到预置的 Planner、Coder、Reviewer、Summarizer、Supervisor Agent。
3. 点击 Coder Agent，查看详情。
4. 看到 Coder Agent 的默认模型是 DeepSeek Coder，备用模型是 Claude 和 GPT。
5. 看到 Coder Agent 允许使用 file_read、file_write、terminal_execute。
6. 看到 Coder Agent 的 System Prompt。
7. 看到 Coder Agent 允许 Handoff，阈值 80000 tokens。
8. 用户编辑 Coder Agent，将 Handoff 阈值改为 60000。
9. 保存成功，配置更新。
10. 用户创建一个新的自定义 Agent，选择 Coder 模板。
11. 修改名称为 "Frontend Coder"，默认模型改为 GPT-4。
12. 保存成功，新 Agent 出现在列表中。
13. 用户禁用 Summarizer Agent。
14. Summarizer Agent 状态变为 disabled，Workspace 中显示为灰色。
15. Runtime 不再分配任务给 Summarizer Agent。
```

如果上述流程可稳定跑通，Agent Registry MVP 即视为完成。
