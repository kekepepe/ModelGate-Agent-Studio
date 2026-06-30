import axios from 'axios';
import type { ApiResponse } from '../types/handoff';
import type { ExecutionLog, LogFilters, LogListResponse, TaskTimelineResponse } from '../types/log';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

function paramsFrom(filters: Record<string, unknown>) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, String(value));
    }
  });
  return params;
}

function unwrap<T>(resp: { data: ApiResponse<T> }, fallback: T): T {
  if (!resp.data.success) {
    throw new Error(resp.data.error?.message || '请求失败');
  }
  return resp.data.data || fallback;
}

export async function getLogs(filters: LogFilters = {}): Promise<LogListResponse> {
  const params = paramsFrom(filters as Record<string, unknown>);
  const resp = await client.get<ApiResponse<LogListResponse>>(`/logs?${params.toString()}`);
  return unwrap(resp, { items: [], total: 0, page: 1, page_size: 20, total_pages: 0 });
}

export async function getLog(logId: string): Promise<ExecutionLog> {
  const resp = await client.get<ApiResponse<ExecutionLog>>(`/logs/${logId}`);
  if (!resp.data.success || !resp.data.data) {
    throw new Error(resp.data.error?.message || '获取日志详情失败');
  }
  return resp.data.data;
}

export async function getTaskTimeline(taskId: string): Promise<TaskTimelineResponse> {
  const resp = await client.get<ApiResponse<TaskTimelineResponse>>(`/logs/task/${taskId}/timeline`);
  if (!resp.data.success || !resp.data.data) {
    throw new Error(resp.data.error?.message || '获取时间线失败');
  }
  return resp.data.data;
}
