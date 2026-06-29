export type QuotaStatus = 'normal' | 'warning' | 'near_limit' | 'limited' | 'cooldown' | 'unknown';
export type QuotaMode = 'known' | 'estimated' | 'unknown';

export interface QuotaRecord {
  id: string;
  provider: string;
  model_id: string;
  model_name: string;
  request_count: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  limit_error_count: number;
  handoff_triggered_count: number;
  quota_mode: QuotaMode;
  token_limit?: number;
  request_limit?: number;
  cost_limit?: number;
  reset_period?: string;
  reset_date?: number;
  usage_percent: number | null;
  estimated_remaining: number | null;
  quota_status: QuotaStatus;
  last_used_at: string | null;
  cooldown_until: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface QuotaSummary {
  total_models: number;
  normal_count: number;
  warning_count: number;
  near_limit_count: number;
  limited_count: number;
  cooldown_count: number;
  unknown_count: number;
}

export interface QuotaOverviewItem {
  quota_record_id: string;
  provider: string;
  model_id: string;
  model_name: string;
  request_count: number;
  total_tokens: number;
  quota_status: QuotaStatus;
  usage_percent: number | null;
  estimated_remaining: number | null;
  last_used_at: string | null;
  limit_error_count: number;
  handoff_triggered_count: number;
}

export interface QuotaOverview {
  summary: QuotaSummary;
  models: QuotaOverviewItem[];
}

export interface RecordUsageRequest {
  provider: string;
  model_id: string;
  model_name?: string;
  request_tokens?: number;
  response_tokens?: number;
  total_tokens?: number;
  error_code?: number | null;
  error_type?: string | null;
}

export interface UpdateQuotaRequest {
  token_limit?: number;
  request_limit?: number;
  cost_limit?: number;
  reset_period?: string;
  reset_date?: number;
}

export const STATUS_COLORS: Record<QuotaStatus, string> = {
  normal: 'bg-green-500',
  warning: 'bg-yellow-500',
  near_limit: 'bg-orange-500',
  limited: 'bg-red-500',
  cooldown: 'bg-blue-500',
  unknown: 'bg-stone-400',
};

export const STATUS_BG_COLORS: Record<QuotaStatus, string> = {
  normal: 'bg-green-50 text-green-700 border-green-200',
  warning: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  near_limit: 'bg-orange-50 text-orange-700 border-orange-200',
  limited: 'bg-red-50 text-red-700 border-red-200',
  cooldown: 'bg-blue-50 text-blue-700 border-blue-200',
  unknown: 'bg-stone-50 text-stone-600 border-stone-200',
};

export const STATUS_LABELS: Record<QuotaStatus, string> = {
  normal: '正常',
  warning: '注意',
  near_limit: '接近上限',
  limited: '已受限',
  cooldown: '冷却中',
  unknown: '未知',
};

export const PROVIDER_LABELS: Record<string, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  deepseek: 'DeepSeek',
  kimi: 'Kimi',
  zhipu: '智谱',
};
