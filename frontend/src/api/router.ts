import axios from 'axios';
import type { RoutingRequest, RoutingResult, OverrideRequest, OverrideResponse, RoutingRules, ApiResponse } from '../types/router';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export async function selectModel(request: RoutingRequest): Promise<RoutingResult> {
  const resp = await client.post<ApiResponse<RoutingResult>>('/router/select-model', request);
  if (!resp.data.success) {
    throw new Error(resp.data.error?.message || '模型路由失败');
  }
  return resp.data.data as RoutingResult;
}

export async function overrideModel(request: OverrideRequest): Promise<OverrideResponse> {
  const resp = await client.post<ApiResponse<OverrideResponse>>('/router/override-model', request);
  if (!resp.data.success) {
    throw new Error(resp.data.error?.message || '模型覆盖失败');
  }
  return resp.data.data as OverrideResponse;
}

export async function getRoutingRules(): Promise<RoutingRules> {
  const resp = await client.get<ApiResponse<RoutingRules>>('/router/rules');
  if (!resp.data.success) {
    throw new Error(resp.data.error?.message || '获取路由规则失败');
  }
  return resp.data.data as RoutingRules;
}
