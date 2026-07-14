import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { HandoffAcceptRequest, HandoffFilters, HandoffResultRequest, HandoffTriggerRequest } from '../types/handoff';
import * as api from '../api/handoffs';

const HANDOFFS_KEY = 'handoffs';
const HANDOFF_KEY = 'handoff';

export function useHandoffs(filters: HandoffFilters = {}) {
  return useQuery({
    queryKey: [HANDOFFS_KEY, filters],
    queryFn: () => api.getHandoffs(filters),
    refetchInterval: 10000,
  });
}

export function useHandoff(handoffId: string) {
  return useQuery({
    queryKey: [HANDOFF_KEY, handoffId],
    queryFn: () => api.getHandoff(handoffId),
    enabled: !!handoffId,
    refetchInterval: 10000,
  });
}

export function useTriggerHandoff() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ taskId, request }: { taskId: string; request: HandoffTriggerRequest }) =>
      api.triggerHandoff(taskId, request),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [HANDOFFS_KEY] });
      qc.invalidateQueries({ queryKey: ['workspace-state'] });
    },
  });
}

export function useAcceptHandoff() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ handoffId, request }: { handoffId: string; request?: HandoffAcceptRequest }) =>
      api.acceptHandoff(handoffId, request || {}),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: [HANDOFFS_KEY] });
      qc.invalidateQueries({ queryKey: [HANDOFF_KEY, vars.handoffId] });
      qc.invalidateQueries({ queryKey: ['workspace-state'] });
    },
  });
}

export function useUpdateHandoffResult() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ handoffId, request }: { handoffId: string; request: HandoffResultRequest }) =>
      api.updateHandoffResult(handoffId, request),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: [HANDOFFS_KEY] });
      qc.invalidateQueries({ queryKey: [HANDOFF_KEY, vars.handoffId] });
      qc.invalidateQueries({ queryKey: ['workspace-state'] });
    },
  });
}

export function useCreateDemoTask() {
  return useMutation({
    mutationFn: api.createDemoTask,
  });
}
