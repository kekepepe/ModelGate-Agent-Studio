import axios from 'axios';
import type { ApiResponse } from '../types/handoff';
import type { ExecutionPlan, WorkspaceState, WorkspaceTask } from '../types/workspace';

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

export async function createGoal(title: string, description?: string, executionMode: 'live' | 'sandbox' | 'dry_run' | 'mock' = 'live', budgetTokens = 100000, budgetCostUsd?: number, maxDurationSeconds = 3600, teamPreset?: string): Promise<{ goal_id: string; run_id: string; status: string }> {
  const resp = await client.post<ApiResponse<{ goal_id: string; run_id: string; status: string }>>('/goals', {
    title, description, execution_mode: executionMode, budget_tokens: budgetTokens,
    budget_cost_usd: budgetCostUsd, max_duration_seconds: maxDurationSeconds, team_preset: teamPreset,
  });
  if (!resp.data.success || !resp.data.data) {
    throw new Error(resp.data.error?.message || '创建 Goal 失败');
  }
  return resp.data.data;
}

export async function startGoal(goalId: string): Promise<{ goal_id: string; run_id: string; status: string }> {
  const resp = await client.post<ApiResponse<{ goal_id: string; run_id: string; status: string }>>(`/goals/${goalId}/start`);
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

export async function confirmPlan(goalId: string, version: number): Promise<ExecutionPlan> {
  const resp = await client.post<ApiResponse<ExecutionPlan>>(`/goals/${goalId}/plans/${version}/confirm`);
  if (!resp.data.success || !resp.data.data) throw new Error(resp.data.error?.message || '确认计划失败');
  return resp.data.data;
}

export async function updatePlan(goalId: string, plan: ExecutionPlan, reason: string): Promise<unknown> {
  const resp = await client.post<ApiResponse<unknown>>(`/goals/${goalId}/replan`, {
    trigger: 'user_change',
    reason,
    plan: {
      plan_id: plan.plan_id,
      task_mode: plan.task_mode,
      goal_summary: plan.goal_summary,
      assumptions: plan.assumptions,
      required_context: plan.required_context,
      activation_reason: reason,
      tasks: plan.tasks.map((task) => ({
        client_task_id: task.client_task_id,
        objective: task.objective,
        task_type: task.task_type,
        required_capabilities: task.required_capabilities,
        required_tools: task.required_tools,
        dependencies: task.dependencies,
        acceptance_criteria: task.acceptance_criteria,
        risk_level: task.risk_level,
        parallel_safe: task.parallel_safe,
        context_query: task.context_query,
        approval_required: task.approval_required,
        workspace_scope: task.workspace_scope,
        merge_strategy: task.merge_strategy,
      })),
      final_acceptance_criteria: plan.final_acceptance_criteria,
      human_approval_points: plan.human_approval_points,
      estimated_cost: plan.estimated_cost,
      fallback_reason: plan.fallback_reason,
    },
  });
  if (!resp.data.success) throw new Error(resp.data.error?.message || '修改计划失败');
  return resp.data.data;
}
