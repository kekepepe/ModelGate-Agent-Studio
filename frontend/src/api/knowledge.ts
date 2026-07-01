import axios from 'axios';
import type { ApiResponse } from '../types/handoff';
import type { EvolutionSummary, MemoryDraft, SkillDraft } from '../types/knowledge';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const client = axios.create({ baseURL: API_BASE, headers: { 'Content-Type': 'application/json' } });

function unwrap<T>(resp: { data: ApiResponse<T> }, fallback: T): T {
  if (!resp.data.success) throw new Error(resp.data.error?.message || '请求失败');
  return resp.data.data || fallback;
}

export async function generateMemories(goalId: string): Promise<EvolutionSummary> {
  const resp = await client.post<ApiResponse<EvolutionSummary>>(`/knowledge/generate/${goalId}`);
  return unwrap(resp, { memory_drafts: [], skill_drafts: [], total_memories: 0, total_skills: 0, pending_review: 0 });
}

export async function getEvolutionSummary(goalId?: string): Promise<EvolutionSummary> {
  const params = goalId ? `?goal_id=${goalId}` : '';
  const resp = await client.get<ApiResponse<EvolutionSummary>>(`/knowledge/evolution${params}`);
  return unwrap(resp, { memory_drafts: [], skill_drafts: [], total_memories: 0, total_skills: 0, pending_review: 0 });
}

export async function approveMemory(memoryId: string, approved: boolean, approvedBy: string = 'user'): Promise<MemoryDraft> {
  const resp = await client.post<ApiResponse<MemoryDraft>>(`/knowledge/memories/${memoryId}/approve`, { approved, approved_by: approvedBy });
  if (!resp.data.success || !resp.data.data) throw new Error(resp.data.error?.message || '审批失败');
  return resp.data.data;
}

export async function approveSkill(skillId: string, approved: boolean, approvedBy: string = 'user'): Promise<SkillDraft> {
  const resp = await client.post<ApiResponse<SkillDraft>>(`/knowledge/skills/${skillId}/approve`, { approved, approved_by: approvedBy });
  if (!resp.data.success || !resp.data.data) throw new Error(resp.data.error?.message || '审批失败');
  return resp.data.data;
}
