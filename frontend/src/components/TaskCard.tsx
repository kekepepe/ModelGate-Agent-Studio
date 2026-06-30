import type { TaskStatus } from '../types/workspace';
import { TASK_STATUS_ICONS, TASK_STATUS_LABELS, TASK_STATUS_BORDERS, TASK_STATUS_BG } from '../types/workspace';

interface TaskCardProps {
  id: string;
  title: string;
  status: TaskStatus;
  priority?: number;
  tokensUsed?: number;
  onSelect?: (taskId: string) => void;
  isSelected?: boolean;
  handoffIndicator?: React.ReactNode;
}

export default function TaskCard({
  id,
  title,
  status,
  priority = 0,
  tokensUsed = 0,
  onSelect,
  isSelected = false,
  handoffIndicator,
}: TaskCardProps) {
  const icon = TASK_STATUS_ICONS[status] || '•';
  const border = TASK_STATUS_BORDERS[status] || 'border-stone-200';
  const bg = TASK_STATUS_BG[status] || 'bg-white';

  const animationClass =
    status === 'running' ? 'animate-breathe' :
    status === 'failed' ? 'animate-shake' :
    status === 'handoff' ? 'animate-rotate-border' : '';

  return (
    <div
      onClick={() => onSelect?.(id)}
      className={`cursor-pointer rounded-lg border ${border} ${bg} p-3 transition-all duration-300 ${animationClass} ${isSelected ? 'ring-2 ring-blue-400' : 'hover:shadow-sm'}`}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter') onSelect?.(id); }}
    >
      <div className="flex items-start gap-2">
        <span className="text-lg leading-none mt-0.5 flex-shrink-0">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <p className="text-sm font-medium text-stone-800 truncate">{title}</p>
            {priority > 0 && (
              <span className="text-[10px] text-amber-600 border border-amber-200 bg-amber-50 px-1 rounded">
                P{priority}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 text-xs text-stone-400">
            <span>{TASK_STATUS_LABELS[status]}</span>
            {tokensUsed > 0 && <span>{tokensUsed.toLocaleString()} tokens</span>}
          </div>
        </div>
      </div>
      {handoffIndicator}
    </div>
  );
}
