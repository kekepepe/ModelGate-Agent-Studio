export interface Model {
  id: string;
  provider: string;
  model_name: string;
  display_name: string;
  capability_tags: string[];
  max_context_tokens: number;
  cost_level: number;
  speed_level: number;
  is_enabled: boolean;
  is_default: boolean;
  api_key?: string | null;
  api_base_url?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ModelCreateData {
  provider: string;
  model_name: string;
  display_name: string;
  capability_tags?: string[];
  max_context_tokens?: number;
  cost_level?: number;
  speed_level?: number;
  is_enabled?: boolean;
  is_default?: boolean;
  api_key?: string | null;
  api_base_url?: string | null;
}

export interface ModelUpdateData {
  provider?: string;
  model_name?: string;
  display_name?: string;
  capability_tags?: string[];
  max_context_tokens?: number;
  cost_level?: number;
  speed_level?: number;
  is_enabled?: boolean;
  is_default?: boolean;
  api_key?: string | null;
  api_base_url?: string | null;
}

export interface ModelFilters {
  provider?: string;
  is_enabled?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface ModelListResponse {
  items: Model[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: { code: string; message: string };
}
