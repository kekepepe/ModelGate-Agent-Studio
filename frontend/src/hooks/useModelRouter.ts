import { useMutation, useQuery } from '@tanstack/react-query';
import type { RoutingRequest, OverrideRequest } from '../types/router';
import * as api from '../api/router';

const RULES_KEY = 'router-rules';

export function useSelectModel() {
  return useMutation({
    mutationFn: (request: RoutingRequest) => api.selectModel(request),
  });
}

export function useOverrideModel() {
  return useMutation({
    mutationFn: (request: OverrideRequest) => api.overrideModel(request),
  });
}

export function useRoutingRules() {
  return useQuery({
    queryKey: [RULES_KEY],
    queryFn: api.getRoutingRules,
    staleTime: 5 * 60 * 1000,
  });
}
