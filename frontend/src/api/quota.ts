import axios from 'axios';
import type {
  QuotaOverview,
  QuotaRecord,
  RecordUsageRequest,
  UpdateQuotaRequest,
} from '../types/quota';
import type { ApiResponse } from '../types/router';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export async function recordUsage(request: RecordUsageRequest): Promise<{
  quota_record_id: string;
  updated_status: string;
  usage_percent: number | null;
  estimated_remaining: number | null;
  risk_flags: string[];
}> {
  const resp = await client.post<ApiResponse<any>>('/quota/record-usage', request);
  if (!resp.data.success) {
    throw new Error(resp.data.error?.message || '记录 usage 失败');
  }
  return resp.data.data;
}

export async function getOverview(
  params?: { provider?: string; status?: string; sort_by?: string; order?: string }
): Promise<QuotaOverview> {
  const resp = await client.get<ApiResponse<QuotaOverview>>('/quota/overview', { params });
  if (!resp.data.success) {
    throw new Error(resp.data.error?.message || '获取额度概览失败');
  }
  return resp.data.data as QuotaOverview;
}

export async function getModelStatus(modelId: string): Promise<QuotaRecord> {
  const resp = await client.get<ApiResponse<QuotaRecord>>(`/quota/models/${modelId}/status`);
  if (!resp.data.success) {
    throw new Error(resp.data.error?.message || '获取模型额度状态失败');
  }
  return resp.data.data as QuotaRecord;
}

export async function updateQuotaConfig(
  modelId: string,
  request: UpdateQuotaRequest
): Promise<QuotaRecord> {
  const resp = await client.patch<ApiResponse<QuotaRecord>>(
    `/quota/models/${modelId}/quota`,
    request
  );
  if (!resp.data.success) {
    throw new Error(resp.data.error?.message || '更新额度配置失败');
  }
  return resp.data.data as QuotaRecord;
}

export async function resetQuotaStatus(
  modelId: string,
  reason?: string
): Promise<QuotaRecord> {
  const resp = await client.patch<ApiResponse<QuotaRecord>>(
    `/quota/models/${modelId}/status`,
    { quota_status: 'normal', reason: reason || '用户手动标记为正常' }
  );
  if (!resp.data.success) {
    throw new Error(resp.data.error?.message || '重置额度状态失败');
  }
  return resp.data.data as QuotaRecord;
}
