export type GoalStatus = 'idle' | 'planning' | 'running' | 'waiting' | 'handoff' | 'reviewing' | 'completed' | 'failed';
export type TaskStatus = 'pending' | 'assigned' | 'running' | 'completed' | 'failed' | 'handoff';
export type WorkerStatus = 'idle' | 'running' | 'handoff_required' | 'completed' | 'failed';

export interface Goal {
  id: string;
  title: string;
  description?: string | null;
  status: GoalStatus;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface WorkspaceTask {
  id: string;
  goal_id: string;
  title: string;
  description?: string | null;
  status: TaskStatus;
  assigned_agent_id?: string | null;
  assigned_worker_id?: string | null;
  output?: string | null;
  tokens_used: number;
  duration_ms?: number | null;
  priority: number;
  flow_position?: number;
  created_at?: string | null;
  updated_at?: string | null;
  agent_name?: string | null;
  agent_role?: string | null;
  model_name?: string | null;
  worker_status?: string | null;
  handoff?: WorkspaceHandoff | null;
  handoffs?: WorkspaceHandoff[];
  model_id?: string | null;
  quota?: WorkspaceQuota | null;
  routing_decision?: WorkspaceRoutingDecision | null;
  context?: string | null;
  recent_logs?: WorkspaceLog[];
}

export interface WorkspaceQuota {
  model_id: string;
  quota_status: string;
  usage_percent?: number | null;
  estimated_remaining?: number | null;
  total_tokens: number;
  token_limit?: number | null;
  request_count: number;
}

export interface WorkspaceRoutingDecision {
  selected_model_id?: string;
  backup_model_ids?: string[];
  confidence?: number;
  routing_reason?: {
    summary?: string;
    primary_factors?: string[];
    secondary_factors?: string[];
    tradeoffs?: string[];
  };
  risk_flags?: Array<{ type: string; severity: string; message: string; suggestion?: string }>;
  score_breakdown?: Array<{
    model_id: string;
    model_name: string;
    total_score: number;
    dimension_scores: Array<{ dimension: string; score: number; weight: number; weighted_score: number; reason: string }>;
  }>;
  is_user_override?: boolean;
}

export interface WorkspaceLog {
  id: string;
  event_type: string;
  event_status: string;
  output_summary?: string | null;
  input_summary?: string | null;
  error_message?: string | null;
  quota_status?: string | null;
  model_id?: string | null;
  model_name?: string | null;
  agent_id?: string | null;
  agent_name?: string | null;
  created_at?: string | null;
}

export interface WorkspaceHandoff {
  id: string;
  task_id: string;
  status: string;
  reason: string;
  reason_description?: string | null;
  from_agent_id: string;
  from_agent_name?: string | null;
  from_model_id: string;
  to_agent_id: string;
  to_agent_name?: string | null;
  to_model_id: string;
  result_after_handoff?: string | null;
  created_at?: string | null;
  accepted_at?: string | null;
  completed_at?: string | null;
}

export interface WorkspaceAgent {
  id: string;
  name: string;
  role: string;
  status: string;
  default_model_id?: string | null;
  is_enabled: boolean;
}

export interface WorkspaceWorker {
  id: string;
  agent_id: string;
  model_id: string;
  goal_id?: string | null;
  task_id?: string | null;
  inherited_from_handoff_id?: string | null;
  status: string;
  total_tokens_used: number;
  model_name?: string | null;
  quota_status?: string | null;
}

export interface WorkspaceState {
  goal: Goal | null;
  tasks: WorkspaceTask[];
  agents: WorkspaceAgent[];
  workers: WorkspaceWorker[];
  handoffs: WorkspaceHandoff[];
}

export const GOAL_STATUS_LABELS: Record<string, string> = {
  idle: '未启动',
  planning: '规划中',
  running: '运行中',
  waiting: '等待中',
  handoff: '交接中',
  reviewing: '审查中',
  completed: '已完成',
  failed: '失败',
};

export const GOAL_STATUS_COLORS: Record<string, string> = {
  idle: 'bg-stone-100 text-stone-600 border-stone-200',
  planning: 'bg-purple-100 text-purple-700 border-purple-200',
  running: 'bg-blue-100 text-blue-700 border-blue-200',
  waiting: 'bg-amber-100 text-amber-700 border-amber-200',
  handoff: 'bg-purple-100 text-purple-700 border-purple-200',
  reviewing: 'bg-orange-100 text-orange-700 border-orange-200',
  completed: 'bg-green-100 text-green-700 border-green-200',
  failed: 'bg-red-100 text-red-700 border-red-200',
};

export const TASK_STATUS_LABELS: Record<string, string> = {
  pending: '待处理',
  assigned: '已分配',
  running: '执行中',
  completed: '已完成',
  failed: '失败',
  handoff: '交接中',
};

export const TASK_STATUS_ICONS: Record<string, string> = {
  pending: '⏸',
  assigned: '📋',
  running: '▶',
  completed: '✓',
  failed: '✗',
  handoff: '🔄',
};

export const TASK_STATUS_BORDERS: Record<string, string> = {
  pending: 'border-dashed border-stone-300',
  assigned: 'border-stone-400',
  running: 'border-blue-500 shadow-blue-100 shadow-md',
  completed: 'border-green-500',
  failed: 'border-red-500',
  handoff: 'border-purple-500 shadow-purple-100 shadow-md',
};

export const TASK_STATUS_BG: Record<string, string> = {
  pending: 'bg-white',
  assigned: 'bg-white',
  running: 'bg-blue-50',
  completed: 'bg-green-50',
  failed: 'bg-red-50',
  handoff: 'bg-purple-50',
};

export const WORKER_STATUS_COLORS: Record<string, string> = {
  idle: 'bg-stone-400',
  running: 'bg-blue-500',
  handoff_required: 'bg-purple-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
};
