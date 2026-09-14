import type { ExecutionLog } from '../types/log';
import { LOG_EVENT_TYPE_ICONS, LOG_EVENT_TYPE_LABELS, LOG_EVENT_STATUS_LABELS } from '../types/log';
import { Badge } from './ui/badge';
import { AgentStatusBadge } from './ui/agent-status-badge';
import { cn } from '@/lib/utils';

interface LogListItemProps {
  log: ExecutionLog;
  onClick?: () => void;
  isSelected?: boolean;
  isNew?: boolean;
}

export default function LogListItem({ log, onClick, isSelected = false, isNew = false }: LogListItemProps) {
  const isError = log.event_status === 'error' || log.event_status === 'failed';

  return (
    <button
      type="button"
      onClick={onClick}
      data-log-id={log.id}
      data-log-status={log.event_status}
      className={cn(
        'flex w-full items-start gap-3 border-b border-stone-100 px-3 py-2.5 text-left transition-colors',
        'hover:bg-stone-50 focus:bg-stone-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-stone-300',
        isSelected && 'bg-stone-100',
        isNew && 'animate-[newLogHighlight_2s_ease-out]',
        isError ? 'border-l-4 border-l-red-400' : 'border-l-4 border-l-transparent',
      )}
    >
      <span
        className="text-base shrink-0"
        title={LOG_EVENT_TYPE_LABELS[log.event_type]}
        aria-hidden
      >
        {LOG_EVENT_TYPE_ICONS[log.event_type] || '•'}
      </span>

      <div className="min-w-0 flex-1">
        <div className="mb-1 flex items-center gap-2">
          <AgentStatusBadge
            state={log.event_status}
            label={LOG_EVENT_STATUS_LABELS[log.event_status] || log.event_status}
            dot={false}
            className="px-1.5 py-0 text-[10px]"
          />
          <Badge variant="outline" className="px-1.5 py-0 text-[10px] font-normal">
            {log.agent_name || log.agent_id || 'System'}
          </Badge>
          {log.model_id && (
            <span className="truncate font-mono text-[10px] text-stone-500">
              {log.model_id}
            </span>
          )}
        </div>
        <p className="line-clamp-2 text-xs leading-snug text-stone-700">
          {log.input_summary || log.output_summary || log.error_message || '—'}
        </p>
      </div>

      <span className="shrink-0 text-[10px] tabular-nums text-stone-400">
        {log.created_at ? new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''}
      </span>
    </button>
  );
}
