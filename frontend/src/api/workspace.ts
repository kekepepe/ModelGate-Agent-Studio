import axios from 'axios';
import type { ApiResponse } from '../types/handoff';
import type { WorkspaceState, WorkspaceTask } from '../types/workspace';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

function unwrap<T>(resp: { data: ApiResponse<T> }, fallback: T): T {
  if (!resp.data.success) {
    throw new Error(resp.data.error?.message || '请求失败');
  }
  return resp.data.data || fallback;
}

export async function createGoal(title: string, description?: string, executionMode: 'live' | 'sandbox' | 'dry_run' | 'mock' = 'live', budgetTokens = 100000, budgetCostUsd?: number, maxDurationSeconds = 3600, teamPreset?: string): Promise<{ goal_id: string; status: string }> {
  const resp = await client.post<ApiResponse<{ goal_id: string; status: string }>>('/goals', {
    title, description, execution_mode: executionMode, budget_tokens: budgetTokens,
    budget_cost_usd: budgetCostUsd, max_duration_seconds: maxDurationSeconds, team_preset: teamPreset,
  });
  if (!resp.data.success || !resp.data.data) {
    throw new Error(resp.data.error?.message || '创建 Goal 失败');
  }
  return resp.data.data;
}

export async function startGoal(goalId: string): Promise<{ goal_id: string; status: string }> {
  const resp = await client.post<ApiResponse<{ goal_id: string; status: string }>>(`/goals/${goalId}/start`);
  if (!resp.data.success || !resp.data.data) {
    throw new Error(resp.data.error?.message || '启动 Goal 失败');
  }
  return resp.data.data;
}

export async function getWorkspaceState(goalId: string): Promise<WorkspaceState> {
  const resp = await client.get<ApiResponse<WorkspaceState>>(`/workspace/${goalId}/state`);
  return unwrap(resp, { goal: null, tasks: [], agents: [], workers: [], handoffs: [] });
}

export async function getTask(taskId: string): Promise<WorkspaceTask> {
  const resp = await client.get<ApiResponse<WorkspaceTask>>(`/tasks/${taskId}`);
  if (!resp.data.success || !resp.data.data) {
    throw new Error(resp.data.error?.message || '获取 Task 详情失败');
  }
  return resp.data.data;
}

export async function retryTask(taskId: string): Promise<WorkspaceTask> {
  const resp = await client.post<ApiResponse<WorkspaceTask>>(`/tasks/${taskId}/retry`);
  if (!resp.data.success || !resp.data.data) throw new Error(resp.data.error?.message || '重试 Task 失败');
  return resp.data.data;
}
