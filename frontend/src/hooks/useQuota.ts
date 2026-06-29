import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { RecordUsageRequest, UpdateQuotaRequest } from '../types/quota';
import * as api from '../api/quota';

const OVERVIEW_KEY = 'quota-overview';
const MODEL_STATUS_KEY = 'quota-model-status';

export function useRecordUsage() {
  return useMutation({
    mutationFn: (request: RecordUsageRequest) => api.recordUsage(request),
  });
}

export function useOverview(params?: {
  provider?: string;
  status?: string;
  sort_by?: string;
  order?: string;
}) {
  return useQuery({
    queryKey: [OVERVIEW_KEY, params],
    queryFn: () => api.getOverview(params),
    refetchInterval: 10000, // poll every 10s
  });
}

export function useModelStatus(modelId: string) {
  return useQuery({
    queryKey: [MODEL_STATUS_KEY, modelId],
    queryFn: () => api.getModelStatus(modelId),
    enabled: !!modelId,
    refetchInterval: 10000,
  });
}

export function useUpdateQuotaConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ modelId, request }: { modelId: string; request: UpdateQuotaRequest }) =>
      api.updateQuotaConfig(modelId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [OVERVIEW_KEY] });
    },
  });
}

export function useResetQuotaStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ modelId, reason }: { modelId: string; reason?: string }) =>
      api.resetQuotaStatus(modelId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [OVERVIEW_KEY] });
      queryClient.invalidateQueries({ queryKey: [MODEL_STATUS_KEY] });
    },
  });
}
