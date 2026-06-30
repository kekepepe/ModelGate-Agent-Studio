export type HandoffStatus = 'requested' | 'generating_summary' | 'ready' | 'accepted' | 'completed' | 'failed';
export type HandoffReason = 'quota_exceeded' | 'error' | 'quality_issue' | 'role_mismatch' | 'manual' | 'context_limit' | 'other';
export type HandoffResult = 'success' | 'partial' | 'failed';

export interface HandoffSummary {
  original_goal: string;
  current_task: string;
  completed_work: string[];
  unfinished_work: string[];
  important_constraints: string[];
  key_decisions: string[];
  errors_and_risks: string[];
  next_suggested_steps: string[];
  context_needed: string[];
}

export interface HandoffTask {
  id: string;
  goal_id: string;
  title: string;
  description: string;
  status: string;
  assigned_agent_id: string;
  assigned_model_id: string;
  assigned_worker_id?: string | null;
  current_output?: string | null;
  error_message?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface WorkerSession {
  id: string;
  agent_id: string;
  model_id: string;
  goal_id: string;
  task_id: string;
  inherited_from_handoff_id?: string | null;
  status: string;
  current_context?: string | null;
  final_output?: string | null;
  error_message?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface HandoffRecord {
  id: string;
  goal_id: string;
  task_id: string;
  from_agent_id: string;
  from_model_id: string;
  from_worker_id?: string | null;
  to_agent_id: string;
  to_model_id: string;
  to_worker_id?: string | null;
  reason: HandoffReason;
  reason_description?: string | null;
  handoff_summary: HandoffSummary;
  status: HandoffStatus;
  result_after_handoff?: HandoffResult | null;
  result_note?: string | null;
  tokens_before_handoff: number;
  tokens_after_handoff: number;
  time_saved_estimate_ms?: number | null;
  error_message?: string | null;
  created_at?: string | null;
  summary_generated_at?: string | null;
  accepted_at?: string | null;
  completed_at?: string | null;
  updated_at?: string | null;
  task?: HandoffTask | null;
  from_agent_name?: string | null;
  from_agent_role?: string | null;
  to_agent_name?: string | null;
  to_agent_role?: string | null;
  worker?: WorkerSession | null;
}

export interface HandoffListItem {
  id: string;
  goal_id: string;
  task_id: string;
  task_title?: string | null;
  from_agent_id: string;
  from_agent_name?: string | null;
  from_model_id: string;
  to_agent_id: string;
  to_agent_name?: string | null;
  to_model_id: string;
  reason: HandoffReason;
  status: HandoffStatus;
  result_after_handoff?: HandoffResult | null;
  created_at?: string | null;
}

export interface HandoffListResponse {
  items: HandoffListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface HandoffFilters {
  goal_id?: string;
  task_id?: string;
  reason?: string;
  status?: string;
  from_agent_id?: string;
  to_agent_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface HandoffTriggerRequest {
  to_agent_id: string;
  to_model_id?: string;
  reason: HandoffReason;
  reason_description?: string;
  include_recent_logs?: boolean;
  include_current_output?: boolean;
}

export interface HandoffAcceptRequest {
  agent_id?: string;
  model_id?: string;
  auto_continue?: boolean;
}

export interface HandoffResultRequest {
  result_after_handoff: HandoffResult;
  status?: 'completed';
  result_note?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
}

export const HANDOFF_STATUS_LABELS: Record<string, string> = {
  requested: '等待处理',
  generating_summary: '生成摘要中',
  ready: '可接手',
  accepted: '已接手',
  completed: '已完成',
  failed: '失败',
};

export const HANDOFF_REASON_LABELS: Record<string, string> = {
  quota_exceeded: '额度不足',
  error: '模型错误',
  quality_issue: '质量问题',
  role_mismatch: '角色不匹配',
  manual: '手动交接',
  context_limit: '上下文限制',
  other: '其他',
};

export const HANDOFF_RESULT_LABELS: Record<string, string> = {
  success: '成功',
  partial: '部分完成',
  failed: '失败',
};

export const HANDOFF_STATUS_CLASSES: Record<string, string> = {
  requested: 'bg-amber-100 text-amber-800 border-amber-200',
  generating_summary: 'bg-lavender-100 text-lavender-800 border-lavender-200',
  ready: 'bg-lavender-100 text-lavender-800 border-lavender-200',
  accepted: 'bg-sky-100 text-sky-700 border-sky-200',
  completed: 'bg-green-100 text-green-800 border-green-200',
  failed: 'bg-red-100 text-red-800 border-red-200',
};

export const HANDOFF_RESULT_CLASSES: Record<string, string> = {
  success: 'bg-green-100 text-green-800 border-green-200',
  partial: 'bg-amber-100 text-amber-800 border-amber-200',
  failed: 'bg-red-100 text-red-800 border-red-200',
};

export const HANDOFF_STATUS_DOTS: Record<string, string> = {
  requested: 'bg-amber-500',
  generating_summary: 'bg-lavender-500 animate-pulse',
  ready: 'bg-lavender-500',
  accepted: 'bg-sky-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
};
