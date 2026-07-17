import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { ModelFilters, ModelUpdateData } from '../types/model';
import * as api from '../api/models';

const MODELS_KEY = 'models';
const MODEL_KEY = 'model';

export function useModels(filters: ModelFilters = {}) {
  return useQuery({
    queryKey: [MODELS_KEY, filters],
    queryFn: () => api.getModels(filters),
  });
}

export function useModel(modelId: string) {
  return useQuery({
    queryKey: [MODEL_KEY, modelId],
    queryFn: () => api.getModel(modelId),
    enabled: !!modelId,
  });
}

export function useCreateModel() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.createModel,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [MODELS_KEY] });
    },
  });
}

export function useUpdateModel(modelId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ModelUpdateData) => api.updateModel(modelId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [MODELS_KEY] });
      qc.invalidateQueries({ queryKey: [MODEL_KEY, modelId] });
    },
  });
}

export function useDeleteModel() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.deleteModel,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [MODELS_KEY] });
    },
  });
}

export function useToggleModel() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.toggleModel,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [MODELS_KEY] });
    },
  });
}

export function useModelHealth() {
  return useMutation({ mutationFn: ({ modelId, executionMode }: { modelId: string; executionMode?: 'live' | 'sandbox' | 'dry_run' | 'mock' }) => api.checkModelHealth(modelId, executionMode) });
}
