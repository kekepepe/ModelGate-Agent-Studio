import axios from 'axios';
import type { Model, ModelCreateData, ModelUpdateData, ModelFilters, ModelListResponse, ApiResponse } from '../types/model';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export async function getModels(filters: ModelFilters = {}): Promise<ModelListResponse> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, String(value));
    }
  });
  const resp = await client.get<ApiResponse<ModelListResponse>>(`/models?${params.toString()}`);
  return resp.data.data || { items: [], total: 0, page: 1, page_size: 20, total_pages: 0 };
}

export async function getModel(modelId: string): Promise<Model> {
  const resp = await client.get<ApiResponse<Model>>(`/models/${modelId}`);
  return resp.data.data as Model;
}

export async function createModel(data: ModelCreateData): Promise<Model> {
  const resp = await client.post<ApiResponse<Model>>('/models', data);
  return resp.data.data as Model;
}

export async function updateModel(modelId: string, data: ModelUpdateData): Promise<Model> {
  const resp = await client.put<ApiResponse<Model>>(`/models/${modelId}`, data);
  return resp.data.data as Model;
}

export async function deleteModel(modelId: string): Promise<{ id: string; deleted: boolean }> {
  const resp = await client.delete<ApiResponse<{ id: string; deleted: boolean }>>(`/models/${modelId}`);
  return resp.data.data as { id: string; deleted: boolean };
}

export async function toggleModel(modelId: string): Promise<{ id: string; is_enabled: boolean }> {
  const resp = await client.patch<ApiResponse<{ id: string; is_enabled: boolean }>>(`/models/${modelId}/toggle`);
  return resp.data.data as { id: string; is_enabled: boolean };
}

export interface ModelHealth { model_id: string; provider: string; execution_mode: string; healthy: boolean; latency_ms: number; message?: string; }

export async function checkModelHealth(modelId: string, executionMode: 'live' | 'sandbox' | 'dry_run' | 'mock' = 'live'): Promise<ModelHealth> {
  const resp = await client.post<ApiResponse<ModelHealth>>(`/models/${modelId}/health?execution_mode=${executionMode}`);
  if (!resp.data.success || !resp.data.data) throw new Error(resp.data.error?.message || '检查失败');
  return resp.data.data;
}
