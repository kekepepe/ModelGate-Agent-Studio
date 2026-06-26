import axios from 'axios';
import type { AgentStation, AgentListItem, AgentTemplate, AgentCreateData, AgentUpdateData, AgentFilters, ApiResponse } from '../types/agent';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export async function getAgents(filters: AgentFilters = {}): Promise<{ items: AgentListItem[]; total: number; page: number; page_size: number }> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, String(value));
    }
  });
  const resp = await client.get<ApiResponse<{ items: AgentListItem[]; total: number; page: number; page_size: number }>>(`/agents?${params.toString()}`);
  return resp.data.data || { items: [], total: 0, page: 1, page_size: 20 };
}

export async function getAgent(agentId: string): Promise<AgentStation> {
  const resp = await client.get<ApiResponse<AgentStation>>(`/agents/${agentId}`);
  return resp.data.data as AgentStation;
}

export async function createAgent(data: AgentCreateData): Promise<{ id: string; name: string; role: string; status: string; created_at?: string }> {
  const resp = await client.post<ApiResponse<{ id: string; name: string; role: string; status: string; created_at?: string }>>('/agents', data);
  return resp.data.data as { id: string; name: string; role: string; status: string; created_at?: string };
}

export async function updateAgent(agentId: string, data: AgentUpdateData): Promise<AgentStation> {
  const resp = await client.patch<ApiResponse<AgentStation>>(`/agents/${agentId}`, data);
  return resp.data.data as AgentStation;
}

export async function updateAgentStatus(agentId: string, isEnabled: boolean): Promise<{ id: string; is_enabled: boolean; status: string }> {
  const resp = await client.patch<ApiResponse<{ id: string; is_enabled: boolean; status: string }>>(`/agents/${agentId}/status`, { is_enabled: isEnabled });
  return resp.data.data as { id: string; is_enabled: boolean; status: string };
}

export async function getAgentTemplates(): Promise<AgentTemplate[]> {
  const resp = await client.get<ApiResponse<AgentTemplate[]>>('/agents/templates');
  return resp.data.data || [];
}
