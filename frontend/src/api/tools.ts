import axios from 'axios';
import type { ToolDefinition, ToolCreateData, ToolUpdateData, ToolFilters, ToolListResponse, ToolCallRecord, ToolCallFilters, ToolCallListResponse } from '../types/tool';
import type { ApiResponse } from '../types/agent';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export async function getTools(filters: ToolFilters = {}): Promise<ToolListResponse> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, String(value));
    }
  });
  const resp = await client.get<ApiResponse<ToolListResponse>>(`/tools?${params.toString()}`);
  return resp.data.data || { items: [], total: 0, page: 1, page_size: 20, total_pages: 0 };
}

export async function getTool(toolId: string): Promise<ToolDefinition> {
  const resp = await client.get<ApiResponse<ToolDefinition>>(`/tools/${toolId}`);
  return resp.data.data as ToolDefinition;
}

export async function createTool(data: ToolCreateData): Promise<ToolDefinition> {
  const resp = await client.post<ApiResponse<ToolDefinition>>('/tools', data);
  return resp.data.data as ToolDefinition;
}

export async function updateTool(toolId: string, data: ToolUpdateData): Promise<ToolDefinition> {
  const resp = await client.put<ApiResponse<ToolDefinition>>(`/tools/${toolId}`, data);
  return resp.data.data as ToolDefinition;
}

export async function deleteTool(toolId: string): Promise<{ id: string; deleted: boolean }> {
  const resp = await client.delete<ApiResponse<{ id: string; deleted: boolean }>>(`/tools/${toolId}`);
  return resp.data.data as { id: string; deleted: boolean };
}

export async function toggleTool(toolId: string): Promise<{ id: string; is_enabled: boolean }> {
  const resp = await client.patch<ApiResponse<{ id: string; is_enabled: boolean }>>(`/tools/${toolId}/toggle`);
  return resp.data.data as { id: string; is_enabled: boolean };
}

export async function getToolCalls(filters: ToolCallFilters = {}): Promise<ToolCallListResponse> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, String(value));
    }
  });
  const resp = await client.get<ApiResponse<ToolCallListResponse>>(`/tools/calls?${params.toString()}`);
  return resp.data.data || { items: [], total: 0, page: 1, page_size: 20, total_pages: 0 };
}

export async function getToolCall(callId: string): Promise<ToolCallRecord> {
  const resp = await client.get<ApiResponse<ToolCallRecord>>(`/tools/calls/${callId}`);
  return resp.data.data as ToolCallRecord;
}
