export type GoalStatus = 'idle' | 'planning' | 'running' | 'paused' | 'waiting' | 'waiting_approval' | 'replanning' | 'revision_required' | 'blocked' | 'handoff' | 'reviewing' | 'completed' | 'failed' | 'cancelled';
export type TaskStatus = 'pending' | 'ready' | 'assigned' | 'running' | 'waiting_tool' | 'waiting_approval' | 'verifying' | 'replanning' | 'revision_required' | 'blocked' | 'completed' | 'completed_verified' | 'completed_unverified' | 'failed' | 'handoff' | 'skipped' | 'cancelled';
export type WorkerStatus = 'idle' | 'running' | 'handoff_required' | 'completed' | 'failed' | 'cancelled';

export interface Goal {
  id: string;
  title: string;
  description?: string | null;
  team_preset?: string | null;
  status: GoalStatus;
  execution_mode?: 'live' | 'sandbox' | 'dry_run' | 'mock';
  workspace_root?: string | null;
  final_verification_status?: string | null;
  budget_tokens?: number;
  budget_cost_usd?: number | null;
  max_duration_seconds?: number;
  max_parallel_tasks?: number;
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
  workspace_scope?: string | null;
  handoff?: WorkspaceHandoff | null;
  handoffs?: WorkspaceHandoff[];
  model_id?: string | null;
  quota?: WorkspaceQuota | null;
  routing_decision?: WorkspaceRoutingDecision | null;
  context?: string | null;
  recent_logs?: WorkspaceLog[];
  dependencies?: string[];
  acceptance_criteria?: Array<Record<string, unknown>>;
  verification_status?: string | null;
  artifacts?: Array<{ id: string; type: string; path?: string | null; checksum?: string | null; verification_status?: string | null }>;
  verification_results?: Array<{ id: string; criterion_type: string; command_or_rule: string; status: string; evidence?: string | null; exit_code?: number | null }>;
  context_runs?: ContextRun[];
  task_type?: string;
  blocked_reason?: string | null;
  changed_files?: string[];
  test_status?: string | null;
  latest_tool_call?: { id: string; tool_name: string; status: string; latency_ms: number; error_message?: string | null; result?: { changed_files?: string[] } } | null;
  recent_tool_calls?: Array<{ id: string; tool_name: string; status: string; latency_ms: number; error_message?: string | null; result?: { changed_files?: string[] } }>;
  plan_version_id?: string | null;
  plan_task_id?: string | null;
  plan_source?: string | null;
  selection_decision?: AgentSelectionDecision | null;
}

export interface PlanTask {
  id: string;
  client_task_id: string;
  objective: string;
  task_type: string;
  required_capabilities: string[];
  required_tools: string[];
  dependencies: string[];
  acceptance_criteria: Array<Record<string, unknown>>;
  risk_level: string;
  parallel_safe: boolean;
  context_query: string;
  approval_required: boolean;
  workspace_scope?: string | null;
  merge_strategy?: string | null;
  runtime_task_id?: string | null;
  source: string;
}

export interface ExecutionPlan {
  id: string;
  plan_id: string;
  goal_id: string;
  version: number;
  status: string;
  task_mode: 'direct' | 'single_agent' | 'sequential_multi_agent' | 'parallel_multi_agent';
  goal_summary: string;
  assumptions: string[];
  required_context: string[];
  activation_reason: string;
  final_acceptance_criteria: Array<Record<string, unknown>>;
  human_approval_points: string[];
  estimated_cost: Record<string, unknown>;
  fallback_reason?: string | null;
  planner_type: string;
  confirmed_at?: string | null;
  tasks: PlanTask[];
}

export interface PlanVersionSummary {
  id: string;
  plan_id: string;
  version: number;
  status: string;
  task_mode: string;
  activation_reason: string;
  planner_type: string;
  created_at?: string | null;
}

export interface PlanChange {
  id: string;
  goal_id: string;
  from_plan_version_id?: string | null;
  to_plan_version_id: string;
  change_type: string;
  reason: string;
  evidence: Array<Record<string, unknown>>;
  retained_task_ids: string[];
  cancelled_task_ids: string[];
  added_task_ids: string[];
  replaced_task_ids: string[];
  created_at?: string | null;
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
  workspace_scope?: string | null;
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
  workspace_scope?: string | null;
  step_count?: number;
  failure_count?: number;
  last_observation?: string | null;
  next_action?: string | null;
}

export interface WorkspaceState {
  goal: Goal | null;
  tasks: WorkspaceTask[];
  agents: WorkspaceAgent[];
  workers: WorkspaceWorker[];
  handoffs: WorkspaceHandoff[];
  active_plan?: ExecutionPlan | null;
  plan_versions?: PlanVersionSummary[];
  task_mode?: ExecutionPlan['task_mode'] | null;
  activation_reason?: string | null;
  task_edges?: Array<{ source: string; target: string; source_client_task_id: string; target_client_task_id: string }>;
  parallel_groups?: Array<{ id: string; task_ids: string[] }>;
  replan_events?: PlanChange[];
  completion_evidence?: {
    allowed: boolean;
    status: string;
    goal_status: string;
    reason: string;
    failed_task_ids: string[];
    tasks: Array<{
      task_id: string;
      title: string;
      status: string;
      verification_status?: string | null;
      verification_required: boolean;
      satisfied: boolean;
      reasons: string[];
    }>;
  } | null;
  context_runs?: ContextRun[];
  selection_decisions?: AgentSelectionDecision[];
  multi_agent_metrics?: MultiAgentMetrics;
}

