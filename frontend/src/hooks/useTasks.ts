import { useQuery } from '@tanstack/react-query';
import { getTasks } from '../api/tasks';
import type { TaskStatus } from '../types/workspace';

/**
 * V1.0-P1-2 — useTasks.
 *
 * Generic filtered + paginated task list backed by the new
 * `GET /api/v1/tasks` endpoint. The Sidebar uses this to render a
 * "current task" line per Station. Returns the same shape as the
 * pre-existing `WorkspaceTask` so the Sidebar reuses the type.
 */
export interface UseTasksArgs {
  agentIds?: string[];
  statuses?: TaskStatus[];
  goalId?: string;
  page?: number;
  pageSize?: number;
}

export const TASKS_KEY = 'tasks';

export function useTasks(args: UseTasksArgs = {}) {
  const { agentIds, statuses, goalId, page = 1, pageSize = 50 } = args;
  return useQuery({
    queryKey: [TASKS_KEY, { agentIds, statuses, goalId, page, pageSize }],
    queryFn: () =>
      getTasks({
        agentIds,
        statuses,
        goalId,
        page,
        pageSize,
      }),
    staleTime: 5_000,
  });
}
