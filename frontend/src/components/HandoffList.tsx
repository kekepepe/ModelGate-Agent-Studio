import { ChevronRight, ArrowLeftRight } from 'lucide-react';
import type { HandoffListItem } from '../types/handoff';
import { HANDOFF_REASON_LABELS } from '../types/handoff';
import HandoffStatusTag from './HandoffStatusTag';

interface HandoffListProps {
  handoffs: HandoffListItem[];
  onSelect: (handoff: HandoffListItem) => void;
  onClearFilters?: () => void;
  hasFilters?: boolean;
}

export default function HandoffList({ handoffs, onSelect, onClearFilters, hasFilters = false }: HandoffListProps) {
  if (handoffs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center px-4">
        <ArrowLeftRight size={48} className="text-stone-300 mb-4" />
        <div className="text-base font-medium text-stone-600 mb-1">
          {hasFilters ? 'No results match your filters' : 'No handoff records yet'}
        </div>
        <p className="text-sm text-stone-400 max-w-md leading-relaxed">
          {hasFilters
            ? '调整或清空筛选条件后重试。'
            : 'Handoffs happen when a task is transferred from one agent or model to another.'}
        </p>
        {hasFilters && onClearFilters && (
          <button onClick={onClearFilters} className="mt-4 px-3 py-2 text-sm text-stone-600 hover:text-stone-800">
            Clear Filters
          </button>
        )}
      </div>
    );
  }

  return (
    <>
      <div className="hidden md:block divide-y divide-stone-100">
        <div className="grid grid-cols-[minmax(280px,1fr)_200px_120px_120px_100px_120px_48px] px-4 py-2 text-xs font-medium text-stone-400 bg-stone-50">
          <span>Goal / Task</span>
          <span className="text-center">From → To</span>
          <span className="text-center">Reason</span>
          <span className="text-center">Status</span>
          <span className="text-center">Result</span>
          <span className="text-right">Created</span>
          <span />
        </div>
        {handoffs.map((handoff) => (
          <button
            key={handoff.id}
            onClick={() => onSelect(handoff)}
            className={`w-full grid grid-cols-[minmax(280px,1fr)_200px_120px_120px_100px_120px_48px] items-center px-4 py-3 text-left hover:bg-stone-50 transition-colors ${handoff.status === 'failed' ? 'border-l-4 border-red-600' : ''}`}
          >
            <div className="min-w-0">
              <div className="text-sm font-medium text-stone-800 truncate">{handoff.goal_id}</div>
              <div className="text-xs text-stone-400 truncate">{handoff.task_title || handoff.task_id}</div>
            </div>
            <div className="flex items-center justify-center gap-2 text-xs text-stone-600 min-w-0">
              <span className="truncate">{handoff.from_agent_name || handoff.from_agent_id.slice(0, 8)}</span>
              <span className="text-stone-300">→</span>
              <span className="truncate">{handoff.to_agent_name || handoff.to_agent_id.slice(0, 8)}</span>
            </div>
            <div className="flex justify-center">
              <span className="px-2 py-0.5 rounded-full text-[11px] bg-stone-100 text-stone-600 border border-stone-200">
                {HANDOFF_REASON_LABELS[handoff.reason] || handoff.reason}
              </span>
            </div>
            <div className="flex justify-center"><HandoffStatusTag status={handoff.status} compact /></div>
            <div className="flex justify-center"><HandoffStatusTag status={handoff.result_after_handoff} type="result" compact /></div>
            <div className="text-xs text-stone-400 text-right font-mono">{handoff.created_at ? formatRelativeTime(handoff.created_at) : '—'}</div>
            <div className="flex justify-end text-stone-300"><ChevronRight size={16} /></div>
          </button>
        ))}
      </div>

      <div className="md:hidden divide-y divide-stone-100">
        {handoffs.map((handoff) => (
          <button key={handoff.id} onClick={() => onSelect(handoff)} className="w-full p-4 text-left hover:bg-stone-50">
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="min-w-0">
                <div className="text-sm font-medium text-stone-800 truncate">{handoff.goal_id}</div>
                <div className="text-xs text-stone-400 truncate">{handoff.task_title || handoff.task_id}</div>
              </div>
              <HandoffStatusTag status={handoff.status} compact />
            </div>
            <div className="text-xs text-stone-500">
              {handoff.from_agent_name || handoff.from_agent_id.slice(0, 8)} → {handoff.to_agent_name || handoff.to_agent_id.slice(0, 8)}
            </div>
          </button>
        ))}
      </div>
    </>
  );
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const diffMs = new Date().getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  if (diffMin < 1) return '刚刚';
  if (diffMin < 60) return `${diffMin} 分钟前`;
  if (diffHour < 24) return `${diffHour} 小时前`;
  if (diffDay < 7) return `${diffDay} 天前`;
  return date.toLocaleDateString('zh-CN');
}
