import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronUp, ChevronDown } from 'lucide-react';
import LogListItem from './LogListItem';
import LogFilters from './LogFilters';
import { getLogs } from '../api/logs';
import type { LogFilters as LogFiltersType } from '../types/log';

interface BottomConsoleProps {
  goalId?: string | null;
}

export default function BottomConsole({ goalId }: BottomConsoleProps) {
  const [expanded, setExpanded] = useState(false);
  const [filters, setFilters] = useState<LogFiltersType>({ page_size: 50 });

  const allFilters = goalId ? { ...filters, goal_id: goalId } : filters;
  const { data: logsData } = useQuery({
    queryKey: ['workspace-logs', allFilters],
    queryFn: () => getLogs(allFilters),
    enabled: !!goalId && expanded,
  });

  // If no goalId, show placeholder
  if (!goalId) {
    return (
      <div className="border-t border-stone-200 bg-white">
        <div className="flex items-center justify-between px-4 py-2">
          <span className="text-xs text-stone-400">启动 Goal 后此处将显示实时执行日志</span>
        </div>
      </div>
    );
  }

  const summaryText = logsData
    ? `${logsData.total} 条日志`
    : '加载中...';

  return (
    <div className="border-t border-stone-200 bg-white">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-2 hover:bg-stone-50 transition-colors"
      >
        <span className="text-xs text-stone-500 font-medium">
          执行日志 · {summaryText}
        </span>
        {expanded ? <ChevronDown size={16} className="text-stone-400" /> : <ChevronUp size={16} className="text-stone-400" />}
      </button>

      {expanded && (
        <div className={`border-t border-stone-100 ${expanded ? 'animate-slide-up' : ''}`} style={{ maxHeight: '300px', overflow: 'hidden' }}>
          <div className="border-b border-stone-100 px-3 py-2">
            <LogFilters filters={filters} onChange={(f) => setFilters(f)} />
          </div>
          <div className="overflow-y-auto" style={{ maxHeight: '240px' }}>
            {logsData?.items.map((log) => (
              <LogListItem key={log.id} log={log} />
            ))}
            {logsData?.items.length === 0 && (
              <p className="text-xs text-stone-400 text-center py-4">暂无日志</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
