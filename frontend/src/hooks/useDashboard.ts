import { useQuery } from '@tanstack/react-query';
import * as api from '../api/dashboard';

const DASHBOARD_STATS_KEY = 'dashboard-stats';
const DASHBOARD_TRENDS_KEY = 'dashboard-trends';
const AGENT_PERFORMANCE_KEY = 'dashboard-agent-performance';

export function useDashboardStats() {
  return useQuery({
    queryKey: [DASHBOARD_STATS_KEY],
    queryFn: () => api.getDashboardStats(),
    refetchInterval: 15000,
  });
}

export function useDashboardTrends(days = 7) {
  return useQuery({
    queryKey: [DASHBOARD_TRENDS_KEY, days],
    queryFn: () => api.getDashboardTrends(days),
    refetchInterval: 15000,
  });
}

export function useAgentPerformance() {
  return useQuery({
    queryKey: [AGENT_PERFORMANCE_KEY],
    queryFn: () => api.getAgentPerformance(),
    refetchInterval: 15000,
  });
}
