import type { WorkerStatus } from '../types/workspace';
import { WORKER_STATUS_COLORS } from '../types/workspace';

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

export default function WorkerBadge({ modelName, status = 'idle', compact = false }: WorkerBadgeProps) {
  const dotColor = WORKER_STATUS_COLORS[status as WorkerStatus] || WORKER_STATUS_COLORS.idle;
  const isRunning = status === 'running';
  const isHandoff = status === 'handoff_required';

  return (
    <div className={`inline-flex items-center gap-1.5 rounded-full border border-stone-200 bg-white ${compact ? 'px-2 py-0.5' : 'px-2.5 py-1'}`}>
      <span
        className={`inline-block w-2 h-2 rounded-full ${dotColor} ${isRunning ? 'animate-breathe-dot' : ''} ${isHandoff ? 'animate-dot-pulse' : ''} ${status === 'failed' ? 'animate-blink' : ''}`}
        style={status === 'failed' ? { animation: 'dot-pulse 0.5s infinite' } : undefined}
      />
      <span className="text-xs text-stone-700 font-medium">{modelName || '—'}</span>
      {!compact && (
        <>
          <span className="text-xs text-stone-400">·</span>
          <span className="text-xs text-stone-400">{STATUS_LABELS[status || 'idle'] || status}</span>
        </>
      )}
    </div>
  );
}
