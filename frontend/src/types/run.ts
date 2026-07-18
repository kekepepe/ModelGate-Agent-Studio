export interface WorkspaceRunSummary {
  run_id: string;
  goal_id: string;
  name: string;
  goal_summary: string;
  team_id?: string | null;
  status: string;
  runtime_status?: string | null;
  current_stage: string;
  active_agents: number;
  completed_tasks: number;
  total_tasks: number;
  progress: number;
  total_tokens_used: number;
  token_budget: number;
  quota_percent: number;
  handoff_count: number;
  error_count: number;
  artifact_count: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface WorkspaceRunList {
  items: WorkspaceRunSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface RunAsset {
  id: string;
  run_id: string;
  task_id: string;
  type: string;
  path?: string | null;
  checksum?: string | null;
  verification_status?: string | null;
  created_at?: string | null;
}