export interface AgentSelectionDecision {
  id: string;
  task_id: string;
  required_capabilities: string[];
  required_tools: string[];
  candidates: Array<{
    agent_id: string; agent_name: string; role: string; eligible: boolean;
    elimination_reasons: string[]; score: number; selected_model_id: string;
    selected_model_name: string; score_breakdown: Record<string, number>;
  }>;
  selected_agent_id: string;
  selected_model_id: string;
  backup_model_ids: string[];
  score: number;
  selection_reason: string;
  fallback_entry: { agent_ids?: string[]; model_ids?: string[]; handoff_allowed?: boolean; reason?: string };
  created_at?: string | null;
}

export interface MultiAgentMetrics {
  mode: ExecutionPlan['task_mode'];
  why_multi_agent: string;
  activated_agent_count: number;
  active_agent_count: number;
  active_parallelism: number;
  coordination_task_count: number;
  coordination_tokens: number;
  productive_tokens: number;
  coordination_token_ratio: number;
  coordination_duration_ms: number;
  parallel_task_count: number;
  single_agent_serial_baseline_ms: number;
  parallel_observed_estimate_ms: number;
  potential_parallel_saving_ms: number;
  estimated_net_time_benefit_ms: number;
  benefit_positive: boolean;
  measurement_note: string;
  mode_comparison: Record<'single_agent' | 'sequential_multi_agent' | 'parallel_multi_agent', { duration_ms: number; tokens: number; basis: string }>;
}

export interface ContextRun {
  id: string;
  goal_id?: string | null;
  task_id?: string | null;
  agent_id?: string | null;
  query: string;
  policy: string;
  filters: Record<string, unknown>;
  latency_ms: number;
  token_budget: number;
  token_count: number;
  status: string;
  created_at?: string | null;
  items: Array<{
    id: string;
    rank: number;
    score: number;
    used: boolean;
    citation?: string | null;
    token_count: number;
    source_id: string;
    source_name?: string | null;
    chunk_id?: string | null;
    path?: string | null;
    content?: string | null;
  }>;
}

export const GOAL_STATUS_LABELS: Record<string, string> = {
  idle: '未启动',
  planning: '规划中',
  running: '运行中',
  paused: '已暂停',
  waiting: '等待中',
  handoff: '交接中',
  reviewing: '审查中',
  completed: '已完成',
  completed_verified: '已验证完成',
  completed_unverified: '未验证完成',
  verifying: '验证中',
  revision_required: '需要修订',
  blocked: '已阻塞',
  failed: '失败',
  cancelled: '已停止',
};

export const GOAL_STATUS_COLORS: Record<string, string> = {
  idle: 'bg-stone-100 text-stone-600 border-stone-200',
  planning: 'bg-purple-100 text-purple-700 border-purple-200',
  running: 'bg-blue-100 text-blue-700 border-blue-200',
  paused: 'bg-stone-100 text-stone-700 border-stone-300',
  waiting: 'bg-amber-100 text-amber-700 border-amber-200',
  handoff: 'bg-purple-100 text-purple-700 border-purple-200',
  reviewing: 'bg-orange-100 text-orange-700 border-orange-200',
  completed: 'bg-green-100 text-green-700 border-green-200',
  failed: 'bg-red-100 text-red-700 border-red-200',
  cancelled: 'bg-stone-100 text-stone-600 border-stone-300',
};

export const TASK_STATUS_LABELS: Record<string, string> = {
  pending: '待处理',
  ready: '就绪',
  assigned: '已分配',
  running: '执行中',
  waiting_tool: '等待工具',
  waiting_approval: '等待审批',
  verifying: '验证中',
  revision_required: '需要修订',
  blocked: '已阻塞',
  completed: '已完成',
  completed_verified: '已验证完成',
  completed_unverified: '未验证完成',
  failed: '失败',
  handoff: '交接中',
  cancelled: '已取消',
};

export const TASK_STATUS_ICONS: Record<string, string> = {
  pending: '⏸',
  ready: '◌',
  assigned: '📋',
  running: '▶',
  waiting_tool: '⏳',
  waiting_approval: '⚠',
  verifying: '🔎',
  revision_required: '↩',
  blocked: '⛔',
  completed: '✓',
  completed_verified: '✓',
  completed_unverified: '⚠',
  failed: '✗',
  handoff: '🔄',
  cancelled: '—',
};

export const TASK_STATUS_BORDERS: Record<string, string> = {
  pending: 'border-dashed border-stone-300',
  assigned: 'border-stone-400',
  running: 'border-blue-500 shadow-blue-100 shadow-md',
  completed: 'border-green-500',
  completed_verified: 'border-green-500',
  completed_unverified: 'border-amber-500',
  verifying: 'border-blue-500',
  revision_required: 'border-amber-500',
  blocked: 'border-red-500',
  failed: 'border-red-500',
  handoff: 'border-purple-500 shadow-purple-100 shadow-md',
};

export const TASK_STATUS_BG: Record<string, string> = {
  pending: 'bg-white',
  assigned: 'bg-white',
  running: 'bg-blue-50',
  completed: 'bg-green-50',
  completed_verified: 'bg-green-50',
  completed_unverified: 'bg-amber-50',
  verifying: 'bg-blue-50',
  revision_required: 'bg-amber-50',
  blocked: 'bg-red-50',
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
