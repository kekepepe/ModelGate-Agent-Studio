import type { HandoffResult, HandoffStatus } from '../types/handoff';
import {
  HANDOFF_RESULT_CLASSES,
  HANDOFF_RESULT_LABELS,
  HANDOFF_STATUS_CLASSES,
  HANDOFF_STATUS_DOTS,
  HANDOFF_STATUS_LABELS,
} from '../types/handoff';

interface HandoffStatusTagProps {
  status?: HandoffStatus | HandoffResult | null;
  type?: 'status' | 'result';
  compact?: boolean;
}

export default function HandoffStatusTag({ status, type = 'status', compact = false }: HandoffStatusTagProps) {
  if (!status) return <span className="text-xs text-stone-300">—</span>;

  const classes = type === 'result'
    ? HANDOFF_RESULT_CLASSES[status]
    : HANDOFF_STATUS_CLASSES[status];
  const label = type === 'result'
    ? HANDOFF_RESULT_LABELS[status]
    : HANDOFF_STATUS_LABELS[status];
  const dot = type === 'status' ? HANDOFF_STATUS_DOTS[status] : '';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${compact ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-0.5 text-xs'} ${classes || 'bg-stone-100 text-stone-600 border-stone-200'}`}>
      {type === 'status' && <span className={`w-1.5 h-1.5 rounded-full ${dot || 'bg-stone-400'}`} />}
      {label || status}
    </span>
  );
}
