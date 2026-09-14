import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { confirmPlan, createGoal, getTask, getWorkspaceState, retryTask as apiRetryTask, startGoal, updatePlan } from '../api/workspace';
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

export function useConfirmPlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ goalId, version }: { goalId: string; version: number }) => confirmPlan(goalId, version),
    onSuccess: (_, variables) => queryClient.invalidateQueries({ queryKey: [WORKSPACE_QUERY_KEY, variables.goalId] }),
  });
}

export function useUpdatePlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ goalId, plan, reason }: { goalId: string; plan: import('../types/workspace').ExecutionPlan; reason: string }) => updatePlan(goalId, plan, reason),
    onSuccess: (_, variables) => queryClient.invalidateQueries({ queryKey: [WORKSPACE_QUERY_KEY, variables.goalId] }),
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
 *
 * V1.0-P1-1: Returns `{ isConnected, lastEventAt }` so consumers (e.g.
 * BottomConsole) can show an SSE health indicator.
 */
export function useRuntimeEvents(goalId: string | null): {
  isConnected: boolean;
  lastEventAt: number | null;
} {
  const queryClient = useQueryClient();
  const [isConnected, setIsConnected] = useState(false);
  const [lastEventAt, setLastEventAt] = useState<number | null>(null);

  useEffect(() => {
    if (!goalId) {
      setIsConnected(false);
      setLastEventAt(null);
      return;
    }
    const stream = new EventSource(`${API_BASE}/runtime/events/${goalId}`);
    const refresh = () => {
      queryClient.invalidateQueries({ queryKey: [WORKSPACE_QUERY_KEY, goalId] });
      queryClient.invalidateQueries({ queryKey: [RUNTIME_STATUS_KEY, goalId] });
      queryClient.invalidateQueries({ queryKey: [TASK_DETAIL_KEY] });
    };
    const onOpen = () => setIsConnected(true);
    const onError = () => {
      // EventSource fires `error` on transient disconnects too; flip
      // the flag off but don't tear down the stream (browser will
      // auto-retry unless we manually call stream.close()).
      setIsConnected(false);
    };
    const onMessage = () => {
      refresh();
      setLastEventAt(Date.now());
    };
    stream.addEventListener('open', onOpen);
    stream.addEventListener('error', onError);
    stream.addEventListener('runtime', onMessage);
    stream.addEventListener('end', () => stream.close());

    return () => {
      stream.removeEventListener('open', onOpen);
      stream.removeEventListener('error', onError);
      stream.removeEventListener('runtime', onMessage);
      stream.close();
      setIsConnected(false);
    };
  }, [goalId, queryClient]);

  return { isConnected, lastEventAt };
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
