import type { QuotaStatus } from '../types/quota';
import { STATUS_COLORS, STATUS_LABELS } from '../types/quota';

interface RiskBadgeProps {
  status: QuotaStatus;
  usagePercent?: number | null;
  estimatedRemaining?: number | null;
  size?: 'sm' | 'md';
}

export default function RiskBadge({
  status,
  usagePercent,
  estimatedRemaining,
  size = 'sm',
}: RiskBadgeProps) {
  const colorClass = STATUS_COLORS[status] || 'bg-stone-400';
  const label = STATUS_LABELS[status] || status;

  const sizeClass = size === 'sm'
    ? 'w-2 h-2'
    : 'w-3 h-3';

  return (
    <div className="group relative inline-flex items-center gap-1.5">
      <span className={`inline-block rounded-full ${sizeClass} ${colorClass}`} />
      <span className="text-xs text-stone-600">{label}</span>
      {(usagePercent !== undefined || estimatedRemaining !== undefined) && (
        <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-50">
          <div className="bg-stone-800 text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap shadow-lg">
            {usagePercent !== null && usagePercent !== undefined && (
              <div>使用率: {(usagePercent * 100).toFixed(1)}%</div>
            )}
            {estimatedRemaining !== null && estimatedRemaining !== undefined && (
              <div>剩余: {estimatedRemaining.toLocaleString()} tokens</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
