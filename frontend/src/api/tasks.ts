import axios from 'axios';
import type { WorkspaceTask, TaskStatus } from '../types/workspace';
import type { ApiResponse } from '../types/agent';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

/** V1.0-P1-2 list response (matches backend `task_service.list_tasks` shape) */
export interface TaskListResponse {
  items: WorkspaceTask[];
  total: number;
  page: number;
  page_size: number;
}

export interface GetTasksArgs {
  agentIds?: string[];
  statuses?: TaskStatus[];
  goalId?: string;
  page?: number;
  pageSize?: number;
}

export async function getTasks(args: GetTasksArgs = {}): Promise<TaskListResponse> {
  const params = new URLSearchParams();
  if (args.agentIds) {
    for (const id of args.agentIds) params.append('agent_id', id);
  }
  if (args.statuses) {
    for (const s of args.statuses) params.append('status', s);
  }
  if (args.goalId) params.set('goal_id', args.goalId);
  if (args.page) params.set('page', String(args.page));
  if (args.pageSize) params.set('page_size', String(args.pageSize));

  const resp = await client.get<ApiResponse<TaskListResponse>>(
    `/tasks?${params.toString()}`,
  );
  return resp.data.data || { items: [], total: 0, page: 1, page_size: args.pageSize ?? 50 };
}
