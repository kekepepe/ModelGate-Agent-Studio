import axios from 'axios';
import type {
  ApiResponse,
  HandoffAcceptRequest,
  HandoffFilters,
  HandoffListResponse,
  HandoffRecord,
  HandoffResultRequest,
  HandoffTask,
  HandoffTriggerRequest,
} from '../types/handoff';

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

export async function getHandoffs(filters: HandoffFilters = {}): Promise<HandoffListResponse> {
  const params = paramsFrom(filters as Record<string, unknown>);
  const resp = await client.get<ApiResponse<HandoffListResponse>>(`/handoffs?${params.toString()}`);
  return unwrap(resp, { items: [], total: 0, page: 1, page_size: 20, total_pages: 0 });
}

export async function getHandoff(handoffId: string): Promise<HandoffRecord> {
  const resp = await client.get<ApiResponse<HandoffRecord>>(`/handoffs/${handoffId}`);
  if (!resp.data.success || !resp.data.data) {
    throw new Error(resp.data.error?.message || '获取交接详情失败');
  }
  return resp.data.data;
}

export async function triggerHandoff(taskId: string, request: HandoffTriggerRequest): Promise<{
  handoff_id: string;
  task_id: string;
  status: string;
  message: string;
}> {
  const resp = await client.post<ApiResponse<{ handoff_id: string; task_id: string; status: string; message: string }>>(
    `/tasks/${taskId}/handoff`,
    request
  );
  if (!resp.data.success || !resp.data.data) {
    throw new Error(resp.data.error?.message || '触发交接失败');
  }
  return resp.data.data;
}

export async function acceptHandoff(handoffId: string, request: HandoffAcceptRequest = {}): Promise<{
  handoff_id: string;
  worker_id: string;
  task_id: string;
  status: string;
}> {
  const resp = await client.post<ApiResponse<{ handoff_id: string; worker_id: string; task_id: string; status: string }>>(
    `/handoffs/${handoffId}/accept`,
    request
  );
  if (!resp.data.success || !resp.data.data) {
    throw new Error(resp.data.error?.message || '接受交接失败');
  }
  return resp.data.data;
}

export async function updateHandoffResult(handoffId: string, request: HandoffResultRequest): Promise<{
  handoff_id: string;
  status: string;
  result_after_handoff: string;
}> {
  const resp = await client.patch<ApiResponse<{ handoff_id: string; status: string; result_after_handoff: string }>>(
    `/handoffs/${handoffId}/result`,
    request
  );
  if (!resp.data.success || !resp.data.data) {
    throw new Error(resp.data.error?.message || '更新交接结果失败');
  }
  return resp.data.data;
}

export async function createDemoTask(request: {
  goal_id: string;
  title: string;
  description?: string;
  status?: string;
  assigned_agent_id: string;
  assigned_model_id: string;
  current_output?: string;
  error_message?: string;
}): Promise<HandoffTask> {
  const resp = await client.post<ApiResponse<HandoffTask>>('/handoff/tasks', request);
  if (!resp.data.success || !resp.data.data) {
    throw new Error(resp.data.error?.message || '创建演示任务失败');
  }
  return resp.data.data;
}
