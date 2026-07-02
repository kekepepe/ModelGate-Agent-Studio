import { Activity, CheckCircle2, GitBranch, MessageSquareText, Wrench, Zap } from 'lucide-react';
import type { DashboardStats } from '../types/dashboard';

interface StatsSummaryCardsProps {
  data?: DashboardStats;
  isLoading?: boolean;
}

const items = [
  { key: 'active_goals', label: 'Active Goals', helper: '当前活跃目标', icon: Activity },
  { key: 'completed_goals_today', label: 'Completed Today', helper: '今日完成目标', icon: CheckCircle2 },
  { key: 'total_tokens_today', label: 'Tokens Today', helper: '今日 Token 消耗', icon: Zap },
  { key: 'total_model_calls_today', label: 'Model Calls', helper: '今日模型调用', icon: MessageSquareText },
  { key: 'total_tool_calls_today', label: 'Tool Calls', helper: '今日工具调用', icon: Wrench },
  { key: 'handoffs_today', label: 'Handoffs', helper: '今日任务移交', icon: GitBranch },
] as const;

export default function StatsSummaryCards({ data, isLoading }: StatsSummaryCardsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {items.map((item) => {
        const Icon = item.icon;
        const value = data ? data[item.key] : 0;
        return (
          <div key={item.key} className="bg-white border border-stone-200 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-stone-500">{item.label}</span>
              <Icon size={16} className="text-stone-400" />
            </div>
            {isLoading ? (
              <div className="h-7 bg-stone-100 rounded animate-pulse" />
            ) : (
              <div className="text-2xl font-semibold text-stone-900">{value.toLocaleString()}</div>
            )}
            <p className="text-xs text-stone-400 mt-1">{item.helper}</p>
          </div>
        );
      })}
    </div>
  );
}
