import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { exportRun, getRun, getRunAssets, getRuns, getRunWorkspace } from '../api/runs';

export const RUNS_QUERY_KEY = 'workspace-runs';
export const RUN_QUERY_KEY = 'workspace-run';

export function useRuns(filters: { status?: string; team_id?: string; search?: string } = {}) {
  return useQuery({
    queryKey: [RUNS_QUERY_KEY, filters],
    queryFn: () => getRuns(filters),
    refetchInterval: 5000,
  });
}

export function useRun(runId?: string) {
  return useQuery({
    queryKey: [RUN_QUERY_KEY, runId, 'summary'],
    queryFn: () => getRun(runId!),
    enabled: Boolean(runId),
    refetchInterval: 5000,
  });
}

export function useRunWorkspace(runId?: string) {
  return useQuery({
    queryKey: [RUN_QUERY_KEY, runId],
    queryFn: () => getRunWorkspace(runId!),
    enabled: Boolean(runId),
    refetchInterval: 2000,
  });
}

export function useRunAssets(runId?: string) {
  return useQuery({
    queryKey: [RUN_QUERY_KEY, runId, 'assets'],
    queryFn: () => getRunAssets(runId!),
    enabled: Boolean(runId),
    refetchInterval: 5000,
  });
}

export function useExportRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: exportRun,
    onSuccess: (_, runId) => queryClient.invalidateQueries({ queryKey: [RUN_QUERY_KEY, runId, 'assets'] }),
  });
}
