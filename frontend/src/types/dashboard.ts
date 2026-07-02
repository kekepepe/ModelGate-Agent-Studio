export interface DashboardAgentStatus {
  agent_id: string;
  name: string;
  role: string;
  status: string;
}

export interface DashboardModelUsage {
  model_id: string;
  display_name: string;
  tokens_used: number;
  calls_count: number;
}

export interface DashboardToolUsage {
  tool_name: string;
  call_count: number;
  success_count: number;
  failed_count: number;
  success_rate: number;
}

export interface DashboardRecentGoal {
  id: string;
  title: string;
  status: string;
  updated_at: string | null;
}

export interface DashboardStats {
  active_goals: number;
  completed_goals_today: number;
  total_tokens_today: number;
  total_model_calls_today: number;
  total_tool_calls_today: number;
  handoffs_today: number;
  agents_status: DashboardAgentStatus[];
  model_usage: DashboardModelUsage[];
  tool_usage: DashboardToolUsage[];
  recent_goals: DashboardRecentGoal[];
}

export interface DashboardTrendPoint {
  date: string;
  tokens: number;
  model_calls: number;
  tool_calls: number;
  handoffs: number;
  tasks_completed: number;
  tasks_failed: number;
  quota_usage_percent: number;
}

export interface DashboardTrends {
  daily: DashboardTrendPoint[];
}

export interface DashboardAgentPerformance {
  agent_id: string;
  name: string;
  role: string;
  tasks_completed: number;
  tasks_failed: number;
  success_rate: number;
  avg_tokens_per_task: number;
  avg_duration_ms: number;
  total_handoffs_initiated: number;
}

export interface DashboardAgentPerformanceResponse {
  agents: DashboardAgentPerformance[];
}
