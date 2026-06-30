import { useQuery, useMutation } from '@tanstack/react-query';
import { createGoal, getTask, getWorkspaceState, startGoal } from '../api/workspace';

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
