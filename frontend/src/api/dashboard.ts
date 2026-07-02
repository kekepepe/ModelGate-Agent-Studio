import axios from 'axios';
import type { ApiResponse } from '../types/agent';
import type {
  DashboardAgentPerformanceResponse,
  DashboardStats,
  DashboardTrends,
} from '../types/dashboard';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export async function getDashboardStats(): Promise<DashboardStats> {
  const resp = await client.get<ApiResponse<DashboardStats>>('/dashboard/stats');
  if (!resp.data.success) {
    throw new Error(resp.data.error?.message || '获取 Dashboard 统计失败');
  }
  return resp.data.data as DashboardStats;
}

export async function getDashboardTrends(days = 7): Promise<DashboardTrends> {
  const resp = await client.get<ApiResponse<DashboardTrends>>('/dashboard/trends', { params: { days } });
  if (!resp.data.success) {
    throw new Error(resp.data.error?.message || '获取 Dashboard 趋势失败');
  }
  return resp.data.data as DashboardTrends;
}

export async function getAgentPerformance(): Promise<DashboardAgentPerformanceResponse> {
  const resp = await client.get<ApiResponse<DashboardAgentPerformanceResponse>>('/dashboard/agent-performance');
  if (!resp.data.success) {
    throw new Error(resp.data.error?.message || '获取 Agent 表现失败');
  }
  return resp.data.data as DashboardAgentPerformanceResponse;
}
