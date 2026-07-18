import axios from 'axios';
import type { ApiResponse } from '../types/handoff';
import type {
  EvolutionSummary, KnowledgeChunk, KnowledgeDocument, KnowledgeSource,
  KnowledgeSourceInput, KnowledgeSyncResult, MemoryDraft, SkillDraft,
} from '../types/knowledge';

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

export async function getEvolutionSummary(goalId?: string, runId?: string): Promise<EvolutionSummary> {
  const resp = await client.get<ApiResponse<EvolutionSummary>>('/knowledge/evolution', { params: { goal_id: goalId, run_id: runId } });
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

export async function disableKnowledgeSource(sourceId: string): Promise<void> {
  const resp = await client.patch<ApiResponse<unknown>>(`/knowledge/sources/${sourceId}/status`, { status: 'disabled' });
  if (!resp.data.success) throw new Error(resp.data.error?.message || '禁用知识源失败');
}

export async function getKnowledgeSources(): Promise<KnowledgeSource[]> {
  const resp = await client.get<ApiResponse<KnowledgeSource[]>>('/knowledge/sources');
  return unwrap(resp, []);
}

export async function createKnowledgeSource(input: KnowledgeSourceInput): Promise<KnowledgeSource> {
  const resp = await client.post<ApiResponse<KnowledgeSource>>('/knowledge/sources', input);
  if (!resp.data.success || !resp.data.data) throw new Error(resp.data.error?.message || '创建知识源失败');
  return resp.data.data;
}

export async function syncKnowledgeSource(sourceId: string): Promise<KnowledgeSyncResult> {
  const resp = await client.post<ApiResponse<KnowledgeSyncResult>>(`/knowledge/sources/${sourceId}/sync`);
  if (!resp.data.success || !resp.data.data) throw new Error(resp.data.error?.message || '同步知识源失败');
  return resp.data.data;
}

export async function getKnowledgeDocuments(sourceId: string): Promise<KnowledgeDocument[]> {
  const resp = await client.get<ApiResponse<KnowledgeDocument[]>>(`/knowledge/sources/${sourceId}/documents`);
  return unwrap(resp, []);
}

export async function getKnowledgeChunks(documentId: string): Promise<KnowledgeChunk[]> {
  const resp = await client.get<ApiResponse<KnowledgeChunk[]>>(`/knowledge/documents/${documentId}/chunks`);
  return unwrap(resp, []);
}
