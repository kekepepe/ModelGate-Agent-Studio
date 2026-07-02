export interface ToolParameter {
  type: string;
  properties: Record<string, { type: string; description?: string }>;
  required?: string[];
}

export interface ToolDefinition {
  id: string;
  name: string;
  display_name: string;
  description: string;
  category: string;
  risk_level: 'low' | 'medium' | 'high';
  parameters: ToolParameter;
  is_enabled: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ToolCreateData {
  name: string;
  display_name: string;
  description?: string;
  category?: string;
  risk_level?: string;
  parameters?: Record<string, unknown>;
  is_enabled?: boolean;
}

export interface ToolUpdateData {
  display_name?: string;
  description?: string;
  category?: string;
  risk_level?: string;
  parameters?: Record<string, unknown>;
  is_enabled?: boolean;
}

export interface ToolFilters {
  category?: string;
  risk_level?: string;
  is_enabled?: boolean;
  page?: number;
  page_size?: number;
}

export interface ToolListResponse {
  items: ToolDefinition[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ToolCallRecord {
  id: string;
  goal_id?: string | null;
  task_id?: string | null;
  agent_id?: string | null;
  worker_id?: string | null;
  tool_name: string;
  tool_input: Record<string, unknown>;
  tool_output?: string | null;
  status: 'started' | 'completed' | 'failed';
  latency_ms: number;
  error_message?: string | null;
  created_at?: string;
}

export interface ToolCallFilters {
  goal_id?: string;
  task_id?: string;
  agent_id?: string;
  tool_name?: string;
  page?: number;
  page_size?: number;
}

export interface ToolCallListResponse {
  items: ToolCallRecord[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
