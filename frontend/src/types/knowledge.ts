export interface MemoryDraft {
  id: string;
  source_run_id?: string | null;
  source_goal_id?: string | null;
  type: string;
  title: string;
  content: string;
  confidence: number;
  reason?: string | null;
  tags: string[];
  human_approved?: boolean | null;
  approved_by?: string | null;
  approved_at?: string | null;
  metadata?: Record<string, unknown>;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface SkillDraft {
  id: string;
  source_run_id?: string | null;
  name: string;
  scenario?: string | null;
  input_requirements?: string | null;
  steps: string[];
  recommended_agents: string[];
  recommended_models: string[];
  tools: string[];
  output_format?: string | null;
  success_criteria?: string | null;
  common_failures: string[];
  status: string;
  human_approved?: boolean | null;
  approved_by?: string | null;
  approved_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface EvolutionSummary {
  memory_drafts: MemoryDraft[];
  skill_drafts: SkillDraft[];
  total_memories: number;
  total_skills: number;
  pending_review: number;
}

export const MEMORY_TYPE_LABELS: Record<string, string> = {
  project_memory: '项目记忆',
  agent_memory: 'Agent 记忆',
  user_memory: '用户偏好',
  session_memory: '会话记忆',
  raw_memory: '原始记忆',
  skill_memory: '技能记忆',
};
