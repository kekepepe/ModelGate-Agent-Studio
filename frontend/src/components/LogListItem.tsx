import type { ExecutionLog } from '../types/log';
import { LOG_EVENT_STATUS_COLORS, LOG_EVENT_TYPE_ICONS, LOG_EVENT_TYPE_LABELS, LOG_EVENT_STATUS_LABELS } from '../types/log';

interface LogListItemProps {
  log: ExecutionLog;
  onClick?: () => void;
  isSelected?: boolean;
  isNew?: boolean;
}

export default function LogListItem({ log, onClick, isSelected = false, isNew = false }: LogListItemProps) {
  const isError = log.event_status === 'error' || log.event_status === 'failed';
  const statusClass = LOG_EVENT_STATUS_COLORS[log.event_status] || 'bg-stone-100 text-stone-600 border-stone-200';

  return (
    <div
      onClick={onClick}
      className={`cursor-pointer border-b border-stone-100 px-4 py-3 transition-colors hover:bg-stone-50 ${
        isSelected ? 'bg-stone-100' : ''
      } ${isNew ? 'animate-[newLogHighlight_2s_ease-out]' : ''} ${isError ? 'border-l-4 border-l-red-400' : 'border-l-4 border-l-transparent'}`}
    >
      <div className="flex items-center gap-3">
        <span className="text-lg" title={LOG_EVENT_TYPE_LABELS[log.event_type]}>{LOG_EVENT_TYPE_ICONS[log.event_type] || '•'}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium rounded border ${statusClass}`}>
              {LOG_EVENT_STATUS_LABELS[log.event_status] || log.event_status}
            </span>
            <span className="text-xs text-stone-400 truncate">
              {log.agent_name || log.agent_id || 'System'}
            </span>
            {log.model_id && (
              <span className="text-xs text-stone-400 truncate font-mono">{log.model_id}</span>
            )}
          </div>
          <p className="text-sm text-stone-700 truncate leading-snug">
            {log.input_summary || log.output_summary || log.error_message || '—'}
          </p>
        </div>
        <span className="text-xs text-stone-400 whitespace-nowrap">
          {log.created_at ? formatRelativeTime(log.created_at) : ''}
        </span>
      </div>
    </div>
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
