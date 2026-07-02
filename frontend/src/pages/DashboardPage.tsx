import { RefreshCw } from 'lucide-react';
import AgentPerformanceChart from '../components/AgentPerformanceChart';
import ModelUsagePieChart from '../components/ModelUsagePieChart';
import QuotaTrendChart from '../components/QuotaTrendChart';
import StatsSummaryCards from '../components/StatsSummaryCards';
import TokenUsageChart from '../components/TokenUsageChart';
import ToolUsageChart from '../components/ToolUsageChart';
import { useAgentPerformance, useDashboardStats, useDashboardTrends } from '../hooks/useDashboard';

export default function DashboardPage() {
  const statsQuery = useDashboardStats();
  const trendsQuery = useDashboardTrends(7);
  const agentQuery = useAgentPerformance();

  const isLoading = statsQuery.isLoading || trendsQuery.isLoading || agentQuery.isLoading;
  const error = statsQuery.error || trendsQuery.error || agentQuery.error;
  const trends = trendsQuery.data?.daily || [];
  const agentPerformance = agentQuery.data?.agents || [];

  const handleRefresh = () => {
    statsQuery.refetch();
    trendsQuery.refetch();
    agentQuery.refetch();
  };

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">Dashboard</h1>
          <p className="text-sm text-stone-500 mt-0.5">系统运行统计与资源趋势</p>
        </div>
        <button
          onClick={handleRefresh}
          className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-stone-600 bg-white border border-stone-200 rounded-lg hover:bg-stone-50 transition-colors"
        >
          <RefreshCw size={14} />
          刷新
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          {(error as Error).message}
        </div>
      )}

      <div className="space-y-4">
        <StatsSummaryCards data={statsQuery.data} isLoading={isLoading} />

        {isLoading ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="bg-white border border-stone-200 rounded-xl p-4">
                <div className="h-4 bg-stone-100 rounded animate-pulse w-40 mb-4" />
                <div className="h-[260px] bg-stone-50 rounded-lg animate-pulse" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <TokenUsageChart data={trends} />
            <ModelUsagePieChart data={statsQuery.data?.model_usage || []} />
            <AgentPerformanceChart data={agentPerformance} />
            <ToolUsageChart data={statsQuery.data?.tool_usage || []} />
            <QuotaTrendChart data={trends} />
            <RecentGoals goals={statsQuery.data?.recent_goals || []} />
          </div>
        )}
      </div>
    </div>
  );
}

interface RecentGoalsProps {
  goals: Array<{ id: string; title: string; status: string; updated_at: string | null }>;
}

function RecentGoals({ goals }: RecentGoalsProps) {
  return (
    <div className="bg-white border border-stone-200 rounded-xl p-4">
      <h2 className="text-sm font-semibold text-stone-800 mb-4">Recent Goals</h2>
      {goals.length === 0 ? (
        <div className="h-[260px] flex items-center justify-center text-sm text-stone-400 border border-dashed border-stone-200 rounded-lg">
          暂无最近目标
        </div>
      ) : (
        <div className="divide-y divide-stone-100">
          {goals.map((goal) => (
            <div key={goal.id} className="flex items-center justify-between py-3 gap-3">
              <div className="min-w-0">
                <div className="text-sm font-medium text-stone-800 truncate">{goal.title}</div>
                <div className="text-xs text-stone-400 mt-0.5">{goal.updated_at ? formatDate(goal.updated_at) : '--'}</div>
              </div>
              <span className="shrink-0 text-[11px] font-medium uppercase tracking-wide px-2 py-0.5 rounded-full bg-stone-100 text-stone-600">
                {goal.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}
