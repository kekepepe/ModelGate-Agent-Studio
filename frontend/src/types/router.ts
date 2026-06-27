export interface DimensionScore {
  dimension: string;
  score: number;
  weight: number;
  weighted_score: number;
  reason: string;
}

export interface ScoreBreakdown {
  model_id: string;
  model_name: string;
  total_score: number;
  dimension_scores: DimensionScore[];
}

export interface RoutingReason {
  summary: string;
  primary_factors: string[];
  secondary_factors: string[];
  tradeoffs: string[];
}

export interface RiskFlag {
  type: string;
  severity: 'low' | 'medium' | 'high';
  message: string;
  suggestion?: string;
}

export interface RoutingRequest {
  task_id: string;
  goal_id?: string;
  task_type: string;
  task_complexity?: string;
  task_description?: string;
  required_capabilities?: string[];
  preferred_agent_id?: string;
  preferred_model_id?: string;
  context_length_estimate?: number;
  has_vision_input?: boolean;
  requires_tool_calling?: boolean;
  budget_preference?: string;
  speed_preference?: string;
}

export interface RoutingResult {
  selected_model_id: string;
  selected_agent_id?: string;
  backup_model_ids: string[];
  routing_reason: RoutingReason;
  confidence: number;
  risk_flags: RiskFlag[];
  score_breakdown: ScoreBreakdown[];
  is_user_override: boolean;
  override_note?: string;
}

export interface OverrideRequest {
  task_id: string;
  selected_model_id: string;
  original_model_id?: string;
  reason?: string;
}

export interface OverrideResponse {
  task_id: string;
  selected_model_id: string;
  is_user_override: boolean;
  override_note?: string;
}

export interface RoutingRules {
  weights: Record<string, number>;
  role_preferences: Record<string, string[]>;
  hard_constraints: string[];
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
}

export const TASK_TYPE_LABELS: Record<string, string> = {
  planning: '规划任务',
  coding: '编码任务',
  review: '审查任务',
  research: '调研任务',
  summarization: '摘要任务',
  supervision: '监督任务',
  debugging: '调试任务',
  documentation: '文档任务',
  testing: '测试任务',
  general: '通用任务',
};

export const DIMENSION_LABELS: Record<string, string> = {
  capability_match: '能力匹配度',
  role_match: '角色匹配度',
  context_fit: '上下文适配度',
  cost_fit: '成本适配度',
  speed_fit: '速度适配度',
  quota_health: '额度健康度',
  historical_performance: '历史表现',
};

export const DIMENSION_COLORS: Record<string, string> = {
  capability_match: 'bg-blue-500',
  role_match: 'bg-green-500',
  context_fit: 'bg-purple-500',
  cost_fit: 'bg-yellow-500',
  speed_fit: 'bg-cyan-500',
  quota_health: 'bg-orange-500',
  historical_performance: 'bg-stone-400',
};
