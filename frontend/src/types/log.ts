export type LogEventType =
  | 'model_call'
  | 'agent_step'
  | 'tool_call'
  | 'task_status_change'
  | 'quota_status_change'
  | 'handoff_created'
  | 'handoff_completed'
  | 'error'
  | 'supervisor_review'
  | 'memory_write_candidate';

export type LogEventStatus =
  | 'success'
  | 'failed'
  | 'error'
  | 'info'
  | 'warning'
  | 'pending'
  | 'running'
  | 'completed'
  | 'cancelled'
  | 'timeout'
  | 'rate_limited'
  | 'quota_exceeded'
  | 'validation_error'
  | 'unknown'
  | 'started'
  | 'transition'
  | 'detected'
  | 'created'
  | 'accepted'
  | 'rejected'
  | 'approved'
  | 'needs_revision'
  | 'skipped';

export interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}

export interface ExecutionLog {
  id: string;
  goal_id?: string | null;
  task_id?: string | null;
  agent_id?: string | null;
  worker_id?: string | null;
  model_id?: string | null;
  handoff_id?: string | null;
  event_type: LogEventType;
  event_status: LogEventStatus;
  input_summary?: string | null;
  output_summary?: string | null;
  token_usage?: TokenUsage | null;
  latency_ms?: number | null;
  error_type?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  tool_name?: string | null;
  quota_status?: string | null;
  handoff_status?: string | null;
  metadata?: Record<string, unknown> | null;
  routing_info?: Record<string, unknown> | null;
  created_at?: string | null;
  agent_name?: string | null;
  task_title?: string | null;
  model_name?: string | null;
}

export interface LogFilters {
  goal_id?: string;
  task_id?: string;
  agent_id?: string;
  model_id?: string;
  handoff_id?: string;
  event_type?: string;
  event_status?: string;
  start_time?: string;
  end_time?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface LogListResponse {
  items: ExecutionLog[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TimelineEvent {
  time: string;
  event_type: string;
  event_status: string;
  agent_id?: string | null;
  model_id?: string | null;
  summary: string;
  icon_type: string;
}

export interface TimelineSummary {
  total_duration_ms: number;
  total_tokens: number;
  model_call_count: number;
  handoff_count: number;
  error_count: number;
}

export interface TaskTimelineResponse {
  events: TimelineEvent[];
  summary: TimelineSummary;
}

export const LOG_EVENT_TYPE_LABELS: Record<string, string> = {
  model_call: '模型调用',
  agent_step: 'Agent 步骤',
  tool_call: '工具调用',
  task_status_change: '任务状态变更',
  quota_status_change: '额度状态变更',
  handoff_created: '交接创建',
  handoff_completed: '交接完成',
  error: '错误',
  supervisor_review: '审核',
  memory_write_candidate: '记忆候选',
};

export const LOG_EVENT_STATUS_LABELS: Record<string, string> = {
  success: '成功',
  failed: '失败',
  error: '错误',
  info: '信息',
  warning: '警告',
  pending: '等待中',
  running: '运行中',
  completed: '已完成',
  cancelled: '已取消',
  timeout: '超时',
  rate_limited: '限流',
  quota_exceeded: '额度耗尽',
  validation_error: '校验错误',
  unknown: '未知',
  started: '开始',
  transition: '状态变更',
  detected: '已检测',
  created: '已创建',
  accepted: '已接受',
  rejected: '已拒绝',
  approved: '已通过',
  needs_revision: '需修改',
  skipped: '已跳过',
};

export const LOG_EVENT_TYPE_ICONS: Record<string, string> = {
  model_call: '🧠',
  agent_step: '🤖',
  tool_call: '🔧',
  task_status_change: '📋',
  quota_status_change: '💰',
  handoff_created: '🔄',
  handoff_completed: '✓',
  error: '⚠',
  supervisor_review: '👁',
  memory_write_candidate: '📝',
};

export const LOG_EVENT_STATUS_COLORS: Record<string, string> = {
  success: 'bg-green-100 text-green-800 border-green-200',
  failed: 'bg-red-100 text-red-800 border-red-200',
  error: 'bg-red-100 text-red-800 border-red-200',
  info: 'bg-sky-100 text-sky-700 border-sky-200',
  warning: 'bg-amber-100 text-amber-800 border-amber-200',
  pending: 'bg-amber-100 text-amber-800 border-amber-200',
  running: 'bg-lavender-100 text-lavender-800 border-lavender-200',
  completed: 'bg-green-100 text-green-800 border-green-200',
  cancelled: 'bg-stone-100 text-stone-600 border-stone-200',
  timeout: 'bg-red-100 text-red-800 border-red-200',
  rate_limited: 'bg-amber-100 text-amber-800 border-amber-200',
  quota_exceeded: 'bg-red-100 text-red-800 border-red-200',
  validation_error: 'bg-red-100 text-red-800 border-red-200',
  unknown: 'bg-stone-100 text-stone-600 border-stone-200',
  started: 'bg-lavender-100 text-lavender-800 border-lavender-200',
  transition: 'bg-stone-100 text-stone-600 border-stone-200',
  detected: 'bg-sky-100 text-sky-700 border-sky-200',
  created: 'bg-lavender-100 text-lavender-800 border-lavender-200',
  accepted: 'bg-green-100 text-green-800 border-green-200',
  rejected: 'bg-red-100 text-red-800 border-red-200',
  approved: 'bg-green-100 text-green-800 border-green-200',
  needs_revision: 'bg-amber-100 text-amber-800 border-amber-200',
  skipped: 'bg-stone-100 text-stone-600 border-stone-200',
};

export const TIMELINE_NODE_COLORS: Record<string, string> = {
  model_call: 'bg-blue-500',
  agent_step: 'bg-green-500',
  tool_call: 'bg-cyan-500',
  handoff_created: 'bg-purple-500',
  handoff_completed: 'bg-purple-500',
  error: 'bg-red-500',
  task_status_change: 'bg-stone-400',
  quota_status_change: 'bg-amber-500',
  supervisor_review: 'bg-sky-500',
  memory_write_candidate: 'bg-lavender-500',
};
