import type { WorkerStatus } from '../types/workspace';
import { Badge } from './ui/badge';
import { AgentStatusBadge } from './ui/agent-status-badge';
import { cn } from '@/lib/utils';

interface WorkerBadgeProps {
  modelName?: string | null;
  status?: string | null;
  totalTokensUsed?: number;
  compact?: boolean;
}

const STATUS_LABELS: Record<string, string> = {
  idle: '空闲',
  running: '运行中',
  handoff_required: '需交接',
  completed: '已完成',
  failed: '失败',
};

export default function WorkerBadge({
  modelName,
  status = 'idle',
  compact = false,
}: WorkerBadgeProps) {
  const isRunning = status === 'running';
  const isHandoff = status === 'handoff_required';
  const pulseClass = isRunning || isHandoff ? 'animate-pulse' : '';

  return (
    <Badge
      variant="secondary"
      className={cn(
        'gap-1.5 font-medium',
        compact ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs',
        pulseClass,
      )}
      data-worker-status={status}
    >
      <span
        aria-hidden
        className={cn(
          'inline-block h-2 w-2 rounded-full',
          status === 'running' && 'bg-blue-500',
          status === 'handoff_required' && 'bg-violet-500',
          status === 'completed' && 'bg-emerald-500',
          status === 'failed' && 'bg-red-500 animate-ping',
          status === 'idle' && 'bg-stone-400',
        )}
      />
      <span className="text-xs text-stone-700 font-medium">
        {modelName || '—'}
      </span>
      {!compact && (
        <>
          <span aria-hidden className="text-stone-400">·</span>
          <AgentStatusBadge
            state={(status as WorkerStatus) ?? 'idle'}
            label={STATUS_LABELS[status || 'idle'] ?? status ?? undefined}
            dot={false}
            className="border-0 bg-transparent px-0 py-0 text-[10px] text-stone-500"
          />
        </>
      )}
    </Badge>
  );
}
