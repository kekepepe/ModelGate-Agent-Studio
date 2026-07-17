import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createGoal, getTask, getWorkspaceState, retryTask as apiRetryTask, startGoal } from '../api/workspace';
import { executeStep as apiExecuteStep, getRuntimeStatus, pauseGoal as apiPauseGoal, resumeGoal as apiResumeGoal, startGoalExecution, stopGoal as apiStopGoal } from '../api/runtime';

const WORKSPACE_QUERY_KEY = 'workspace-state';
const TASK_DETAIL_KEY = 'task-detail';
const RUNTIME_STATUS_KEY = 'runtime-status';
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export function useWorkspaceState(goalId: string | null) {
  return useQuery({
    queryKey: [WORKSPACE_QUERY_KEY, goalId],
    queryFn: () => getWorkspaceState(goalId!),
    enabled: !!goalId,
    refetchInterval: 2000,
  });
}

export function useTaskDetail(taskId: string | null) {
  return useQuery({
    queryKey: [TASK_DETAIL_KEY, taskId],
    queryFn: () => getTask(taskId!),
    enabled: !!taskId,
    refetchInterval: 2000,
  });
}

export function useCreateGoal() {
  return useMutation({
    mutationFn: ({ title, description, executionMode, budgetTokens, budgetCostUsd, maxDurationSeconds, teamPreset }: {
      title: string; description?: string; executionMode?: 'live' | 'sandbox' | 'dry_run' | 'mock';
      budgetTokens?: number; budgetCostUsd?: number; maxDurationSeconds?: number; teamPreset?: string;
    }) => createGoal(title, description, executionMode, budgetTokens, budgetCostUsd, maxDurationSeconds, teamPreset),
  });
}

export function useStartGoal() {
  return useMutation({
    mutationFn: (goalId: string) => startGoal(goalId),
  });
}

export function useExecuteGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (goalId: string) => startGoalExecution(goalId),
    onSuccess: (_, goalId) => {
      queryClient.invalidateQueries({ queryKey: [WORKSPACE_QUERY_KEY, goalId] });
    },
  });
}

export function useExecuteStep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => apiExecuteStep(taskId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [TASK_DETAIL_KEY, data.task_id] });
      queryClient.invalidateQueries({ queryKey: [WORKSPACE_QUERY_KEY] });
    },
  });
}

export function useRuntimeStatus(goalId: string | null) {
  return useQuery({
    queryKey: [RUNTIME_STATUS_KEY, goalId],
    queryFn: () => getRuntimeStatus(goalId!),
    enabled: !!goalId,
    refetchInterval: 2000,
  });
}

/**
 * Runtime emits only persisted backend events. This subscription makes the
 * Workspace refresh immediately after a real state transition while polling
 * remains a recovery fallback for disconnected browsers.
 */
export function useRuntimeEvents(goalId: string | null) {
  const queryClient = useQueryClient();
  useEffect(() => {
    if (!goalId) return;
    const stream = new EventSource(`${API_BASE}/runtime/events/${goalId}`);
    const refresh = () => {
      queryClient.invalidateQueries({ queryKey: [WORKSPACE_QUERY_KEY, goalId] });
      queryClient.invalidateQueries({ queryKey: [RUNTIME_STATUS_KEY, goalId] });
      queryClient.invalidateQueries({ queryKey: [TASK_DETAIL_KEY] });
    };
    stream.addEventListener('runtime', refresh);
    stream.addEventListener('end', () => stream.close());
    return () => stream.close();
  }, [goalId, queryClient]);
}

export function usePauseGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: apiPauseGoal,
    onSuccess: (_, goalId) => queryClient.invalidateQueries({ queryKey: [WORKSPACE_QUERY_KEY, goalId] }),
  });
}

export function useResumeGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: apiResumeGoal,
    onSuccess: (_, goalId) => queryClient.invalidateQueries({ queryKey: [WORKSPACE_QUERY_KEY, goalId] }),
  });
}

export function useStopGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: apiStopGoal,
    onSuccess: (_, goalId) => {
      queryClient.invalidateQueries({ queryKey: [WORKSPACE_QUERY_KEY, goalId] });
      queryClient.invalidateQueries({ queryKey: [RUNTIME_STATUS_KEY, goalId] });
    },
  });
}

export function useRetryTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: apiRetryTask,
    onSuccess: (task) => {
      queryClient.invalidateQueries({ queryKey: [TASK_DETAIL_KEY, task.id] });
      queryClient.invalidateQueries({ queryKey: [WORKSPACE_QUERY_KEY, task.goal_id] });
    },
  });
}
