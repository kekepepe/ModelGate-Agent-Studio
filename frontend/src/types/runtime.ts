export interface ExecutionStep {
  task_id: string;
  status: string;
  output?: string | null;
  tokens_used: number;
  duration_ms?: number | null;
  model_name?: string | null;
  worker_id?: string | null;
  quota_status?: string | null;
  is_handoff: boolean;
}

export interface GoalExecutionResult {
  goal_id: string;
  status: string;
  tasks_completed: number;
  tasks_failed: number;
  tasks_handoff: number;
  total_tokens_used: number;
  total_duration_ms: number;
  execution_log: ExecutionStep[];
}

export interface RuntimeStatusResponse {
  goal_id: string;
  goal_title: string;
  goal_status: string;
  current_task_id?: string | null;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  running_tasks: number;
  handoff_tasks: number;
  handoff_count: number;
  total_tokens_used: number;
  log_count: number;
  model_call_count: number;
  error_count: number;
  final_output?: string | null;
  error_message?: string | null;
  quota_status?: string | null;
  final_summary?: FinalSummary | null;
}

export interface FinalSummary {
  completed: string[];
  incomplete: string[];
  quality: {
    status: string;
    passed?: boolean | null;
    summary?: string | null;
    reviewer_model_id?: string | null;
  };
  risks: string[];
  models: Array<{ id: string; name: string; cost_level?: number | null }>;
  handoff_count: number;
  cost: { currency_estimate?: number | null; available: boolean; note: string };
}
