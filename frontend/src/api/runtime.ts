import axios from 'axios';
import type { ApiResponse } from '../types/handoff';
import type { ExecutionStep, GoalExecutionResult, RuntimeStatusResponse } from '../types/runtime';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export async function executeGoal(goalId: string): Promise<GoalExecutionResult> {
  const resp = await client.post<ApiResponse<GoalExecutionResult>>(`/runtime/execute/${goalId}`);
  if (!resp.data.success || !resp.data.data) {
    throw new Error(resp.data.error?.message || '执行失败');
  }
  return resp.data.data;
}

export async function executeStep(taskId: string): Promise<ExecutionStep> {
  const resp = await client.post<ApiResponse<ExecutionStep>>(`/runtime/execute-step/${taskId}`);
  if (!resp.data.success || !resp.data.data) {
    throw new Error(resp.data.error?.message || '执行失败');
  }
  return resp.data.data;
}

export async function getRuntimeStatus(goalId: string): Promise<RuntimeStatusResponse> {
  const resp = await client.get<ApiResponse<RuntimeStatusResponse>>(`/runtime/status/${goalId}`);
  if (!resp.data.success || !resp.data.data) {
    throw new Error(resp.data.error?.message || '获取状态失败');
  }
  return resp.data.data;
}
