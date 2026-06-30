import { useQuery } from '@tanstack/react-query';
import { getLog, getLogs, getTaskTimeline } from '../api/logs';
import type { LogFilters } from '../types/log';

const LOGS_QUERY_KEY = 'logs';
const LOG_DETAIL_QUERY_KEY = 'log-detail';
const TASK_TIMELINE_QUERY_KEY = 'task-timeline';

export function useLogsQuery(filters: LogFilters = {}) {
  return useQuery({
    queryKey: [LOGS_QUERY_KEY, filters],
    queryFn: () => getLogs(filters),
    refetchInterval: 5000,
  });
}

export function useLogDetailQuery(logId: string | null) {
  return useQuery({
    queryKey: [LOG_DETAIL_QUERY_KEY, logId],
    queryFn: () => getLog(logId!),
    enabled: !!logId,
  });
}

export function useTaskTimelineQuery(taskId: string | null) {
  return useQuery({
    queryKey: [TASK_TIMELINE_QUERY_KEY, taskId],
    queryFn: () => getTaskTimeline(taskId!),
    enabled: !!taskId,
  });
}
