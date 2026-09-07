export type AgentRole = 'planner' | 'coder' | 'reviewer' | 'research' | 'summarizer' | 'supervisor' | string;

export type AgentStatus = 'idle' | 'running' | 'handoff' | 'blocked' | 'error' | 'disabled' | string;

export interface AgentStation {
  id: string;
  name: string;
  role: AgentRole;
  description: string;
  status: AgentStatus;
  current_task_id?: string;
  default_model_id: string;
  backup_model_ids: string[];
  allowed_tools: string[];
  capability_profile?: Record<string, number>;
  workspace_permissions?: string[];
  input_types?: string[];
  output_types?: string[];
  max_concurrency?: number;
  system_prompt: string;
  output_format?: string;
  max_steps_per_task: number;
  max_tool_calls_per_task?: number;
  max_tokens_per_task: number;
  max_duration_seconds: number;
  max_consecutive_failures: number;
  allow_handoff: boolean;
  handoff_threshold_tokens?: number;
  is_enabled: boolean;
  total_tasks_completed: number;
  total_tasks_failed: number;
  total_handoffs_initiated: number;
  average_tokens_per_task?: number;
  average_duration_ms?: number;
  average_cost_usd?: number;
  created_at?: string;
  updated_at?: string;
}

export interface AgentListItem {
  id: string;
  name: string;
  slug?: string | null;
  role: AgentRole;
  description?: string;
  status: AgentStatus;
  default_model_id: string;
  is_enabled: boolean;
  is_builtin?: boolean;
  current_task_id?: string;
  total_tasks_completed: number;
  capabilities?: string[];
  max_concurrency?: number;
  created_at?: string;
}

export interface AgentTemplate {
  id: string;
  name: string;
  role: string;
  description: string;
  default_config: Partial<AgentStation>;
}

export interface AgentCreateData {
  name: string;
  role?: string;
  description?: string;
  default_model_id?: string;
  backup_model_ids?: string[];
  allowed_tools?: string[];
  capability_profile?: Record<string, number>;
  workspace_permissions?: string[];
  input_types?: string[];
  output_types?: string[];
  max_concurrency?: number;
  system_prompt?: string;
  output_format?: string;
  max_steps_per_task?: number;
  max_tokens_per_task?: number;
  max_duration_seconds?: number;
  max_consecutive_failures?: number;
  allow_handoff?: boolean;
  handoff_threshold_tokens?: number;
  template_id?: string;
}

export interface AgentUpdateData {
  name?: string;
  role?: string;
  description?: string;
  default_model_id?: string;
  backup_model_ids?: string[];
  allowed_tools?: string[];
  capability_profile?: Record<string, number>;
  workspace_permissions?: string[];
  input_types?: string[];
  output_types?: string[];
  max_concurrency?: number;
  system_prompt?: string;
  output_format?: string;
  max_steps_per_task?: number;
  max_tokens_per_task?: number;
  max_duration_seconds?: number;
  max_consecutive_failures?: number;
  allow_handoff?: boolean;
  handoff_threshold_tokens?: number;
}

export interface AgentFilters {
  role?: string;
  status?: string;
  is_enabled?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
}

export const ROLE_CONFIG: Record<string, { label: string; color: string; bg: string; text: string; iconColor: string }> = {
  planner: { label: '规划师', color: '#e0f2fe', bg: 'bg-sky-100', text: 'text-sky-700', iconColor: '#0369a1' },
  coder: { label: '编码师', color: '#ede9fe', bg: 'bg-lavender-100', text: 'text-lavender-800', iconColor: '#5b4ba4' },
  reviewer: { label: '审查员', color: '#fef3c7', bg: 'bg-amber-100', text: 'text-amber-800', iconColor: '#92400e' },
  research: { label: '研究员', color: '#dcfce7', bg: 'bg-green-100', text: 'text-green-800', iconColor: '#166534' },
  summarizer: { label: '摘要员', color: '#f3e8ff', bg: 'bg-purple-100', text: 'text-purple-800', iconColor: '#7e22ce' },
  supervisor: { label: '监督者', color: '#fee2e2', bg: 'bg-red-100', text: 'text-red-800', iconColor: '#991b1b' },
};

export const STATUS_CONFIG: Record<string, { label: string; dot: string; text: string; animate?: boolean }> = {
  idle: { label: '空闲', dot: 'bg-green-500', text: 'text-green-700' },
  running: { label: '执行中', dot: 'bg-blue-500', text: 'text-blue-700', animate: true },
  handoff: { label: '交接中', dot: 'bg-lavender-500', text: 'text-lavender-800' },
  blocked: { label: '阻塞', dot: 'bg-amber-500', text: 'text-amber-700' },
  error: { label: '错误', dot: 'bg-red-500', text: 'text-red-700' },
  disabled: { label: '禁用', dot: 'bg-stone-400', text: 'text-stone-500' },
};

export const MOCK_MODELS = [
  { id: 'claude-3-opus', name: 'Claude 3 Opus', provider: 'Anthropic' },
  { id: 'gpt-4-turbo', name: 'GPT-4 Turbo', provider: 'OpenAI' },
  { id: 'deepseek-coder', name: 'DeepSeek Coder', provider: 'DeepSeek' },
  { id: 'kimi-long-context', name: 'Kimi Long Context', provider: 'Moonshot' },
  { id: 'claude-3-haiku', name: 'Claude 3 Haiku', provider: 'Anthropic' },
  { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', provider: 'OpenAI' },
];

export const MOCK_TOOLS = [
  { id: 'file_read', name: 'file_read', description: '读取文件内容', category: '文件操作', risk_level: 'low' as const },
  { id: 'file_write', name: 'file_write', description: '写入文件内容', category: '文件操作', risk_level: 'low' as const },
  { id: 'file_delete', name: 'file_delete', description: '删除文件', category: '文件操作', risk_level: 'high' as const },
  { id: 'terminal_execute', name: 'terminal_execute', description: '执行终端命令', category: '终端', risk_level: 'high' as const },
  { id: 'web_search', name: 'web_search', description: '网络搜索', category: '网络', risk_level: 'low' as const },
  { id: 'diff_view', name: 'diff_view', description: '查看代码差异', category: '代码', risk_level: 'low' as const },
];

export const AGENT_CAPABILITIES = [
  'planning', 'research', 'code_read', 'code_edit', 'test', 'review',
  'security_review', 'document_write', 'data_analysis', 'tool_orchestration',
  'supervision', 'direct',
];
