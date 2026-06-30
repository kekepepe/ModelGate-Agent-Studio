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
