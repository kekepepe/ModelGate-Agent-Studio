import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createGoal, getTask, getWorkspaceState, startGoal } from '../api/workspace';
import { executeGoal as apiExecuteGoal, executeStep as apiExecuteStep } from '../api/runtime';

const WORKSPACE_QUERY_KEY = 'workspace-state';
const TASK_DETAIL_KEY = 'task-detail';

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
    mutationFn: ({ title, description }: { title: string; description?: string }) =>
      createGoal(title, description),
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
    mutationFn: (goalId: string) => apiExecuteGoal(goalId),
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
