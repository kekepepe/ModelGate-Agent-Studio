import axios from 'axios';
import type { ApiResponse } from '../types/handoff';
import type { RunAsset, WorkspaceRunList, WorkspaceRunSummary } from '../types/run';
import type { WorkspaceState } from '../types/workspace';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const client = axios.create({ baseURL: API_BASE, headers: { 'Content-Type': 'application/json' } });

function unwrap<T>(response: { data: ApiResponse<T> }): T {
  if (!response.data.success || response.data.data === undefined) {
    throw new Error(response.data.error?.message || '请求失败');
  }
  return response.data.data;
}

export async function getRuns(filters: { status?: string; team_id?: string; search?: string } = {}): Promise<WorkspaceRunList> {
  return unwrap(await client.get<ApiResponse<WorkspaceRunList>>('/runs', { params: filters }));
}

export async function getRun(runId: string): Promise<WorkspaceRunSummary> {
  return unwrap(await client.get<ApiResponse<WorkspaceRunSummary>>(`/runs/${runId}`));
}

export async function getRunWorkspace(runId: string): Promise<WorkspaceState> {
  return unwrap(await client.get<ApiResponse<WorkspaceState>>(`/runs/${runId}/workspace`));
}

export async function getRunAssets(runId: string): Promise<{ run: WorkspaceRunSummary; items: RunAsset[] }> {
  return unwrap(await client.get<ApiResponse<{ run: WorkspaceRunSummary; items: RunAsset[] }>>(`/runs/${runId}/assets`));
}

export async function exportRun(runId: string): Promise<{ artifact_id: string; file_name: string; content: string; snapshot: boolean }> {
  return unwrap(await client.post<ApiResponse<{ artifact_id: string; file_name: string; content: string; snapshot: boolean }>>(`/runs/${runId}/export`));
}
