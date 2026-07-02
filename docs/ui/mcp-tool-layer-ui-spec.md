# MCP Tool Layer UI Spec

> 所属产品：ModelGate Agent Studio
>
> 文档定位：Tool Manager 页面和 Workspace 工具调用展示的前端 UI 规范。

---

## 1. Tool Manager 页面

### 1.1 路由

```
/tools → ToolManagerPage
```

### 1.2 页面布局

```
┌─────────────────────────────────────────────────────────────┐
│  Tool Manager                                    [+ 注册工具] │
├─────────────────────────────────────────────────────────────┤
│  [Category ▼]  [Risk Level ▼]                    [刷新]      │
├─────────────────────────────────────────────────────────────┤
│  Name        │ Display   │ Category │ Risk   │ Status │ Op  │
│  file_read   │ 文件读取  │ 文件操作  │ low    │ ✅    │ ⋯  │
│  file_search │ 文件搜索  │ 文件操作  │ low    │ ✅    │ ⋯  │
│  git_diff    │ Git 差异  │ 代码     │ low    │ ✅    │ ⋯  │
│  test_runner │ 测试运行  │ 测试     │ medium │ ✅    │ ⋯  │
├─────────────────────────────────────────────────────────────┤
│                    < 1 / 1 >                                 │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 状态定义

**列表状态：**
- **加载中**：骨架屏
- **空状态**：图标 + "暂无注册工具" + "注册第一个工具" 按钮
- **失败状态**：错误提示 + 重试按钮
- **正常**：表格展示

**每行操作：**
- 编辑（铅笔图标）
- 启用/禁用 toggle
- 删除（垃圾桶图标）+ 确认弹窗

### 1.4 添加/编辑工具模态框

```
┌──────────────────────────────────────┐
│  注册工具 / 编辑工具                  │
├──────────────────────────────────────┤
│  Name *                              │
│  [________________]                  │
│                                      │
│  Display Name *                      │
│  [________________]                  │
│                                      │
│  Description                         │
│  [________________]                  │
│                                      │
│  Category *          Risk Level *    │
│  [文件操作 ▼]        [low ▼]         │
│                                      │
│  Parameters (JSON Schema)            │
│  ┌──────────────────────────────┐    │
│  │ {                            │    │
│  │   "path": {...}              │    │
│  │ }                            │    │
│  └──────────────────────────────┘    │
│                                      │
│  [取消]                    [保存]    │
└──────────────────────────────────────┘
```

**校验规则：**
- Name: 必填，snake_case，唯一
- Display Name: 必填
- Category: 必选
- Risk Level: 必选（low/medium/high）
- Parameters: 必填，合法 JSON
- 保存按钮 disabled 直到必填项填写完整

**状态：**
- 提交中：按钮显示 spinner + "保存中..."
- 成功：关闭弹窗，刷新列表，toast 提示
- 失败：弹窗内红色错误文字

### 1.5 删除确认

```
┌──────────────────────────────────────┐
│  确认删除                            │
│                                      │
│  确定要删除工具 "file_write" 吗？     │
│  此操作不可撤销。                    │
│                                      │
│  [取消]                    [删除]    │
└──────────────────────────────────────┘
```

---

## 2. Workspace Task 工具调用记录

### 2.1 位置

在 TaskDetailPanel 底部，位于 task output 之后、handoff history 之前。

### 2.2 设计

```
┌─────────────────────────────────────────────┐
│  🔧 工具调用记录 (3)                         │
├─────────────────────────────────────────────┤
│  ● 12:30:01  file_read          ✅ 45ms     │
│    参数: {"path": "src/main.ts"}             │
│    结果: "import React from 'react'...       │
│                                              │
│  ● 12:30:02  file_search        ✅ 12ms     │
│    参数: {"pattern": "*.tsx"}                │
│    结果: "Found 12 files..."                 │
│                                              │
│  ● 12:30:05  test_runner        ❌ 2300ms   │
│    参数: {"command": "npm test"}             │
│    错误: "Test failed: expected..."          │
└─────────────────────────────────────────────┘
```

### 2.3 每条记录

- 时间（HH:MM:SS）
- 工具名称（code 样式 tag）
- 状态：✅ completed（绿色）/ ❌ failed（红色）
- 耗时（ms）
- 可折叠：默认展开参数摘要，点击展开完整输入/输出
- 错误记录：红色背景高亮

### 2.4 状态处理

- **加载中**：骨架屏
- **空状态**：无工具调用时，不渲染此区域
- **错误状态**：区域内错误提示

---

## 3. AgentConfigForm 工具权限调整

### 3.1 现状

Step 2 使用 MOCK_TOOLS 硬编码 6 个工具。

### 3.2 修改后

Step 2 工具权限列表改为调用 `useTools({ is_enabled: true })`，展示 Tool Registry 中的 real tools。

**UI 不变**，仅数据源变更：
- 每个工具一行 checkbox
- 显示 tool.display_name + tool.description
- risk_level 以风险标签展示（low=绿色, medium=黄色, high=红色）

---

## 4. 导航变更

在 App.tsx 导航栏增加 "Tool Manager" 入口，位于 "Handoff" 和 "Logs" 之间。

```
Agent Registry | Model Manager | Model Router | Quota | Handoff | Tools | Logs | Workspace | Evolution
```

---

## 5. 设计约束

- 遵循低饱和、非深色、Claude 风格
- 颜色：risk low=green-500, medium=amber-500, high=red-500
- 状态：enabled=green-500, disabled=stone-400
- 不使用复杂动画
- 表格响应式，小屏幕下 stacking 布局
